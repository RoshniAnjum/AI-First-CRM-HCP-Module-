"""
LangGraph agent with 8 tools:
  - LogInteractionTool       : extract structured data + resolve relative dates
  - MergeInteractionTool     : merge new input into existing form without overwriting
  - SummarizeInteractionTool : generate concise summary of the full interaction
  - EditInteractionTool      : update specific fields only
  - ClearFormTool            : reset all fields
  - SuggestFollowUpTool      : recommend next action
  - ValidateInteractionTool  : check for missing required fields
"""
import os
import json
import re
from typing import TypedDict, Optional, Dict, Any
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

load_dotenv()

# ── LLM ──────────────────────────────────────────────────────────────────────

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
)

TODAY     = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
NOW       = datetime.now().strftime("%H:%M")

# ── State ─────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    user_message: str
    current_form: Dict[str, Any]
    tool_called: str
    form_data: Dict[str, Any]
    assistant_message: str
    follow_up: Optional[str]
    validation: Optional[Dict[str, Any]]


# ── Empty form template ───────────────────────────────────────────────────────

EMPTY_FORM: Dict[str, Any] = {
    "hcp_name": None,
    "interaction_type": None,
    "date": None,
    "time": None,
    "attendees": None,
    "discussion_topic": None,
    "sentiment": None,
    "materials_shared": None,
    "brochure_shared": False,
    "summary": None,
}


# ── Prompts ───────────────────────────────────────────────────────────────────

ROUTER_SYSTEM = f"""You are a routing assistant for an HCP (Healthcare Professional) CRM system.
Decide which tool to call based on the user message.

Available tools:
- LogInteractionTool       : User is describing a brand new interaction with an HCP from scratch
- MergeInteractionTool     : User is adding more details or updating an existing interaction without replacing it
- SummarizeInteractionTool : User asks for a summary, overview, or recap of the interaction
- EditInteractionTool      : User wants to change or correct a specific field value
- ClearFormTool            : User wants to clear, reset, or start over
- SuggestFollowUpTool      : User asks for a follow-up recommendation or next steps
- ValidateInteractionTool  : User asks to validate, check, or review the form

Respond with ONLY a JSON object, no extra text:
{{"tool": "<tool_name>"}}"""


LOG_SYSTEM = f"""You are an AI assistant that extracts structured HCP interaction data from natural language.

Today is {TODAY}. Yesterday was {YESTERDAY}. Current time is {NOW}.

Extract these fields:
- hcp_name        : Full name of the Healthcare Professional (string or null)
- interaction_type: One of "Meeting", "Call", "Email", "Conference", "Visit" (string or null)
- date            : Date in YYYY-MM-DD format. Resolve relative dates:
                    "today" → {TODAY}, "yesterday" → {YESTERDAY},
                    "last Monday" → calculate from today, etc. (string or null)
- time            : Time in HH:MM 24-hour format. "now" → {NOW} (string or null)
- attendees       : Other attendees besides the HCP, comma-separated (string or null)
- discussion_topic: Main topics discussed (string or null)
- sentiment       : One of "positive", "neutral", "negative". Infer from tone words. (string or null)
- materials_shared: Materials, brochures, or samples shared (string or null)
- brochure_shared : true if any material was shared, false otherwise (boolean)

Rules:
- Return ONLY valid JSON. No explanation, no markdown, no extra text.
- Use null for fields not mentioned.
- If materials_shared is not null, set brochure_shared to true.

Example:
{{"hcp_name": "Dr. Sarah Johnson", "interaction_type": "Meeting", "date": "{TODAY}", "time": "14:30", "attendees": "John Smith", "discussion_topic": "Prodo-X efficacy and trial results", "sentiment": "positive", "materials_shared": "Product brochure", "brochure_shared": true}}"""


