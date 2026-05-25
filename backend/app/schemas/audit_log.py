from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None
    username_snapshot: str | None
    user_role: str | None
    action: str
    resource: str | None
    file_name: str | None
    file_extension: str | None
    status: str
    detail: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    total: int
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)
    items: list[AuditLogResponse]
