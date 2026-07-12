import sys
from pathlib import Path

from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.security import get_password_hash
from app.database import SessionLocal, init_db
from app.models.user import User


INITIAL_USERS = [
    {"username": "gerente", "password": "Gerente12345", "role": "gerente"},
    {"username": "jefe", "password": "Jefe12345", "role": "jefe_operarios"},
    {"username": "operario1", "password": "Operario12345", "role": "operario"},
]


def upsert_user(db: Session, username: str, password: str, role: str) -> None:
    user = db.query(User).filter(User.username == username).first()
    password_hash = get_password_hash(password)

    if user is None:
        db.add(User(username=username, password_hash=password_hash, role=role, is_active=True))
        return

    user.password_hash = password_hash
    user.role = role
    user.is_active = True


def main() -> None:
    init_db()
    with SessionLocal() as db:
        for user_data in INITIAL_USERS:
            upsert_user(db, user_data["username"], user_data["password"], user_data["role"])
        db.commit()

    print("Usuarios iniciales creados o actualizados: gerente, jefe, operario1")


if __name__ == "__main__":
    main()