MERGE_SYSTEM = f"""You are an AI assistant that intelligently merges new interaction details into an existing HCP interaction form.

Today is {TODAY}. Yesterday was {YESTERDAY}. Current time is {NOW}.

You will receive:
1. The existing form data (may have some fields already filled)
2. New information from the user

Rules:
- NEVER overwrite a field that already has a value unless the user explicitly says to change it.
- If a field is null or empty in the existing form, fill it from the new input.
- If both existing and new have a value for discussion_topic or attendees, APPEND the new value to the existing one (comma-separated or with a semicolon).
- Resolve relative dates: "today" → {TODAY}, "yesterday" → {YESTERDAY}.
- Return the COMPLETE merged form as JSON. No explanation, no markdown, no extra text.
- sentiment must be one of: "positive", "neutral", "negative"
- interaction_type must be one of: "Meeting", "Call", "Email", "Conference", "Visit"
- If materials_shared is set, also set brochure_shared to true."""


SUMMARIZE_SYSTEM = """You are an AI assistant that generates concise professional summaries of HCP interactions for pharmaceutical sales representatives.

You will receive the full interaction form data.

Generate a summary that captures:
- Who was met and when
- What was discussed (key topics and insights)
- The overall sentiment and HCP receptiveness
- What materials were shared
- Any notable outcomes or next steps implied

Rules:
- Return ONLY valid JSON. No explanation, no markdown, no extra text.
- Format: {"summary": "<2-4 sentence professional summary>", "message": "<one line confirmation>"}
- Be concise, factual, and professional. No emojis."""


EDIT_SYSTEM = f"""You are an AI assistant that updates specific fields of an HCP interaction form.

Today is {TODAY}.

You will receive the current form and a user instruction to change specific fields.

Rules:
- Return the COMPLETE updated form as JSON, preserving all unchanged fields exactly.
- Return ONLY valid JSON. No explanation, no markdown, no extra text.
- date format: YYYY-MM-DD. Resolve relative dates.
- time format: HH:MM
- sentiment must be one of: "positive", "neutral", "negative"
- interaction_type must be one of: "Meeting", "Call", "Email", "Conference", "Visit"
- If materials_shared is set to a non-null value, also set brochure_shared to true."""


SUGGEST_SYSTEM = """You are an AI assistant that suggests follow-up actions for pharmaceutical sales representatives after HCP interactions.

Based on the interaction data, suggest a specific, actionable next step.

Rules:
- Return ONLY valid JSON. No explanation, no markdown, no extra text.
- Format: {"follow_up": "<specific suggestion>", "message": "<brief explanation>"}"""


VALIDATE_SYSTEM = """You are an AI assistant that validates HCP interaction form completeness.

Required fields: hcp_name, date, interaction_type, discussion_topic

Rules:
- Return ONLY valid JSON. No explanation, no markdown, no extra text.
- Format: {"is_valid": true/false, "missing_fields": ["field1", ...], "message": "<summary>"}
- A field is missing if it is null, empty string, or not provided."""


# ── Helper ────────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> Dict[str, Any]:
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"No valid JSON in LLM response: {text[:400]}")


def _normalize_bool(form_data: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(form_data.get("brochure_shared"), str):
        form_data["brochure_shared"] = form_data["brochure_shared"].lower() in ("true", "yes", "1")
    if form_data.get("materials_shared"):
        form_data["brochure_shared"] = True
    return form_data


# ── Node: Router ──────────────────────────────────────────────────────────────

def route_node(state: AgentState) -> AgentState:
    response = llm.invoke([
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=state["user_message"]),
    ])
    try:
        parsed = _extract_json(response.content)
        tool = parsed.get("tool", "LogInteractionTool")
    except ValueError:
        tool = "LogInteractionTool"

    valid_tools = {
        "LogInteractionTool", "MergeInteractionTool", "SummarizeInteractionTool",
        "EditInteractionTool", "ClearFormTool",
        "SuggestFollowUpTool", "ValidateInteractionTool",
    }
    if tool not in valid_tools:
        tool = "LogInteractionTool"
    return {**state, "tool_called": tool}


