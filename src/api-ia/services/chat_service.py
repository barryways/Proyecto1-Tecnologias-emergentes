
from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
from uuid import uuid4

from fastapi import HTTPException, status
from openai import OpenAI
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from database import SessionLocal, ensure_bootstrap_data
from db_models import Conversacion, Mensaje, TipoMensaje
from models.chat_schemas import ChatMessage, ConversationDetail


def _to_api_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_db_datetime(value: datetime | None) -> datetime:
    source = value or datetime.now(timezone.utc)
    if source.tzinfo is None:
        return source
    return source.astimezone(timezone.utc).replace(tzinfo=None)


def _derive_title(messages: list[dict[str, object]]) -> str:
    first_user_message = next((item["content"] for item in messages if item["role"] == "user"), "")
    if not isinstance(first_user_message, str) or not first_user_message:
        return "Nueva conversacion"
    trimmed = " ".join(first_user_message.split())
    return trimmed[:57] + "..." if len(trimmed) > 60 else trimmed


def _conversation_to_detail(conversation: Conversacion) -> ConversationDetail:
    messages = [
        ChatMessage(
            role=message.tipo_mensaje.descripcion,
            content=message.contenido,
            timestamp=_to_api_datetime(message.fecha_hora),
        )
        for message in conversation.mensajes
    ]
    return ConversationDetail(
        conversation_id=conversation.id_conversacion,
        title=conversation.titulo,
        created_at=_to_api_datetime(conversation.fec_creacion),
        updated_at=_to_api_datetime(conversation.fec_actualizacion),
        message_count=len(messages),
        messages=messages,
    )


def _load_conversation(session, conversation_id: str) -> Conversacion | None:
    return session.scalar(
        select(Conversacion)
        .options(selectinload(Conversacion.mensajes).selectinload(Mensaje.tipo_mensaje))
        .where(Conversacion.id_conversacion == conversation_id)
    )


def _normalize_openai_history(history: list[ChatMessage], message: str) -> list[dict[str, str]]:
    normalized_messages: list[dict[str, str]] = []

    for item in history:
        content = item.content.strip()
        if not content:
            continue
        normalized_messages.append(
            {
                "role": item.role,
                "content": content,
            }
        )

    trimmed_message = message.strip()
    if trimmed_message and (
        not normalized_messages
        or normalized_messages[-1]["role"] != "user"
        or normalized_messages[-1]["content"] != trimmed_message
    ):
        normalized_messages.append({"role": "user", "content": trimmed_message})

    return normalized_messages


def list_conversations(user_id: int) -> list[ConversationDetail]:
    with SessionLocal() as session:
        ensure_bootstrap_data(session)
        conversations = session.scalars(
            select(Conversacion)
            .options(selectinload(Conversacion.mensajes).selectinload(Mensaje.tipo_mensaje))
            .where(Conversacion.id_usuario == user_id)
            .order_by(Conversacion.fec_actualizacion.desc())
        ).unique().all()
        return [_conversation_to_detail(conversation) for conversation in conversations]


def _get_openai_client() -> tuple[OpenAI, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model_id = os.getenv("OPENAI_MODEL_ID", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falta configurar OPENAI_API_KEY en el backend.",
        )

    if not model_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falta configurar OPENAI_MODEL_ID en el backend.",
        )

    return OpenAI(api_key=api_key), model_id


