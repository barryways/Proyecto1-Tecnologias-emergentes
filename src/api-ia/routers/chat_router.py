import logging
from security import verify_api_key
from fastapi import APIRouter, Depends
from services.claude_service import ask_tutor
from models.chat_schemas import ChatRequest, ChatResponse
from dependencies import get_collection_tutor_advanced_programming
from models.api_response import ApiResponse

router = APIRouter(prefix="/chat", tags=["Chat"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/ask", response_model=ApiResponse[ChatResponse], dependencies=[Depends(verify_api_key)])
def chat_completion(request: ChatRequest, collection=Depends(get_collection_tutor_advanced_programming)):
    try:
        logger.info('❗ en - <chat_completion>')
        answer = ask_tutor(request.message, collection)
        logger.info('✅ respuesta generada')
        return ApiResponse.ok(
            data=ChatResponse(content=answer),
            message="Respuesta generada exitosamente"
        )
    except ValueError as e:
        logger.error(f'❌ error en <chat_completion>: {str(e)}')
        return ApiResponse.error(
            message=f"Error, motivo: {str(e)}",
            code=422
        )
    except Exception as e:
        logger.error(f'❌ error en <chat_completion>: {str(e)}')
        return ApiResponse.error(
            message=f"Error al procesar la pregunta",
            code=500
        )