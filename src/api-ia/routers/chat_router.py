from fastapi import APIRouter, Depends
from models.chat_schemas import ChatRequest, ChatResponse
from dependencies import get_collection_tutor_advanced_programming
from services.claude_service import ask_tutor

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/ask", response_model=ChatResponse)
async def chat_completion(request: ChatRequest, collection=Depends(get_collection_tutor_advanced_programming)):
    answer = ask_tutor(request.message, collection)
    return ChatResponse(content=answer)
