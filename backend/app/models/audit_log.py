from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    username_snapshot: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    resource: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_extension: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