# ── Node: LogInteractionTool ──────────────────────────────────────────────────

def log_interaction_node(state: AgentState) -> AgentState:
    """
    Extract structured data from natural language.
    Resolves relative dates (today, yesterday, last Monday, etc.).
    """
    response = llm.invoke([
        SystemMessage(content=LOG_SYSTEM),
        HumanMessage(content=state["user_message"]),
    ])
    try:
        form_data = _extract_json(response.content)
        form_data = {**EMPTY_FORM, **form_data}
        form_data = _normalize_bool(form_data)
        message = "The interaction has been logged. The form has been updated with the details you provided."
    except ValueError:
        form_data = state["current_form"]
        message = "Unable to parse the interaction details. Please rephrase and try again."
    return {**state, "form_data": form_data, "assistant_message": message}


# ── Node: MergeInteractionTool ────────────────────────────────────────────────

def merge_interaction_node(state: AgentState) -> AgentState:
    """
    Merge new user input into the existing form.
    Preserves existing field values — only fills nulls or appends to lists.
    """
    existing = json.dumps(state["current_form"], indent=2)
    prompt = (
        f"Existing form data:\n{existing}\n\n"
        f"New information from user: {state['user_message']}"
    )
    response = llm.invoke([
        SystemMessage(content=MERGE_SYSTEM),
        HumanMessage(content=prompt),
    ])
    try:
        merged = _extract_json(response.content)
        # Ensure all keys exist
        form_data = {**EMPTY_FORM, **state["current_form"], **merged}
        form_data = _normalize_bool(form_data)
        message = "The new details have been merged into the existing interaction record."
    except ValueError:
        form_data = state["current_form"]
        message = "Unable to merge the new details. Please try again."
    return {**state, "form_data": form_data, "assistant_message": message}


# ── Node: SummarizeInteractionTool ────────────────────────────────────────────

def summarize_interaction_node(state: AgentState) -> AgentState:
    """
    Generate a concise professional summary of the full interaction.
    Captures key insights, sentiment, and outcomes.
    """
    form_json = json.dumps(state["current_form"], indent=2)
    response = llm.invoke([
        SystemMessage(content=SUMMARIZE_SYSTEM),
        HumanMessage(content=f"Interaction data:\n{form_json}"),
    ])
    try:
        parsed = _extract_json(response.content)
        summary = parsed.get("summary", "")
        message = parsed.get("message", "Summary generated.")
        # Store summary back into form_data
        form_data = {**state["current_form"], "summary": summary}
    except ValueError:
        summary = ""
        form_data = state["current_form"]
        message = "Unable to generate a summary. Please ensure the form has sufficient data."
    return {**state, "form_data": form_data, "assistant_message": message}


# ── Node: EditInteractionTool ─────────────────────────────────────────────────

def edit_interaction_node(state: AgentState) -> AgentState:
    current = json.dumps(state["current_form"], indent=2)
    prompt = f"Current form:\n{current}\n\nUser instruction: {state['user_message']}"
    response = llm.invoke([
        SystemMessage(content=EDIT_SYSTEM),
        HumanMessage(content=prompt),
    ])
    try:
        updated = _extract_json(response.content)
        form_data = {**state["current_form"], **updated}
        form_data = _normalize_bool(form_data)
        message = "The specified fields have been updated."
    except ValueError:
        form_data = state["current_form"]
        message = "Unable to process the update. Please provide clearer instructions."
    return {**state, "form_data": form_data, "assistant_message": message}


# ── Node: ClearFormTool ───────────────────────────────────────────────────────

def clear_form_node(state: AgentState) -> AgentState:
    return {
        **state,
        "form_data": dict(EMPTY_FORM),
        "assistant_message": "The form has been cleared. You may begin logging a new interaction.",
    }


# ── Node: SuggestFollowUpTool ─────────────────────────────────────────────────

