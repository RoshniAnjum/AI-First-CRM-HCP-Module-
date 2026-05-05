from pydantic import BaseModel
from typing import Optional, Any, Dict


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class FormState(BaseModel):
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[str] = None
    discussion_topic: Optional[str] = None
    sentiment: Optional[str] = None
    materials_shared: Optional[str] = None
    brochure_shared: Optional[bool] = False
    summary: Optional[str] = None          # Added for SummarizeInteractionTool


class ChatResponse(BaseModel):
    message: str
    tool_called: str
    form_data: FormState
    follow_up: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None
