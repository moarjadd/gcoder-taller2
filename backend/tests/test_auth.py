from fastapi.testclient import TestClient

from app.core.security import verify_password
from app.database import SessionLocal, init_db
from app.main import app
from app.models.user import User
from scripts.seed_users import main as seed_users
from tests.auth_helpers import auth_headers


client = TestClient(app)


def test_seed_creates_initial_users_with_bcrypt_hashes():
    seed_users()

    with SessionLocal() as db:
        gerente = db.query(User).filter(User.username == "gerente").first()
        jefe = db.query(User).filter(User.username == "jefe").first()
        operario = db.query(User).filter(User.username == "operario1").first()

    assert gerente is not None
    assert gerente.role == "gerente"
    assert gerente.password_hash != "Gerente12345"
    assert gerente.password_hash.startswith("$2")
    assert verify_password("Gerente12345", gerente.password_hash)

    assert jefe is not None
    assert jefe.role == "jefe_operarios"
    assert jefe.password_hash != "Jefe12345"
    assert jefe.password_hash.startswith("$2")
    assert verify_password("Jefe12345", jefe.password_hash)

    assert operario is not None
    assert operario.role == "operario"
    assert operario.password_hash != "Operario12345"
    assert operario.password_hash.startswith("$2")
    assert verify_password("Operario12345", operario.password_hash)


def test_login_returns_jwt_role_and_username():
    seed_users()

    response = client.post(
        "/api/auth/login",
        json={"username": "jefe", "password": "Jefe12345"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["role"] == "jefe_operarios"
    assert body["username"] == "jefe"


def test_me_returns_current_user_from_token():
    seed_users()
    login_response = client.post(
        "/api/auth/login",
        json={"username": "operario1", "password": "Operario12345"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    body = response.json()

    assert response.status_code == 200, body
    assert body["username"] == "operario1"
    assert body["role"] == "operario"
    assert body["is_active"] is True


def test_protected_endpoints_reject_requests_without_token():
    unauthenticated_client = TestClient(app)

    analyze_response = unauthenticated_client.post("/api/analyze")
    convert_response = unauthenticated_client.post("/api/convert")

    assert analyze_response.status_code == 401
    assert convert_response.status_code == 401


def test_protected_endpoints_reject_invalid_token():
    headers = {"Authorization": "Bearer invalid-token"}

    assert client.post("/api/analyze", headers=headers).status_code == 401
    assert client.post("/api/convert", headers=headers).status_code == 401


def test_role_dependency_accepts_allowed_role():
    response = client.get("/api/auth/me", headers=auth_headers("jefe", "jefe_operarios"))

    assert response.status_code == 200
