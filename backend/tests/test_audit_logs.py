import json

import trimesh
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from scripts.seed_users import main as seed_users
from tests.auth_helpers import auth_headers
from tests.stl_dataset import cube_mesh, stl_payload


client = TestClient(app)


def _count_logs(action: str) -> int:
    with SessionLocal() as db:
        return db.query(AuditLog).filter(AuditLog.action == action).count()


def _latest_logs(actions: set[str]) -> list[AuditLog]:
    with SessionLocal() as db:
        return (
            db.query(AuditLog)
            .filter(AuditLog.action.in_(actions))
            .order_by(AuditLog.created_at.desc())
            .limit(20)
            .all()
        )


def test_gerente_can_query_global_logs_and_operario_cannot():
    gerente_response = client.get("/api/logs", headers=auth_headers("gerente", "gerente"))
    operario_response = client.get("/api/logs", headers=auth_headers("operario1", "operario"))

    assert gerente_response.status_code == 200
    assert "items" in gerente_response.json()
    assert operario_response.status_code == 403


def test_jefe_operarios_cannot_create_gerente():
    response = client.post(
        "/api/users",
        headers=auth_headers("jefe", "jefe_operarios"),
        json={"username": "gerente2", "password": "Gerente12345", "role": "gerente"},
    )

    assert response.status_code == 403


def test_login_success_and_failure_generate_audit_logs_without_password_or_token():
    seed_users()
    before_success = _count_logs("LOGIN_SUCCESS")
    before_failed = _count_logs("LOGIN_FAILED")

    success_response = client.post(
        "/api/auth/login",
        json={"username": "gerente", "password": "Gerente12345"},
    )
    failed_response = client.post(
        "/api/auth/login",
        json={"username": "gerente", "password": "wrong-password"},
    )

    assert success_response.status_code == 200
    assert failed_response.status_code == 401
    assert _count_logs("LOGIN_SUCCESS") == before_success + 1
    assert _count_logs("LOGIN_FAILED") == before_failed + 1

    logs_response = client.get("/api/logs", headers=auth_headers("gerente", "gerente"))
    serialized = json.dumps(logs_response.json()).lower()
    assert "gerente12345" not in serialized
    assert "wrong-password" not in serialized
    assert "bearer " not in serialized
    assert success_response.json()["access_token"].lower() not in serialized


def test_analyze_with_token_generates_file_and_analysis_logs():
    before_upload = _count_logs("FILE_UPLOADED")
    before_success = _count_logs("ANALYZE_SUCCESS")

    response = client.post(
        "/api/analyze",
        headers=auth_headers("operario1", "operario"),
        files={"file": ("nested/path/cube.stl", stl_payload(cube_mesh()), "model/stl")},
    )

    assert response.status_code == 200, response.json()
    assert _count_logs("FILE_UPLOADED") == before_upload + 1
    assert _count_logs("ANALYZE_SUCCESS") == before_success + 1

    recent_logs = _latest_logs({"FILE_UPLOADED", "ANALYZE_SUCCESS"})
    assert any(log.file_extension == "stl" for log in recent_logs)
    assert all("/" not in (log.file_name or "") and "\\" not in (log.file_name or "") for log in recent_logs)


def test_convert_with_token_generates_conversion_and_parameter_logs():
    before_started = _count_logs("GCODE_GENERATION_STARTED")
    before_params = _count_logs("PARAMETERS_USED")
    before_success = _count_logs("CONVERT_SUCCESS")

    response = client.post(
        "/api/convert",
        headers=auth_headers("operario1", "operario"),
        files={"file": ("cube.stl", stl_payload(trimesh.creation.box(extents=(10, 10, 4))), "model/stl")},
        data={"params": json.dumps({"step_down_mm": 1.0, "feed_rate_mm_min": 700, "spindle_rpm": 11000})},
    )

    assert response.status_code == 200, response.json()
    assert _count_logs("GCODE_GENERATION_STARTED") == before_started + 1
    assert _count_logs("PARAMETERS_USED") == before_params + 1
    assert _count_logs("CONVERT_SUCCESS") == before_success + 1

    parameter_logs = _latest_logs({"PARAMETERS_USED"})
    assert any("step_down_mm=1.0" in (log.detail or "") for log in parameter_logs)
    assert any("feed_rate_mm_min=700.0" in (log.detail or "") for log in parameter_logs)


def test_logs_me_returns_only_current_user_logs():
    headers = auth_headers("operario1", "operario")
    response = client.get("/api/logs/me", headers=headers)
    body = response.json()

    assert response.status_code == 200, body
    assert all(item["username_snapshot"] == "operario1" for item in body["items"])
