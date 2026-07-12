from app.core.security import create_access_token, get_password_hash
from app.database import SessionLocal, init_db
from app.models.user import User


def auth_headers(username: str = "jefe", role: str = "jefe_operarios") -> dict[str, str]:
    init_db()
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            db.add(
                User(
                    username=username,
                    password_hash=get_password_hash("Test12345"),
                    role=role,
                    is_active=True,
                )
            )
        elif not user.is_active or user.role != role:
            user.is_active = True
            user.role = role
        db.commit()

    token = create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}
