from fastapi import APIRouter, Depends

from models.auth_schemas import AuthResponse, LoginRequest, RegisterRequest, SessionResponse
from services.auth_service import build_session_response, get_current_user, login_user, register_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest) -> AuthResponse:
    return register_user(payload)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    return login_user(payload)


@router.get("/me", response_model=SessionResponse)
async def me(current_user: dict[str, str] = Depends(get_current_user)) -> SessionResponse:
    return build_session_response(current_user)
