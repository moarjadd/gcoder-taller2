from datetime import datetime
from pathlib import PurePath

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


SENSITIVE_MARKERS = ("password", "contraseña", "token", "bearer", "authorization")


def sanitize_filename(filename: str | None) -> tuple[str | None, str | None]:
    if not filename:
        return None, None
    name = PurePath(filename.replace("\\", "/")).name
    if not name:
        return None, None
    extension = name.rsplit(".", 1)[1].lower() if "." in name else None
    return name[:255], extension[:20] if extension else None


def sanitize_detail(detail: str | None) -> str | None:
    if not detail:
        return None
    lowered = detail.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        return "[redacted]"
    return detail[:500]


def request_metadata(request: Request | None) -> tuple[str | None, str | None]:
    if request is None:
        return None, None
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent[:255] if user_agent else None


def create_audit_log(
    db: Session,
    *,
    action: str,
    status: str,
    user: User | None = None,
    resource: str | None = None,
    file_name: str | None = None,
    file_extension: str | None = None,
    detail: str | None = None,
    request: Request | None = None,
    username_snapshot: str | None = None,
    user_role: str | None = None,
) -> AuditLog:
    safe_file_name, detected_extension = sanitize_filename(file_name)
    ip_address, user_agent = request_metadata(request)
    audit_log = AuditLog(
        user_id=user.id if user else None,
        username_snapshot=user.username if user else username_snapshot,
        user_role=user.role if user else user_role,
        action=action,
        resource=resource,
        file_name=safe_file_name,
        file_extension=(file_extension or detected_extension).lower()[:20] if (file_extension or detected_extension) else None,
        status=status,
        detail=sanitize_detail(detail),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def params_detail(params: object) -> str:
    values = []
    for field_name in ("step_down_mm", "feed_rate_mm_min", "spindle_rpm", "safe_z_mm"):
        value = getattr(params, field_name, None)
        if value is not None:
            values.append(f"{field_name}={value}")
    return ", ".join(values)


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
