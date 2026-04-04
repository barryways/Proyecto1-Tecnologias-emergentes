from __future__ import annotations

from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

from config import (
    DATABASE_URL,
    DB_ECHO,
    DB_SSL_CA,
    DB_SSL_ENABLED,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_FIRST_NAME,
    DEFAULT_ADMIN_LAST_NAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_STUDENT_ID,
)
from db_models import Base, RolUsuario, TipoMensaje, Usuario
from security import hash_password

ROLE_DESCRIPTIONS = ("admin", "student")
MESSAGE_TYPE_DESCRIPTIONS = ("user", "assistant", "system")

connect_args: dict[str, object] = {}

if DB_SSL_ENABLED:
    ssl_options: dict[str, str] = {}
    if DB_SSL_CA:
        ssl_options["ca"] = str(Path(DB_SSL_CA).expanduser())
    connect_args["ssl"] = ssl_options

engine = create_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def init_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        ensure_bootstrap_data(session)
        session.commit()


def ensure_bootstrap_data(session: Session) -> None:
    _ensure_roles(session)
    _ensure_message_types(session)
    _ensure_default_admin(session)


def _ensure_roles(session: Session) -> None:
    existing_roles = set(session.scalars(select(RolUsuario.descripcion)).all())
    for description in ROLE_DESCRIPTIONS:
        if description not in existing_roles:
            session.add(RolUsuario(descripcion=description))
    session.flush()


def _ensure_message_types(session: Session) -> None:
    existing_types = set(session.scalars(select(TipoMensaje.descripcion)).all())
    for description in MESSAGE_TYPE_DESCRIPTIONS:
        if description not in existing_types:
            session.add(TipoMensaje(descripcion=description))
    session.flush()


def _ensure_default_admin(session: Session) -> None:
    if not DEFAULT_ADMIN_EMAIL or not DEFAULT_ADMIN_PASSWORD:
        return

    existing_admin = session.scalar(
        select(Usuario).where(
            or_(
                Usuario.correo == DEFAULT_ADMIN_EMAIL,
                Usuario.no_carnet == DEFAULT_ADMIN_STUDENT_ID,
            )
        )
    )
    if existing_admin:
        return

    admin_role = session.scalar(select(RolUsuario).where(RolUsuario.descripcion == "admin"))
    if admin_role is None:
        raise RuntimeError("No fue posible inicializar el rol de administrador.")

    session.add(
        Usuario(
            nombre=DEFAULT_ADMIN_FIRST_NAME,
            apellido=DEFAULT_ADMIN_LAST_NAME,
            no_carnet=DEFAULT_ADMIN_STUDENT_ID,
            correo=DEFAULT_ADMIN_EMAIL,
            clave_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            id_rol=admin_role.id_rol,
        )
    )
    session.flush()
