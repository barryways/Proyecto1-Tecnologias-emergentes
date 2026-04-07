from datetime import datetime
from decimal import Decimal
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


class UsuarioResumen(BaseModel):
    id_usuario: int
    nombre: str
    apellido: str


class ConsultaDetalle(BaseModel):
    tokens_entrada: int
    tokens_salida: int
    tokens_totales: int
    modelo: str
    costo_entrada: Decimal
    costo_salida: Decimal
    costo_total: Decimal
    fec_consumo: str


class ResumenConsumo(BaseModel):
    costo_total: Decimal
    tokens_totales: int
    total_consultas: int


class DashboardConsumo(BaseModel):
    nombre_completo: str
    resumen: ResumenConsumo
    ultimo_consumo: Optional[str]
    ultimas_consultas: list[ConsultaDetalle]
