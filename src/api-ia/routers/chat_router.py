import logging
from security import verify_api_key
from fastapi import APIRouter, Depends
from services.chat_service import ask_tutor
from models.api_response import ApiResponse
from models.chat_schemas import ChatRequest, ChatResponse


router = APIRouter(prefix="/chat", tags=["Chat"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/ask", response_model=ApiResponse[ChatResponse], dependencies=[Depends(verify_api_key)])
def chat_completion(request: ChatRequest):
    try:
        logger.info('❗ en - <chat_completion>')
        answer = ask_tutor(request.message)
        return ApiResponse.ok(
            data=ChatResponse(content=answer),
            message="Respuesta generada exitosamente"
        )
    except ValueError as e:
        return ApiResponse.error(
            message=f"Error, motivo: {str(e)}",
            code=422,
            method='chat_completion',
            e=e
        )
    except Exception as e:
        return ApiResponse.error(
            message=f"Falla al generar la respuesta",
            code=500,
            method='chat_completion',
            e=e
        )