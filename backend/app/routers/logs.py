from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_active_user, require_roles
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogListResponse
from app.services.audit_log_service import parse_date


router = APIRouter(tags=["logs"])


def apply_log_filters(
    query,
    *,
    user_id: str | None = None,
    username: str | None = None,
    action: str | None = None,
    status: str | None = None,
    file_extension: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if username:
        query = query.filter(AuditLog.username_snapshot == username)
    if action:
        query = query.filter(AuditLog.action == action)
    if status:
        query = query.filter(AuditLog.status == status)
    if file_extension:
        query = query.filter(AuditLog.file_extension == file_extension.lower())
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)
    return query


@router.get("/logs", response_model=AuditLogListResponse)
def list_logs(
    user_id: str | None = None,
    username: str | None = None,
    action: str | None = None,
    status: str | None = None,
    file_extension: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("gerente")),
):
    query = apply_log_filters(
        db.query(AuditLog),
        user_id=user_id,
        username=username,
        action=action,
        status=status,
        file_extension=file_extension,
        date_from=parse_date(date_from),
        date_to=parse_date(date_to),
    )
    total = query.count()
    items = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.get("/logs/me", response_model=AuditLogListResponse)
def list_my_logs(
    action: str | None = None,
    status: str | None = None,
    file_extension: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = apply_log_filters(
        db.query(AuditLog),
        user_id=current_user.id,
        action=action,
        status=status,
        file_extension=file_extension,
        date_from=parse_date(date_from),
        date_to=parse_date(date_to),
    )
    total = query.count()
    items = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "items": items}
