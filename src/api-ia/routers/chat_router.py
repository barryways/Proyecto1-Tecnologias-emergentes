from fastapi import APIRouter, Depends, File, UploadFile

from models.chat_schemas import ChatRequest, ChatResponse, DashboardConsumo, ConversationDetail, UsuarioResumen
from models.stt_schemas import TranscriptionResponse
from services.auth_service import get_current_user
from services.chat_service import get_consumo_usuario, list_conversations, list_usuarios, save_conversation
from services.stt_service import transcribe_wav_audio

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/conversations", response_model=list[ConversationDetail])
async def get_conversations(
    current_user: dict[str, object] = Depends(get_current_user),
):
    return list_conversations(int(current_user["id_usuario"]))


@router.post("/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    current_user: dict[str, object] = Depends(get_current_user),
):
    assistant_reply, conversation = save_conversation(
        user_id=int(current_user["id_usuario"]),
        message=request.message,
        history=request.history,
        conversation_id=request.conversation_id,
        max_tokens=request.max_tokens,
    )
    return ChatResponse(content=assistant_reply, conversation=conversation)


@router.get("/usuarios", response_model=list[UsuarioResumen])
async def get_usuarios():
    return list_usuarios()


@router.get("/tokens/{user_id}", response_model=DashboardConsumo)
async def get_token_usage(
    user_id: int
):
    return get_consumo_usuario(user_id)


@router.post("/transcriptions", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user: dict[str, str] = Depends(get_current_user),
):
    _ = current_user
    audio_bytes = await audio.read()
    transcript = transcribe_wav_audio(audio_bytes)
    return TranscriptionResponse(text=transcript)
