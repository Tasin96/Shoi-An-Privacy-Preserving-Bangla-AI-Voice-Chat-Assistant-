from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.schemas.safety import EmergencyPayload

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str
    citations: Optional[List[str]] = Field(default_factory=list)
    confidence: float = 1.0
    risk_level: str = "none"
    emergency_payload: Optional[EmergencyPayload] = None

class VoiceResponse(BaseModel):
    transcript: str
    reply_text: str
    audio_base64: Optional[str] = None
    citations: List[str] = Field(default_factory=list)
    risk_level: str = "none"
    emergency_payload: Optional[EmergencyPayload] = None
