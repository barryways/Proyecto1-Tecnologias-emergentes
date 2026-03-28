from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    max_tokens: Optional[int] = 1024

class ChatResponse(BaseModel):
    content: str