def suggest_follow_up_node(state: AgentState) -> AgentState:
    form_json = json.dumps(state["current_form"], indent=2)
    response = llm.invoke([
        SystemMessage(content=SUGGEST_SYSTEM),
        HumanMessage(content=f"HCP Interaction data:\n{form_json}"),
    ])
    try:
        parsed = _extract_json(response.content)
        follow_up = parsed.get("follow_up", "")
        message = parsed.get("message", "Follow-up suggestion generated.")
    except ValueError:
        follow_up = response.content.strip()
        message = "Follow-up suggestion generated."
    return {**state, "form_data": state["current_form"], "follow_up": follow_up, "assistant_message": message}


# ── Node: ValidateInteractionTool ─────────────────────────────────────────────

def validate_interaction_node(state: AgentState) -> AgentState:
    """
    Validate required fields directly in Python — no LLM needed for null checks.
    LLM is only used to generate a human-readable summary message.
    """
    form = state["current_form"]

    required = {
        "hcp_name":         "HCP Name",
        "date":             "Date",
        "interaction_type": "Interaction Type",
        "discussion_topic": "Discussion Topic",
    }

    missing_keys = []
    missing_labels = []

    for key, label in required.items():
        val = form.get(key)
        if not val or (isinstance(val, str) and val.strip() == ""):
            missing_keys.append(key)
            missing_labels.append(label)

    is_valid = len(missing_keys) == 0

    if is_valid:
        message = "The form is complete. All required fields are filled."
        validation = {"is_valid": True, "missing_fields": [], "message": "All required fields are present."}
    else:
        fields_str = ", ".join(missing_labels)
        message = f"The following required fields are missing: {fields_str}. Please provide the missing information."
        validation = {
            "is_valid": False,
            "missing_fields": missing_keys,
            "message": f"Missing: {fields_str}.",
        }

    return {**state, "form_data": state["current_form"], "validation": validation, "assistant_message": message}


# ── Graph ─────────────────────────────────────────────────────────────────────

def decide_tool(state: AgentState) -> str:
    return state["tool_called"]


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router",                  route_node)
    graph.add_node("LogInteractionTool",       log_interaction_node)
    graph.add_node("MergeInteractionTool",     merge_interaction_node)
    graph.add_node("SummarizeInteractionTool", summarize_interaction_node)
    graph.add_node("EditInteractionTool",      edit_interaction_node)
    graph.add_node("ClearFormTool",            clear_form_node)
    graph.add_node("SuggestFollowUpTool",      suggest_follow_up_node)
    graph.add_node("ValidateInteractionTool",  validate_interaction_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router", decide_tool,
        {
            "LogInteractionTool":       "LogInteractionTool",
            "MergeInteractionTool":     "MergeInteractionTool",
            "SummarizeInteractionTool": "SummarizeInteractionTool",
            "EditInteractionTool":      "EditInteractionTool",
            "ClearFormTool":            "ClearFormTool",
            "SuggestFollowUpTool":      "SuggestFollowUpTool",
            "ValidateInteractionTool":  "ValidateInteractionTool",
        },
    )

    for node in [
        "LogInteractionTool", "MergeInteractionTool", "SummarizeInteractionTool",
        "EditInteractionTool", "ClearFormTool",
        "SuggestFollowUpTool", "ValidateInteractionTool",
    ]:
        graph.add_edge(node, END)

    return graph.compile()


crm_graph = build_graph()


# ── Public API ────────────────────────────────────────────────────────────────

def run_agent(user_message: str, current_form: Dict[str, Any]) -> Dict[str, Any]:
    initial_state: AgentState = {
        "user_message": user_message,
        "current_form": current_form,
        "tool_called": "",
        "form_data": current_form,
        "assistant_message": "",
        "follow_up": None,
        "validation": None,
    }
    result = crm_graph.invoke(initial_state)
    return {
        "tool_called":       result["tool_called"],
        "form_data":         result["form_data"],
        "assistant_message": result["assistant_message"],
        "follow_up":         result.get("follow_up"),
        "validation":        result.get("validation"),
    }
