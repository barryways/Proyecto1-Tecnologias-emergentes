from typing import Literal

from pydantic import BaseModel


PortalType = Literal["chat", "admin"]
RoleType = Literal["student", "admin"]


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    student_id: str
    password: str
    confirm_password: str
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str
    portal: PortalType = "chat"


class UserResponse(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    student_id: str
    email: str
    role: RoleType


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    portal: PortalType
    user: UserResponse


class SessionResponse(BaseModel):
    authenticated: bool = True
    user: UserResponse
