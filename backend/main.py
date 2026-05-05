"""
FastAPI backend for the AI-First CRM HCP Log Interaction system.
"""
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db, Interaction, ChatMessage
from schemas import ChatRequest, ChatResponse, FormState
from agent import run_agent

load_dotenv()

app = FastAPI(
    title="HCP CRM AI Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory form state per session
_session_forms: dict = {}
# Map session_id → DB interaction row id
_session_db_ids: dict = {}

EMPTY_FORM = {
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

def get_session_form(session_id: str, db: Session = None) -> dict:
    """Return in-memory form, or reload from DB if session was lost (e.g. server restart)."""
    if session_id in _session_forms:
        return _session_forms[session_id]

    # Try to recover from DB
    if db is not None:
        db_id = _session_db_ids.get(session_id)
        row = None
        if db_id:
            row = db.query(Interaction).filter(Interaction.id == db_id).first()
        if row is None:
            # Find the most recent interaction row as fallback
            row = db.query(Interaction).order_by(Interaction.id.desc()).first()

        if row:
            recovered = {
                "hcp_name":         row.hcp_name,
                "interaction_type": row.interaction_type,
                "date":             row.date,
                "time":             row.time,
                "attendees":        row.attendees,
                "discussion_topic": row.discussion_topic,
                "sentiment":        row.sentiment,
                "materials_shared": row.materials_shared,
                "brochure_shared":  row.brochure_shared or False,
                "summary":          getattr(row, "summary", None),
            }
            _session_forms[session_id] = recovered
            _session_db_ids[session_id] = row.id
            return recovered

    return dict(EMPTY_FORM)

def set_session_form(session_id: str, form: dict):
    _session_forms[session_id] = form


@app.get("/")
def health_check():
    return {"status": "ok", "service": "HCP CRM AI Backend"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id or "default"
    current_form = get_session_form(session_id, db)

    try:
        result = run_agent(
            user_message=request.message,
            current_form=current_form,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    updated_form = result["form_data"]
    set_session_form(session_id, updated_form)

    # Save interaction to DB — one row per session, upsert
    try:
        db_id = _session_db_ids.get(session_id)
        db_row = db.query(Interaction).filter(Interaction.id == db_id).first() if db_id else None

        if db_row is None:
            db_row = Interaction(
                hcp_name         = updated_form.get("hcp_name"),
                interaction_type = updated_form.get("interaction_type"),
                date             = updated_form.get("date"),
                time             = updated_form.get("time"),
                attendees        = updated_form.get("attendees"),
                discussion_topic = updated_form.get("discussion_topic"),
                sentiment        = updated_form.get("sentiment"),
                materials_shared = updated_form.get("materials_shared"),
                brochure_shared  = updated_form.get("brochure_shared", False),
                follow_up_suggestion = result.get("follow_up"),
                summary          = updated_form.get("summary"),
            )
            db.add(db_row)
            db.commit()
            db.refresh(db_row)
            _session_db_ids[session_id] = db_row.id
        else:
            db_row.hcp_name         = updated_form.get("hcp_name")
            db_row.interaction_type = updated_form.get("interaction_type")
            db_row.date             = updated_form.get("date")
            db_row.time             = updated_form.get("time")
            db_row.attendees        = updated_form.get("attendees")
            db_row.discussion_topic = updated_form.get("discussion_topic")
            db_row.sentiment        = updated_form.get("sentiment")
            db_row.materials_shared = updated_form.get("materials_shared")
            db_row.brochure_shared  = updated_form.get("brochure_shared", False)
            if result.get("follow_up"):
                db_row.follow_up_suggestion = result["follow_up"]
            if updated_form.get("summary"):
                db_row.summary = updated_form.get("summary")
            db.commit()
    except Exception:
        db.rollback()

    # Save chat messages
    try:
        db.add(ChatMessage(role="user",      content=request.message))
        db.add(ChatMessage(role="assistant", content=result["assistant_message"]))
        db.commit()
    except Exception:
        db.rollback()

    return ChatResponse(
        message=result["assistant_message"],
        tool_called=result["tool_called"],
        form_data=FormState(**updated_form),
        follow_up=result.get("follow_up"),
        validation=result.get("validation"),
    )


@app.get("/form/{session_id}")
def get_form(session_id: str, db: Session = Depends(get_db)):
    return get_session_form(session_id, db)


@app.get("/interactions")
def list_interactions(db: Session = Depends(get_db)):
    """View all saved interactions."""
    rows = db.query(Interaction).order_by(Interaction.id.desc()).all()
    return [
        {
            "id": r.id,
            "hcp_name": r.hcp_name,
            "interaction_type": r.interaction_type,
            "date": r.date,
            "time": r.time,
            "attendees": r.attendees,
            "discussion_topic": r.discussion_topic,
            "sentiment": r.sentiment,
            "materials_shared": r.materials_shared,
            "brochure_shared": r.brochure_shared,
            "follow_up_suggestion": r.follow_up_suggestion,
            "created_at": str(r.created_at),
        }
        for r in rows
    ]


@app.get("/messages")
def list_messages(db: Session = Depends(get_db)):
    """View all chat messages."""
    rows = db.query(ChatMessage).order_by(ChatMessage.id.desc()).limit(50).all()
    return [{"role": r.role, "content": r.content, "time": str(r.created_at)} for r in rows]
