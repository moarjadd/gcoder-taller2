import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.metrics import elapsed_ms, now_seconds
from app.core.mesh_loader import load_mesh_from_upload
from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.routers._form import parse_model_transform
from app.schemas.machining import MachiningParams
from app.schemas.responses import ConvertResponse
from app.services.audit_log_service import create_audit_log, params_detail, sanitize_filename
from app.services.conversion_service import convert_mesh


router = APIRouter(tags=["convert"])


@router.post("/convert", response_model=ConvertResponse)
async def convert_stl(
    request: Request,
    file: UploadFile = File(...),
    params: str | None = Form(default=None),
    transform: str | None = Form(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    operation_start = now_seconds()
    filename = file.filename or "modelo.stl"
    _, extension = sanitize_filename(filename)

    try:
        machining_params = MachiningParams.model_validate(json.loads(params) if params else {})
    except json.JSONDecodeError as exc:
        create_audit_log(
            db,
            action="CONVERT_FAILED",
            status="failed",
            user=current_user,
            resource="convert",
            file_name=filename,
            file_extension=extension,
            detail="El campo params debe ser JSON valido.",
            request=request,
        )
        raise HTTPException(status_code=400, detail="El campo params debe ser JSON vÃ¡lido.") from exc
    except ValidationError as exc:
        detail = "; ".join(error["msg"] for error in exc.errors())
        create_audit_log(
            db,
            action="CONVERT_FAILED",
            status="failed",
            user=current_user,
            resource="convert",
            file_name=filename,
            file_extension=extension,
            detail=f"Parametros invalidos: {detail}",
            request=request,
        )
        raise HTTPException(status_code=422, detail=f"ParÃ¡metros de mecanizado invÃ¡lidos: {detail}") from exc

    create_audit_log(
        db,
        action="GCODE_GENERATION_STARTED",
        status="success",
        user=current_user,
        resource="convert",
        file_name=filename,
        file_extension=extension,
        detail="Generacion de G-code iniciada.",
        request=request,
    )
    create_audit_log(
        db,
        action="PARAMETERS_USED",
        status="success",
        user=current_user,
        resource="convert",
        file_name=filename,
        file_extension=extension,
        detail=params_detail(machining_params),
        request=request,
    )

    try:
        load_start = now_seconds()
        mesh = await load_mesh_from_upload(file)
        mesh_load_ms = elapsed_ms(load_start)
        result = convert_mesh(
            mesh,
            filename,
            machining_params,
            parse_model_transform(transform),
            mesh_load_ms=mesh_load_ms,
            started_at=operation_start,
        )
        create_audit_log(
            db,
            action="CONVERT_SUCCESS",
            status="success",
            user=current_user,
            resource="convert",
            file_name=filename,
            file_extension=extension,
            detail=f"G-code generado. lines_count={result['linesCount']}",
            request=request,
        )
        create_audit_log(
            db,
            action="GCODE_EXPORTED",
            status="success",
            user=current_user,
            resource="convert",
            file_name=filename,
            file_extension=extension,
            detail="G-code disponible en la respuesta de conversion.",
            request=request,
        )
        return result
    except HTTPException as exc:
        create_audit_log(
            db,
            action="CONVERT_FAILED",
            status="failed",
            user=current_user,
            resource="convert",
            file_name=filename,
            file_extension=extension,
            detail=str(exc.detail),
            request=request,
        )
        raise
    except Exception as exc:
        create_audit_log(
            db,
            action="CONVERT_FAILED",
            status="error",
            user=current_user,
            resource="convert",
            file_name=filename,
            file_extension=extension,
            detail="Error inesperado durante la conversion.",
            request=request,
        )
        raise exc
