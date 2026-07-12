from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.audit_log_service import create_audit_log


router = APIRouter(tags=["auth"])


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if user is None or not user.is_active:
        existing_user = db.query(User).filter(User.username == payload.username).first()
        create_audit_log(
            db,
            action="LOGIN_FAILED",
            status="failed",
            user=existing_user if existing_user else None,
            username_snapshot=payload.username,
            user_role=existing_user.role if existing_user else None,
            resource="auth",
            detail="Credenciales invalidas o usuario inactivo.",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    create_audit_log(
        db,
        action="LOGIN_SUCCESS",
        status="success",
        user=user,
        resource="auth",
        detail="Inicio de sesion correcto.",
        request=request,
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
    }


@router.get("/auth/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/auth/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    create_audit_log(
        db,
        action="LOGOUT",
        status="success",
        user=current_user,
        resource="auth",
        detail="Cierre de sesion solicitado por el usuario.",
        request=request,
    )
    return {"status": "ok"}
