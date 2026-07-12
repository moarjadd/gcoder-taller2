from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.auth import UserRole


def normalize_username(value: str) -> str:
    username = value.strip()
    if not username:
        raise ValueError("El username no puede estar vacío.")
    return username


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=72)
    role: UserRole = "operario"

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return normalize_username(value)


class UserUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=80)
    password: str | None = Field(default=None, min_length=8, max_length=72)
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        return normalize_username(value) if value is not None else None


class UserAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
