from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.mysql import LONGTEXT, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RolUsuario(Base):
    __tablename__ = "rol_usuario"

    id_rol: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    descripcion: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    fec_creacion: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        UniqueConstraint("no_carnet", name="uq_usuario_no_carnet"),
        UniqueConstraint("correo", name="uq_usuario_correo"),
        Index("idx_usuario_id_rol", "id_rol"),
    )

    id_usuario: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    no_carnet: Mapped[str] = mapped_column(String(20), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), nullable=False)
    clave_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    id_rol: Mapped[int] = mapped_column(
        ForeignKey("rol_usuario.id_rol", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    fec_creacion: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    rol: Mapped[RolUsuario] = relationship(back_populates="usuarios")
    conversaciones: Mapped[list["Conversacion"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    consumos: Mapped[list["ConsumoUsuario"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
    )


class Conversacion(Base):
    __tablename__ = "conversacion"
    __table_args__ = (
        Index("idx_conversacion_id_usuario", "id_usuario"),
    )

    id_conversacion: Mapped[str] = mapped_column(String(36), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuario.id_usuario", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    fec_creacion: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    fec_actualizacion: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    usuario: Mapped[Usuario] = relationship(back_populates="conversaciones")
    mensajes: Mapped[list["Mensaje"]] = relationship(
        back_populates="conversacion",
        cascade="all, delete-orphan",
        order_by="Mensaje.orden_mensaje",
    )


class TipoMensaje(Base):
    __tablename__ = "tipo_mensaje"

    id_tipo_mensaje: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    descripcion: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    mensajes: Mapped[list["Mensaje"]] = relationship(back_populates="tipo_mensaje")


class Mensaje(Base):
    __tablename__ = "mensaje"
    __table_args__ = (
        UniqueConstraint("id_conversacion", "orden_mensaje", name="uq_mensaje_orden"),
        Index("idx_mensaje_id_conversacion", "id_conversacion"),
        Index("idx_mensaje_conversacion_fecha", "id_conversacion", "fecha_hora"),
        Index("idx_mensaje_tipo", "id_tipo_mensaje"),
    )

    id_mensaje: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_conversacion: Mapped[str] = mapped_column(
        ForeignKey("conversacion.id_conversacion", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    id_tipo_mensaje: Mapped[int] = mapped_column(
        ForeignKey("tipo_mensaje.id_tipo_mensaje", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    contenido: Mapped[str] = mapped_column(LONGTEXT().with_variant(Text(), "sqlite"), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    orden_mensaje: Mapped[int] = mapped_column(Integer, nullable=False)

    conversacion: Mapped[Conversacion] = relationship(back_populates="mensajes")
    tipo_mensaje: Mapped[TipoMensaje] = relationship(back_populates="mensajes")


class ConsumoUsuario(Base):
    __tablename__ = "consumo_usuario"
    __table_args__ = (
        Index("idx_consumo_usuario", "id_usuario"),
        Index("idx_consumo_fecha", "fec_consumo"),
        Index("idx_consumo_usuario_fecha", "id_usuario", "fec_consumo"),
    )

    id_consumo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuario.id_usuario", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    tokens_entrada: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_salida: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_totales: Mapped[int] = mapped_column(Integer, nullable=False)
    modelo: Mapped[str] = mapped_column(String(50), nullable=False, default="gpt-3.5-turbo")
    costo_entrada: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    costo_salida: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    costo_total: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    fec_consumo: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="consumos")
