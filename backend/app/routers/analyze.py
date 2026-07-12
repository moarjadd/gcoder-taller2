from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.metrics import elapsed_ms, now_seconds
from app.core.mesh_loader import load_mesh_from_bytes
from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.routers._form import parse_model_transform
from app.schemas.responses import AnalyzeResponse
from app.services.analysis_service import analyze_mesh
from app.services.audit_log_service import create_audit_log, sanitize_filename


router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_stl(
    request: Request,
    file: UploadFile = File(...),
    transform: str | None = Form(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    operation_start = now_seconds()
    filename = file.filename or "modelo.stl"
    _, extension = sanitize_filename(filename)
    create_audit_log(
        db,
        action="FILE_UPLOADED",
        status="success",
        user=current_user,
        resource="analyze",
        file_name=filename,
        file_extension=extension,
        detail="Archivo recibido para analisis.",
        request=request,
    )

    try:
        load_start = now_seconds()
        contents = await file.read()
        mesh = load_mesh_from_bytes(contents, filename)
        mesh_load_ms = elapsed_ms(load_start)
        result = analyze_mesh(
            mesh,
            filename,
            len(contents),
            parse_model_transform(transform),
            mesh_load_ms=mesh_load_ms,
            started_at=operation_start,
        )
        create_audit_log(
            db,
            action="ANALYZE_SUCCESS",
            status="success",
            user=current_user,
            resource="analyze",
            file_name=filename,
            file_extension=extension,
            detail=f"Analisis completado. triangle_count={result['triangleCount']}",
            request=request,
        )
        return result
    except HTTPException as exc:
        create_audit_log(
            db,
            action="ANALYZE_FAILED",
            status="failed",
            user=current_user,
            resource="analyze",
            file_name=filename,
            file_extension=extension,
            detail=str(exc.detail),
            request=request,
        )
        raise
    except Exception as exc:
        create_audit_log(
            db,
            action="ANALYZE_FAILED",
            status="error",
            user=current_user,
            resource="analyze",
            file_name=filename,
            file_extension=extension,
            detail="Error inesperado durante el analisis.",
            request=request,
        )
        raise exc
