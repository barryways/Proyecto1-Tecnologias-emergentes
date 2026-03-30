from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["assistant", "user", "system"]
    content: str
    timestamp: Optional[datetime] = None


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationDetail(ConversationSummary):
    messages: list[ChatMessage] = Field(default_factory=list)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: list[ChatMessage] = Field(default_factory=list)
    max_tokens: Optional[int] = 1024

class ChatResponse(BaseModel):
    content: str
    conversation: ConversationDetail
