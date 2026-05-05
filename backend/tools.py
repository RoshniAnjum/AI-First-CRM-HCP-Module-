"""
LangGraph tool definitions for the HCP Interaction CRM agent.

All 5 required tools:
  1. LogInteractionTool
  2. EditInteractionTool
  3. ClearFormTool
  4. SuggestFollowUpTool
  5. ValidateInteractionTool
"""
import json
import re
from typing import Optional, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Input schemas
# ─────────────────────────────────────────────

class LogInteractionInput(BaseModel):
    user_message: str = Field(description="Raw natural language message from the user describing the HCP interaction.")


class EditInteractionInput(BaseModel):
    user_message: str = Field(description="Natural language instruction specifying which fields to update and their new values.")
    current_form: Dict[str, Any] = Field(description="Current form state as a dict so unchanged fields are preserved.")


class ClearFormInput(BaseModel):
    confirm: bool = Field(default=True, description="Confirmation flag to clear the form.")


class SuggestFollowUpInput(BaseModel):
    form_data: Dict[str, Any] = Field(description="Current form state to base the follow-up suggestion on.")


class ValidateInteractionInput(BaseModel):
    form_data: Dict[str, Any] = Field(description="Current form state to validate for completeness.")


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _extract_json(text: str) -> Dict[str, Any]:
    """
    Robustly extract the first JSON object from an LLM response string.
    Raises ValueError if no valid JSON is found.
    """
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in LLM response: {text[:300]}")


# ─────────────────────────────────────────────
# Tool 1 — LogInteractionTool
# ─────────────────────────────────────────────

@tool("LogInteractionTool", args_schema=LogInteractionInput)
def log_interaction_tool(user_message: str) -> Dict[str, Any]:
    """
    Extract structured HCP interaction data from a natural language message.
    Returns a dict with keys: hcp_name, date, sentiment, discussion_topic, brochure_shared.
    Use this when the user is describing a new interaction with an HCP.
    """
    # This function body is intentionally minimal — the LLM decides what to extract.
    # The agent will call the LLM with a structured prompt and parse the result.
    # The actual extraction happens in agent.py via the LLM call.
    return {
        "tool": "LogInteractionTool",
        "user_message": user_message,
    }


# ─────────────────────────────────────────────
# Tool 2 — EditInteractionTool
# ─────────────────────────────────────────────

@tool("EditInteractionTool", args_schema=EditInteractionInput)
def edit_interaction_tool(user_message: str, current_form: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update ONLY the fields mentioned in the user message, preserving all other fields.
    Use this when the user wants to change specific fields of an existing interaction.
    """
    return {
        "tool": "EditInteractionTool",
        "user_message": user_message,
        "current_form": current_form,
    }


# ─────────────────────────────────────────────
# Tool 3 — ClearFormTool
# ─────────────────────────────────────────────

@tool("ClearFormTool", args_schema=ClearFormInput)
def clear_form_tool(confirm: bool = True) -> Dict[str, Any]:
    """
    Reset all form fields to their empty/default state.
    Use this when the user asks to clear, reset, or start over.
    """
    return {
        "tool": "ClearFormTool",
        "form_data": {
            "hcp_name": None,
            "date": None,
            "sentiment": None,
            "discussion_topic": None,
            "brochure_shared": False,
        },
    }


# ─────────────────────────────────────────────
# Tool 4 — SuggestFollowUpTool
# ─────────────────────────────────────────────

@tool("SuggestFollowUpTool", args_schema=SuggestFollowUpInput)
def suggest_follow_up_tool(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest the next best action based on the current interaction data.
    Use this when the user asks for a follow-up recommendation or next steps.
    """
    return {
        "tool": "SuggestFollowUpTool",
        "form_data": form_data,
    }


# ─────────────────────────────────────────────
# Tool 5 — ValidateInteractionTool
# ─────────────────────────────────────────────

@tool("ValidateInteractionTool", args_schema=ValidateInteractionInput)
def validate_interaction_tool(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check the current form for missing or incomplete required fields.
    Use this when the user asks to validate, check, or review the form.
    """
    return {
        "tool": "ValidateInteractionTool",
        "form_data": form_data,
    }


# Export all tools as a list for the agent
ALL_TOOLS = [
    log_interaction_tool,
    edit_interaction_tool,
    clear_form_tool,
    suggest_follow_up_tool,
    validate_interaction_tool,
]
