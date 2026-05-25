from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from tests.auth_helpers import auth_headers


client = TestClient(app)


def _unique_username(prefix: str = "operario") -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _count_logs(action: str) -> int:
    with SessionLocal() as db:
        return db.query(AuditLog).filter(AuditLog.action == action).count()


def _create_operario(username: str | None = None, password: str = "Operario12345") -> dict:
    response = client.post(
        "/api/users",
        headers=auth_headers("jefe", "jefe_operarios"),
        json={"username": username or _unique_username(), "password": password, "role": "operario"},
    )
    assert response.status_code == 201, response.json()
    return response.json()


def test_jefe_operarios_can_create_operario_and_response_does_not_include_password_hash():
    before = _count_logs("USER_CREATED")
    response = client.post(
        "/api/users",
        headers=auth_headers("jefe", "jefe_operarios"),
        json={"username": _unique_username(), "password": "Operario12345", "role": "operario"},
    )
    body = response.json()

    assert response.status_code == 201, body
    assert body["role"] == "operario"
    assert body["is_active"] is True
    assert "password_hash" not in body
    assert "password" not in body
    assert _count_logs("USER_CREATED") == before + 1


def test_jefe_operarios_cannot_create_gerente_or_other_jefe():
    gerente_response = client.post(
        "/api/users",
        headers=auth_headers("jefe", "jefe_operarios"),
        json={"username": _unique_username("gerente"), "password": "Gerente12345", "role": "gerente"},
    )
    jefe_response = client.post(
        "/api/users",
        headers=auth_headers("jefe", "jefe_operarios"),
        json={"username": _unique_username("jefe"), "password": "Jefe12345", "role": "jefe_operarios"},
    )

    assert gerente_response.status_code == 403
    assert jefe_response.status_code == 403


def test_operario_cannot_create_or_list_users():
    create_response = client.post(
        "/api/users",
        headers=auth_headers("operario1", "operario"),
        json={"username": _unique_username(), "password": "Operario12345", "role": "operario"},
    )
    list_response = client.get("/api/users", headers=auth_headers("operario1", "operario"))

    assert create_response.status_code == 403
    assert list_response.status_code == 403


def test_gerente_can_list_users_and_jefe_lists_only_operarios():
    gerente_response = client.get("/api/users", headers=auth_headers("gerente", "gerente"))
    jefe_response = client.get("/api/users", headers=auth_headers("jefe", "jefe_operarios"))

    assert gerente_response.status_code == 200
    assert any(user["role"] == "gerente" for user in gerente_response.json())
    assert jefe_response.status_code == 200
    assert all(user["role"] == "operario" for user in jefe_response.json())
    assert all("password_hash" not in user for user in gerente_response.json())


def test_jefe_can_get_update_deactivate_and_reactivate_operario_with_logs():
    user = _create_operario()
    before_update = _count_logs("USER_UPDATED")
    before_deactivated = _count_logs("USER_DEACTIVATED")
    before_reactivated = _count_logs("USER_REACTIVATED")

    get_response = client.get(f"/api/users/{user['id']}", headers=auth_headers("jefe", "jefe_operarios"))
    update_response = client.patch(
        f"/api/users/{user['id']}",
        headers=auth_headers("jefe", "jefe_operarios"),
        json={"username": _unique_username("renombrado"), "password": "NuevaClave123"},
    )
    deactivate_response = client.delete(f"/api/users/{user['id']}", headers=auth_headers("jefe", "jefe_operarios"))
    reactivate_response = client.patch(
        f"/api/users/{user['id']}",
        headers=auth_headers("jefe", "jefe_operarios"),
        json={"is_active": True},
    )

    assert get_response.status_code == 200
    assert update_response.status_code == 200, update_response.json()
    assert update_response.json()["role"] == "operario"
    assert "password_hash" not in update_response.json()
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False
    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["is_active"] is True
    assert _count_logs("USER_UPDATED") == before_update + 1
    assert _count_logs("USER_DEACTIVATED") == before_deactivated + 1
    assert _count_logs("USER_REACTIVATED") == before_reactivated + 1


def test_inactive_user_cannot_login():
    password = "Operario12345"
    user = _create_operario(password=password)
    client.delete(f"/api/users/{user['id']}", headers=auth_headers("jefe", "jefe_operarios"))

    response = client.post("/api/auth/login", json={"username": user["username"], "password": password})

    assert response.status_code == 401


def test_jefe_cannot_manage_non_operario_users():
    gerente = client.get("/api/users", headers=auth_headers("gerente", "gerente")).json()[0]
    gerente_id = next(user["id"] for user in client.get("/api/users", headers=auth_headers("gerente", "gerente")).json() if user["role"] == "gerente")

    get_response = client.get(f"/api/users/{gerente_id}", headers=auth_headers("jefe", "jefe_operarios"))
    patch_response = client.patch(
        f"/api/users/{gerente_id}",
        headers=auth_headers("jefe", "jefe_operarios"),
        json={"username": gerente["username"]},
    )
    delete_response = client.delete(f"/api/users/{gerente_id}", headers=auth_headers("jefe", "jefe_operarios"))

    assert get_response.status_code == 403
    assert patch_response.status_code == 403
    assert delete_response.status_code == 403
