from fastapi import APIRouter
from models.chat_schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/completions")
async def chat_completion(request: ChatRequest):
    return ChatResponse(content="Hello, world!")
