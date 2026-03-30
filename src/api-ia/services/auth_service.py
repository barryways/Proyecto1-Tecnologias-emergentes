from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.auth_schemas import AuthResponse, LoginRequest, RegisterRequest, SessionResponse, UserResponse

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "users.csv"
USERS_HEADERS = [
    "first_name",
    "last_name",
    "student_id",
    "email",
    "password_hash",
    "role",
    "created_at",
]
JWT_SECRET = os.getenv("JWT_SECRET", "studybot-dev-secret-change-me")
JWT_LIFETIME_DAYS = int(os.getenv("JWT_LIFETIME_DAYS", "365"))
DEFAULT_ADMIN_EMAIL = os.getenv("AUTH_DEFAULT_ADMIN_EMAIL", "admin@landivar.edu.gt").strip().lower()
DEFAULT_ADMIN_PASSWORD = os.getenv("AUTH_DEFAULT_ADMIN_PASSWORD", "Admin123!")
DEFAULT_ADMIN_FIRST_NAME = os.getenv("AUTH_DEFAULT_ADMIN_FIRST_NAME", "Admin")
DEFAULT_ADMIN_LAST_NAME = os.getenv("AUTH_DEFAULT_ADMIN_LAST_NAME", "StudyBot")
DEFAULT_ADMIN_STUDENT_ID = os.getenv("AUTH_DEFAULT_ADMIN_STUDENT_ID", "ADMIN-001")

auth_scheme = HTTPBearer(auto_error=False)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _write_csv_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [dict(row) for row in reader]


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _is_valid_email(email: str) -> bool:
    normalized = _normalize_email(email)
    if "@" not in normalized:
        return False
    local_part, domain_part = normalized.split("@", 1)
    return bool(local_part and domain_part and "." in domain_part)


def hash_password(password: str) -> str:
    iterations = 260000
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt}${derived_key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, raw_iterations, salt, saved_hash = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(raw_iterations),
    )
    return hmac.compare_digest(derived_key.hex(), saved_hash)


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")


def _base64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(f"{raw}{padding}".encode("utf-8"))


def create_jwt(payload: dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_segment = _base64url_encode(
        json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    payload_segment = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    signing_input = f"{header_segment}.{payload_segment}"
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
        ) from exc

    signing_input = f"{header_segment}.{payload_segment}"
    expected_signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(_base64url_encode(expected_signature), signature_segment):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma del token invalida.",
        )

    payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
    expiration = payload.get("exp")

    if not isinstance(expiration, int) or expiration < int(_now().timestamp()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesion expiro.",
        )

    return payload


def _user_to_response(user_record: dict[str, str]) -> UserResponse:
    first_name = user_record["first_name"].strip()
    last_name = user_record["last_name"].strip()
    return UserResponse(
        first_name=first_name,
        last_name=last_name,
        full_name=f"{first_name} {last_name}".strip(),
        student_id=user_record["student_id"],
        email=user_record["email"],
        role=user_record["role"],
    )


def ensure_users_storage() -> None:
    _ensure_data_dir()
    rows = _read_csv_rows(USERS_FILE)

    if any(row.get("role") == "admin" for row in rows):
        return

    admin_record = {
        "first_name": DEFAULT_ADMIN_FIRST_NAME,
        "last_name": DEFAULT_ADMIN_LAST_NAME,
        "student_id": DEFAULT_ADMIN_STUDENT_ID,
        "email": DEFAULT_ADMIN_EMAIL,
        "password_hash": hash_password(DEFAULT_ADMIN_PASSWORD),
        "role": "admin",
        "created_at": _now().isoformat(),
    }
    rows.append(admin_record)
    _write_csv_rows(USERS_FILE, USERS_HEADERS, rows)


def read_users() -> list[dict[str, str]]:
    ensure_users_storage()
    return _read_csv_rows(USERS_FILE)


def find_user_by_email(email: str) -> dict[str, str] | None:
    normalized_email = _normalize_email(email)
    return next((user for user in read_users() if user["email"] == normalized_email), None)


def register_user(payload: RegisterRequest) -> AuthResponse:
    ensure_users_storage()

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
    if find_user_by_email(normalized_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario registrado con ese correo.",
        )

    users = read_users()
    user_record = {
        "first_name": payload.first_name.strip(),
        "last_name": payload.last_name.strip(),
        "student_id": payload.student_id.strip(),
        "email": normalized_email,
        "password_hash": hash_password(payload.password),
        "role": "student",
        "created_at": _now().isoformat(),
    }
    users.append(user_record)
    _write_csv_rows(USERS_FILE, USERS_HEADERS, users)

    return create_auth_response(user_record, portal="chat")


def create_auth_response(user_record: dict[str, str], portal: str) -> AuthResponse:
    expires_at = _now() + timedelta(days=JWT_LIFETIME_DAYS)
    token = create_jwt(
        {
            "sub": user_record["email"],
            "role": user_record["role"],
            "portal": portal,
            "exp": int(expires_at.timestamp()),
            "iat": int(_now().timestamp()),
        }
    )
    return AuthResponse(
        access_token=token,
        expires_at=expires_at.isoformat(),
        portal=portal,
        user=_user_to_response(user_record),
    )


def login_user(payload: LoginRequest) -> AuthResponse:
    user_record = find_user_by_email(payload.email)
    if not user_record or not verify_password(payload.password, user_record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contrasena incorrectos.",
        )

    if payload.portal == "admin" and user_record["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta cuenta no tiene acceso al dashboard de administracion.",
        )

    return create_auth_response(user_record, portal=payload.portal)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> dict[str, str]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se encontro un token de autenticacion.",
        )

    payload = decode_jwt(credentials.credentials)
    user_record = find_user_by_email(payload.get("sub", ""))
    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario autenticado ya no existe.",
        )
    return user_record


def build_session_response(user_record: dict[str, str]) -> SessionResponse:
    return SessionResponse(user=_user_to_response(user_record))