def ask_tutor(
    message: str,
    history: list[ChatMessage],
    max_tokens: int | None = 1024,
) -> str:
    trimmed_message = message.strip()
    if not trimmed_message:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La pregunta no puede estar vacía.",
        )

    openai_client, model_id = _get_openai_client()
    messages = [
        {
            "role": "system",
            "content": (
                "Eres un tutor virtual del curso de Programacion Avanzada. "
                "Responde unicamente basandote en el contexto del curso.\n\n"
                "FORMATO DE RESPUESTA:\n"
                "- Responde siempre en formato Markdown\n"
                "- Usa ## para titulos de secciones\n"
                "- Usa **negrita** para conceptos importantes\n"
                "- Usa listas con - para enumerar puntos\n"
                "- Usa bloques de codigo con ```cpp o ```pseudocode para ejemplos de codigo\n\n"
                "IMPORTANTE:\n"
                "- No entregues codigo completo listo para ejecutar\n"
                "- Puedes dar pseudocodigo o fragmentos parciales explicativos\n"
                "- Explica que hacer pero no como hacerlo con codigo exacto\n"
                "- Si la pregunta esta fuera del curso responde: "
                "'Esa pregunta esta fuera del contenido del curso.'\n"
                "- Responde siempre en espanol de manera clara y didactica"
            ),
        },
        *_normalize_openai_history(history, trimmed_message),
    ]

    request_options: dict[str, object] = {
        "model": model_id,
        "messages": messages,
    }
    if max_tokens:
        request_options["max_tokens"] = max_tokens

    try:
        response = openai_client.chat.completions.create(**request_options)
    except Exception as exc:
        _logger.exception("No fue posible obtener respuesta del modelo de OpenAI.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No fue posible obtener respuesta del modelo de IA.",
        ) from exc

    content = response.choices[0].message.content if response.choices else None
    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="El modelo de IA no devolvio contenido.",
        )

    return content


def save_conversation(
    user_id: int,
    message: str,
    history: list[ChatMessage],
    conversation_id: str | None = None,
    max_tokens: int | None = 1024,
) -> tuple[str, ConversationDetail]:
    timestamp = datetime.now(timezone.utc)
    trimmed_message = message.strip()
    assistant_reply = ask_tutor(message=trimmed_message, history=history, max_tokens=max_tokens)
    normalized_history = [
        {
            "role": item.role,
            "content": item.content,
            "timestamp": _to_db_datetime(item.timestamp),
        }
        for item in history
    ]

    if trimmed_message and (
        not normalized_history
        or normalized_history[-1]["role"] != "user"
        or str(normalized_history[-1]["content"]).strip() != trimmed_message
    ):
        normalized_history.append(
            {
                "role": "user",
                "content": trimmed_message,
                "timestamp": _to_db_datetime(timestamp),
            }
        )

    if not normalized_history or normalized_history[-1]["role"] != "assistant":
        normalized_history.append(
            {
                "role": "assistant",
                "content": assistant_reply,
                "timestamp": _to_db_datetime(timestamp),
            }
        )

    target_id = conversation_id or str(uuid4())

    with SessionLocal() as session:
        ensure_bootstrap_data(session)

        message_types = {
            item.descripcion: item.id_tipo_mensaje
            for item in session.scalars(select(TipoMensaje)).all()
        }
        if not {"user", "assistant", "system"}.issubset(message_types):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudieron resolver los tipos de mensaje en la base de datos.",
            )

        conversation = _load_conversation(session, target_id)
        if conversation and conversation.id_usuario != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar esta conversacion.",
            )

        if conversation is None:
            conversation = Conversacion(
                id_conversacion=target_id,
                id_usuario=user_id,
                titulo=_derive_title(normalized_history),
                fec_actualizacion=_to_db_datetime(timestamp),
            )
            session.add(conversation)
            session.flush()
        else:
            conversation.titulo = _derive_title(normalized_history)
            conversation.fec_actualizacion = _to_db_datetime(timestamp)
            session.execute(delete(Mensaje).where(Mensaje.id_conversacion == target_id))
            session.flush()

        for order, item in enumerate(normalized_history, start=1):
            session.add(
                Mensaje(
                    id_conversacion=target_id,
                    id_tipo_mensaje=message_types[str(item["role"])],
                    contenido=str(item["content"]),
                    fecha_hora=item["timestamp"],
                    orden_mensaje=order,
                )
            )

        session.commit()
        saved_conversation = _load_conversation(session, target_id)
        if saved_conversation is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No fue posible recuperar la conversacion guardada.",
            )

        return assistant_reply, _conversation_to_detail(saved_conversation)


_logger = logging.getLogger(__name__)

