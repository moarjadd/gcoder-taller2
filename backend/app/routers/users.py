from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.user import User
from app.schemas.users import UserAdminResponse, UserCreateRequest, UserUpdateRequest
from app.services.audit_log_service import create_audit_log


router = APIRouter(tags=["users"])


def get_user_or_404(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return user


def ensure_jefe_can_manage_target(target_user: User) -> None:
    if target_user.role != "operario":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El jefe de operarios solo puede gestionar usuarios operarios.",
        )


def ensure_unique_username(db: Session, username: str, exclude_user_id: str | None = None) -> None:
    query = db.query(User).filter(User.username == username)
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    if query.first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario ya existe.")


@router.post("/users", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("jefe_operarios")),
):
    if payload.role != "operario":
        create_audit_log(
            db,
            action="USER_CREATE_FAILED",
            status="failed",
            user=current_user,
            resource="users",
            detail=f"Intento de crear usuario con rol no permitido: role={payload.role}, username={payload.username}",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El jefe de operarios solo puede crear usuarios con rol operario.",
        )

    try:
        ensure_unique_username(db, payload.username)
    except HTTPException:
        create_audit_log(
            db,
            action="USER_CREATE_FAILED",
            status="failed",
            user=current_user,
            resource="users",
            detail=f"Username duplicado al crear operario: username={payload.username}",
            request=request,
        )
        raise

    user = User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role="operario",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    create_audit_log(
        db,
        action="USER_CREATED",
        status="success",
        user=current_user,
        resource="users",
        detail=f"Operario creado. target_user_id={user.id}, target_username={user.username}",
        request=request,
    )
    return user


@router.get("/users", response_model=list[UserAdminResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("gerente", "jefe_operarios")),
):
    query = db.query(User)
    if current_user.role == "jefe_operarios":
        query = query.filter(User.role == "operario")
    return query.order_by(User.username.asc()).all()


@router.get("/users/{user_id}", response_model=UserAdminResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("gerente", "jefe_operarios")),
):
    user = get_user_or_404(db, user_id)
    if current_user.role == "jefe_operarios":
        ensure_jefe_can_manage_target(user)
    return user


@router.patch("/users/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("jefe_operarios")),
):
    try:
        target_user = get_user_or_404(db, user_id)
        ensure_jefe_can_manage_target(target_user)
    except HTTPException as exc:
        create_audit_log(
            db,
            action="USER_UPDATE_FAILED",
            status="failed",
            user=current_user,
            resource="users",
            detail=f"No se pudo actualizar usuario. target_user_id={user_id}, reason={exc.detail}",
            request=request,
        )
        raise

    changes: list[str] = []
    if payload.username is not None and payload.username != target_user.username:
        try:
            ensure_unique_username(db, payload.username, exclude_user_id=target_user.id)
        except HTTPException:
            create_audit_log(
                db,
                action="USER_UPDATE_FAILED",
                status="failed",
                user=current_user,
                resource="users",
                detail=f"Username duplicado al actualizar operario. target_user_id={target_user.id}",
                request=request,
            )
            raise
        target_user.username = payload.username
        changes.append("username")

    if payload.password is not None:
        target_user.password_hash = get_password_hash(payload.password)
        changes.append("password")

    if payload.is_active is not None and payload.is_active != target_user.is_active:
        target_user.is_active = payload.is_active
        changes.append("is_active")

    if not changes:
        return target_user

    db.commit()
    db.refresh(target_user)

    action = "USER_UPDATED"
    if changes == ["is_active"]:
        action = "USER_REACTIVATED" if target_user.is_active else "USER_DEACTIVATED"

    safe_changes = ["password_changed" if change == "password" else change for change in changes]
    create_audit_log(
        db,
        action=action,
        status="success",
        user=current_user,
        resource="users",
        detail=f"Operario actualizado. target_user_id={target_user.id}, target_username={target_user.username}, changes={','.join(safe_changes)}",
        request=request,
    )
    return target_user


@router.delete("/users/{user_id}", response_model=UserAdminResponse)
def deactivate_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("jefe_operarios")),
):
    try:
        target_user = get_user_or_404(db, user_id)
        ensure_jefe_can_manage_target(target_user)
    except HTTPException as exc:
        create_audit_log(
            db,
            action="USER_DEACTIVATE_FAILED",
            status="failed",
            user=current_user,
            resource="users",
            detail=f"No se pudo desactivar usuario. target_user_id={user_id}, reason={exc.detail}",
            request=request,
        )
        raise

    if not target_user.is_active:
        create_audit_log(
            db,
            action="USER_DEACTIVATED",
            status="warning",
            user=current_user,
            resource="users",
            detail=f"Operario ya estaba inactivo. target_user_id={target_user.id}, target_username={target_user.username}",
            request=request,
        )
        return target_user

    target_user.is_active = False
    db.commit()
    db.refresh(target_user)
    create_audit_log(
        db,
        action="USER_DEACTIVATED",
        status="success",
        user=current_user,
        resource="users",
        detail=f"Operario desactivado. target_user_id={target_user.id}, target_username={target_user.username}",
        request=request,
    )
    return target_user
