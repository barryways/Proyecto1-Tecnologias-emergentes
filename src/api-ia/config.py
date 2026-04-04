from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name, str(default)).strip().lower()
    return raw_value in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    return int(raw_value)


def build_database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url

    host = os.getenv("DB_HOST", "localhost").strip()
    port = os.getenv("DB_PORT", "3306").strip()
    name = os.getenv("DB_NAME", "studybot_db").strip()
    user = quote_plus(os.getenv("DB_USER", "root").strip())
    password = os.getenv("DB_PASSWORD", "").strip()

    credentials = user
    if password:
        credentials = f"{credentials}:{quote_plus(password)}"

    return f"mysql+pymysql://{credentials}@{host}:{port}/{name}?charset=utf8mb4"


CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

DATABASE_URL = build_database_url()
DB_ECHO = env_bool("DB_ECHO", False)
DB_SSL_ENABLED = env_bool("DB_SSL_ENABLED", False)
DB_SSL_CA = os.getenv("DB_SSL_CA", "").strip()

JWT_SECRET = os.getenv("JWT_SECRET", "studybot-dev-secret-change-me")
JWT_LIFETIME_DAYS = env_int("JWT_LIFETIME_DAYS", 365)

DEFAULT_ADMIN_EMAIL = os.getenv("AUTH_DEFAULT_ADMIN_EMAIL", "admin@landivar.edu.gt").strip().lower()
DEFAULT_ADMIN_PASSWORD = os.getenv("AUTH_DEFAULT_ADMIN_PASSWORD", "Admin123!")
DEFAULT_ADMIN_FIRST_NAME = os.getenv("AUTH_DEFAULT_ADMIN_FIRST_NAME", "Admin").strip()
DEFAULT_ADMIN_LAST_NAME = os.getenv("AUTH_DEFAULT_ADMIN_LAST_NAME", "StudyBot").strip()
DEFAULT_ADMIN_STUDENT_ID = os.getenv("AUTH_DEFAULT_ADMIN_STUDENT_ID", "ADMIN-001").strip()
