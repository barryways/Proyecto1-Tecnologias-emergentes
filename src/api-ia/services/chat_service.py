from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from models.chat_schemas import ChatMessage, ConversationDetail

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONVERSATIONS_FILE = DATA_DIR / "conversación.csv"
CONVERSATION_HEADERS = [
    "conversation_id",
    "email",
    "title",
    "created_at",
    "updated_at",
    "messages_json",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_conversations_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CONVERSATIONS_FILE.exists():
        return

    with CONVERSATIONS_FILE.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CONVERSATION_HEADERS)
        writer.writeheader()


def _read_rows() -> list[dict[str, str]]:
    ensure_conversations_storage()
    with CONVERSATIONS_FILE.open("r", newline="", encoding="utf-8") as csv_file:
        return [dict(row) for row in csv.DictReader(csv_file)]


def _write_rows(rows: Iterable[dict[str, str]]) -> None:
    ensure_conversations_storage()
    with CONVERSATIONS_FILE.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CONVERSATION_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def _derive_title(messages: list[dict[str, str]]) -> str:
    first_user_message = next((item["content"] for item in messages if item["role"] == "user"), "")
    if not first_user_message:
        return "Nueva conversacion"
    trimmed = " ".join(first_user_message.split())
    return trimmed[:57] + "..." if len(trimmed) > 60 else trimmed


def _deserialize_row(row: dict[str, str]) -> ConversationDetail:
    messages = json.loads(row.get("messages_json") or "[]")
    return ConversationDetail(
        conversation_id=row["conversation_id"],
        title=row["title"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        message_count=len(messages),
        messages=[ChatMessage(**message) for message in messages],
    )


def list_conversations(email: str) -> list[ConversationDetail]:
    rows = [row for row in _read_rows() if row["email"] == email]
    conversations = [_deserialize_row(row) for row in rows]
    return sorted(conversations, key=lambda item: item.updated_at, reverse=True)


def build_agent_reply(message: str, history: list[ChatMessage]) -> str:
    prompt_length = len(history)
    return (
        "Respuesta generada desde el backend Python.\n\n"
        f"Tu consulta fue: {message}\n"
        f"Mensajes en el contexto: {prompt_length}.\n\n"
        "Aqui puedes conectar despues tu modelo real para enriquecer la respuesta del agente."
    )


def save_conversation(
    email: str,
    message: str,
    history: list[ChatMessage],
    conversation_id: str | None = None,
) -> tuple[str, ConversationDetail]:
    rows = _read_rows()
    assistant_reply = build_agent_reply(message, history)
    timestamp = _now_iso()
    normalized_history = [
        {
            "role": item.role,
            "content": item.content,
            "timestamp": (item.timestamp or datetime.now(timezone.utc)).isoformat(),
        }
        for item in history
    ]

    if not normalized_history or normalized_history[-1]["role"] != "assistant":
        normalized_history.append(
            {
                "role": "assistant",
                "content": assistant_reply,
                "timestamp": timestamp,
            }
        )

    target_id = conversation_id or str(uuid4())
    existing_row = next(
        (row for row in rows if row["email"] == email and row["conversation_id"] == target_id),
        None,
    )

    if existing_row:
        created_at = existing_row["created_at"]
        existing_row["title"] = _derive_title(normalized_history)
        existing_row["updated_at"] = timestamp
        existing_row["messages_json"] = json.dumps(normalized_history, ensure_ascii=False)
    else:
        created_at = timestamp
        rows.append(
            {
                "conversation_id": target_id,
                "email": email,
                "title": _derive_title(normalized_history),
                "created_at": created_at,
                "updated_at": timestamp,
                "messages_json": json.dumps(normalized_history, ensure_ascii=False),
            }
        )

    _write_rows(rows)

    saved_row = next(
        row for row in rows if row["email"] == email and row["conversation_id"] == target_id
    )
    return assistant_reply, _deserialize_row(saved_row)
