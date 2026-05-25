from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


UserRole = Literal["gerente", "jefe_operarios", "operario"]


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: UserRole
    username: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
