from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload

from config import JWT_LIFETIME_DAYS
from database import SessionLocal, ensure_bootstrap_data
from db_models import RolUsuario, Usuario
from models.auth_schemas import AuthResponse, LoginRequest, RegisterRequest, SessionResponse, UserResponse
from security import create_jwt, decode_jwt, hash_password, now_utc, verify_password

auth_scheme = HTTPBearer(auto_error=False)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _is_valid_email(email: str) -> bool:
    normalized = _normalize_email(email)
    if "@" not in normalized:
        return False
    local_part, domain_part = normalized.split("@", 1)
    return bool(local_part and domain_part and "." in domain_part)


def _user_to_record(user: Usuario) -> dict[str, Any]:
    role = user.rol.descripcion if user.rol else "student"
    return {
        "id_usuario": user.id_usuario,
        "first_name": user.nombre.strip(),
        "last_name": user.apellido.strip(),
        "student_id": user.no_carnet.strip(),
        "email": user.correo.strip(),
        "role": role,
    }


def _user_to_response(user_record: dict[str, Any]) -> UserResponse:
    first_name = user_record["first_name"]
    last_name = user_record["last_name"]
    return UserResponse(
        first_name=first_name,
        last_name=last_name,
        full_name=f"{first_name} {last_name}".strip(),
        student_id=user_record["student_id"],
        email=user_record["email"],
        role=user_record["role"],
    )


def _find_user_by_email(session, email: str) -> Usuario | None:
    normalized_email = _normalize_email(email)
    return session.scalar(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(Usuario.correo == normalized_email)
    )


def _find_user_by_id(session, user_id: int) -> Usuario | None:
    return session.scalar(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(Usuario.id_usuario == user_id)
    )


def _get_role(session, description: str) -> RolUsuario | None:
    return session.scalar(select(RolUsuario).where(RolUsuario.descripcion == description))


def register_user(payload: RegisterRequest) -> AuthResponse:
    if not all(
        [
            payload.first_name.strip(),
            payload.last_name.strip(),
            payload.student_id.strip(),
            payload.password.strip(),
            payload.confirm_password.strip(),
            payload.email.strip(),
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todos los campos del registro son obligatorios.",
        )

    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La confirmacion de contrasena no coincide.",
        )

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contrasena debe tener al menos 8 caracteres.",
        )

    if not _is_valid_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes ingresar un correo institucional valido.",
        )

    normalized_email = _normalize_email(payload.email)
    normalized_student_id = payload.student_id.strip()

    with SessionLocal() as session:
        ensure_bootstrap_data(session)

        existing_user = session.scalar(
            select(Usuario).where(
                or_(
                    Usuario.correo == normalized_email,
                    Usuario.no_carnet == normalized_student_id,
                )
            )
        )
        if existing_user:
            if existing_user.correo == normalized_email:
                detail = "Ya existe un usuario registrado con ese correo."
            else:
                detail = "Ya existe un usuario registrado con ese carnet."
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

        student_role = _get_role(session, "student")
        if student_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No fue posible resolver el rol de estudiante.",
            )

        user = Usuario(
            nombre=payload.first_name.strip(),
            apellido=payload.last_name.strip(),
            no_carnet=normalized_student_id,
            correo=normalized_email,
            clave_hash=hash_password(payload.password),
            id_rol=student_role.id_rol,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        user_with_role = _find_user_by_id(session, user.id_usuario)
        if user_with_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No fue posible recuperar el usuario recien registrado.",
            )

        return create_auth_response(_user_to_record(user_with_role), portal="chat")


def create_auth_response(user_record: dict[str, Any], portal: str) -> AuthResponse:
    issued_at = now_utc()
    expires_at = issued_at + timedelta(days=JWT_LIFETIME_DAYS)
    token = create_jwt(
        {
            "sub": str(user_record["id_usuario"]),
            "email": user_record["email"],
            "role": user_record["role"],
            "portal": portal,
            "exp": int(expires_at.timestamp()),
            "iat": int(issued_at.timestamp()),
        }
    )
    return AuthResponse(
        access_token=token,
        expires_at=expires_at.isoformat(),
        portal=portal,
        user=_user_to_response(user_record),
    )


def login_user(payload: LoginRequest) -> AuthResponse:
    with SessionLocal() as session:
        ensure_bootstrap_data(session)
        user = _find_user_by_email(session, payload.email)
        if not user or not verify_password(payload.password, user.clave_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contrasena incorrectos.",
            )

        user_record = _user_to_record(user)
        if payload.portal == "admin" and user_record["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Esta cuenta no tiene acceso al dashboard de administracion.",
            )

        return create_auth_response(user_record, portal=payload.portal)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se encontro un token de autenticacion.",
        )

    payload = decode_jwt(credentials.credentials)
    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de autenticacion es invalido.",
        ) from exc

    with SessionLocal() as session:
        ensure_bootstrap_data(session)
        user = _find_user_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El usuario autenticado ya no existe.",
            )
        return _user_to_record(user)


def build_session_response(user_record: dict[str, Any]) -> SessionResponse:
    return SessionResponse(user=_user_to_response(user_record))
