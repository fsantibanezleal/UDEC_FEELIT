"""REST API routes for the initial FeelIT bootstrap."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.braille import layout_braille_cells, translate_text_to_cells
from app.core.config import APP_NAME, APP_PORT, APP_VERSION
from app.core.demo_assets import build_demo_model_catalog
from app.core.haptic_materials import build_material_catalog
from app.core.haptic_workspace import (
    DEFAULT_FILE_BROWSER_PAGE_SIZE,
    build_haptic_workspace_payload,
    build_invalid_workspace_repair_preview,
    build_workspace_browser_payload,
    build_workspace_descriptor_preview,
    build_workspace_manager_payload,
    build_workspace_text_payload,
    create_workspace_file,
    raw_workspace_file_path,
    register_workspace_file,
    repair_workspace_file,
    rescan_workspace_file,
    unregister_workspace_file,
    update_workspace_file,
)
from app.core.library_assets import (
    build_audio_catalog,
    build_document_catalog,
    build_document_payload,
)
from app.core.model_validation import validate_local_model_bundle, validate_local_model_file
from app.core.modes import build_mode_catalog

router = APIRouter(prefix="/api")


class BraillePreviewRequest(BaseModel):
    """Payload for the Braille preview endpoint."""

    text: str = Field(..., min_length=1, max_length=4000)
    columns: int = Field(default=12, ge=1, le=40)


class RegisterHapticWorkspaceRequest(BaseModel):
    """Payload for registering an existing workspace descriptor file."""

    workspace_file_path: str = Field(..., min_length=1, max_length=2048)


class CreateHapticWorkspaceRequest(BaseModel):
    """Payload for creating a new workspace descriptor file."""

    title: str = Field(..., min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    description: str = Field(default="", max_length=500)
    root_path: str = Field(..., min_length=1, max_length=2048)
    auto_populate: bool = True


class UpdateHapticWorkspaceRequest(BaseModel):
    """Payload for editing one existing registered workspace descriptor."""

    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    content_root_path: str = Field(..., min_length=1, max_length=2048)
    file_browser_root_path: str = Field(..., min_length=1, max_length=2048)
    refresh_libraries: bool = False


class HapticConfigurationRequest(BaseModel):
    """Payload for haptic runtime backend selection and dependency overrides."""

    requested_backend: str = Field(..., min_length=1, max_length=120)
    sdk_roots: dict[str, str] = Field(default_factory=dict)
    bridge_paths: dict[str, str] = Field(default_factory=dict)
    device_selectors: dict[str, str] = Field(default_factory=dict)


@router.get("/health")
async def health(request: Request) -> dict:
    """Return application health and runtime metadata."""
    backend = request.app.state.haptic_backend
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "public_port": APP_PORT,
        "haptics": backend.status().model_dump(),
    }


@router.get("/meta")
async def meta() -> dict:
    """Return public application metadata."""
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "public_port": APP_PORT,
        "modes": build_mode_catalog(),
    }


@router.get("/modes")
async def modes() -> dict:
    """Return the current application mode catalog."""
    return {"modes": build_mode_catalog()}


@router.get("/materials")
async def materials() -> dict:
    """Return the current haptic material profile catalog."""
    return {"materials": build_material_catalog()}


@router.get("/demo-models")
async def demo_models() -> dict:
    """Return bundled multi-format demo assets for the 3D explorer."""
    return {"models": build_demo_model_catalog()}


@router.post("/models/validate-local-upload")
async def validate_local_model_upload(file: UploadFile = File(...)) -> dict:
    """Validate one local model file before browser-side staging."""
    try:
        payload = await file.read()
        filename = file.filename or "uploaded-model"
        return validate_local_model_file(filename, payload).model_dump()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/models/validate-local-bundle")
async def validate_local_model_bundle_upload(
    main_filename: str = Form(...),
    files: list[UploadFile] = File(...),
) -> dict:
    """Validate one local model bundle before browser-side staging."""
    try:
        bundle_payload: dict[str, bytes] = {}
        for upload in files:
            filename = upload.filename or ""
            if not filename:
                continue
            bundle_payload[filename] = await upload.read()
        return validate_local_model_bundle(main_filename, bundle_payload).model_dump()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/library/documents")
async def library_documents() -> dict:
    """Return the bundled document library catalog."""
    return {
        "documents": build_document_catalog(),
        "supported_formats": ["txt", "html", "epub"],
    }


@router.get("/library/documents/{slug}")
async def library_document(
    slug: str,
    offset: int = Query(default=0, ge=0),
    max_chars: int = Query(default=1200, ge=250, le=4000),
) -> dict:
    """Return a clipped bundled document segment for the Braille Reader."""
    try:
        return build_document_payload(slug, offset=offset, max_chars=max_chars)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown document slug: {slug}") from error


@router.get("/library/audio")
async def library_audio() -> dict:
    """Return the bundled audio library catalog."""
    return {"audio": build_audio_catalog()}


@router.get("/haptic-workspaces")
async def haptic_workspaces() -> dict:
    """Return the catalog of known Haptic Desktop workspaces."""
    return build_workspace_manager_payload()


@router.get("/haptic-workspaces/{slug}")
async def haptic_workspace_detail(slug: str) -> dict:
    """Return a resolved Haptic Desktop workspace payload."""
    try:
        return build_haptic_workspace_payload(slug)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown workspace slug: {slug}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/haptic-workspaces/{slug}/browse")
async def haptic_workspace_browse(
    slug: str,
    path: str = Query(default="", max_length=2048),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=DEFAULT_FILE_BROWSER_PAGE_SIZE, ge=1, le=24),
) -> dict:
    """Browse the configured file-browser root for one workspace."""
    try:
        return build_workspace_browser_payload(slug, path, page=page, page_size=page_size)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown workspace slug: {slug}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/haptic-workspaces/{slug}/text-file")
async def haptic_workspace_text_file(
    slug: str,
    path: str = Query(..., min_length=1, max_length=2048),
    offset: int = Query(default=0, ge=0),
    max_chars: int = Query(default=1200, ge=250, le=4000),
) -> dict:
    """Return a segmented text payload for one raw workspace file."""
    try:
        return build_workspace_text_payload(slug, path, offset=offset, max_chars=max_chars)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown workspace slug: {slug}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/haptic-workspaces/{slug}/raw-file")
async def haptic_workspace_raw_file(
    slug: str,
    path: str = Query(..., min_length=1, max_length=2048),
) -> FileResponse:
    """Stream a raw workspace file under the safe configured root."""
    try:
        file_path = raw_workspace_file_path(slug, path)
        return FileResponse(file_path)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown workspace slug: {slug}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/haptic-workspaces/register")
async def haptic_workspace_register(payload: RegisterHapticWorkspaceRequest) -> dict:
    """Register an existing user workspace descriptor."""
    try:
        record = register_workspace_file(payload.workspace_file_path)
        return {
            "registered": True,
            "workspace": {
                "slug": record["slug"],
                "title": record["title"],
                "workspace_file_label": record["workspace_file_label"],
            },
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/haptic-workspaces/create")
async def haptic_workspace_create(payload: CreateHapticWorkspaceRequest) -> dict:
    """Create and register a new user workspace descriptor."""
    try:
        record = create_workspace_file(
            title=payload.title,
            slug=payload.slug,
            description=payload.description,
            root_path=payload.root_path,
            auto_populate=payload.auto_populate,
        )
        return {
            "created": True,
            "workspace": {
                "slug": record["slug"],
                "title": record["title"],
                "workspace_file_label": record["workspace_file_label"],
            },
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/haptic-workspaces/{slug}/descriptor")
async def haptic_workspace_descriptor_preview(slug: str) -> dict:
    """Return one preview payload for the selected workspace descriptor."""
    try:
        return build_workspace_descriptor_preview(slug)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown workspace slug: {slug}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/haptic-workspaces/{slug}/descriptor")
async def haptic_workspace_update_descriptor(
    slug: str,
    payload: UpdateHapticWorkspaceRequest,
) -> dict:
    """Apply one safe structured descriptor update for a registered workspace."""
    try:
        record = update_workspace_file(
            slug,
            title=payload.title,
            description=payload.description,
            content_root_path=payload.content_root_path,
            file_browser_root_path=payload.file_browser_root_path,
            refresh_libraries=payload.refresh_libraries,
        )
        return {
            "updated": True,
            "workspace": {
                "slug": record["slug"],
                "title": record["title"],
                "registry_key": record["registry_key"],
                "workspace_file_label": record["workspace_file_label"],
            },
        }
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown workspace slug: {slug}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/haptic-workspaces/{slug}/rescan")
async def haptic_workspace_rescan(slug: str) -> dict:
    """Rebuild one registered workspace descriptor library catalog from disk."""
    try:
        record = rescan_workspace_file(slug)
        return {
            "rescanned": True,
            "workspace": {
                "slug": record["slug"],
                "title": record["title"],
                "registry_key": record["registry_key"],
                "workspace_file_label": record["workspace_file_label"],
            },
        }
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown workspace slug: {slug}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete("/haptic-workspaces/{registry_key}")
async def haptic_workspace_unregister(registry_key: str) -> dict:
    """Remove one registered workspace descriptor reference from the local registry."""
    try:
        removed = unregister_workspace_file(registry_key)
        return {"unregistered": True, "workspace": removed}
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Unknown workspace registry entry.") from error


@router.post("/haptic-workspaces/invalid/{registry_key}/repair")
async def haptic_workspace_repair(registry_key: str) -> dict:
    """Repair one invalid registered workspace descriptor when it can be normalized safely."""
    try:
        record = repair_workspace_file(registry_key)
        return {
            "repaired": True,
            "workspace": {
                "slug": record["slug"],
                "title": record["title"],
                "registry_key": record["registry_key"],
                "workspace_file_label": record["workspace_file_label"],
            },
        }
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Unknown workspace registry entry.") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/haptic-workspaces/invalid/{registry_key}/preview")
async def haptic_workspace_invalid_preview(registry_key: str) -> dict:
    """Return one preview payload for a potential invalid-descriptor repair."""
    try:
        return build_invalid_workspace_repair_preview(registry_key)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Unknown workspace registry entry.") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/device/status")
async def device_status(request: Request) -> dict:
    """Return the current haptic backend state."""
    backend = request.app.state.haptic_backend
    return backend.status().model_dump()


@router.get("/haptics/configuration")
async def haptic_configuration(request: Request) -> dict:
    """Return the current haptic runtime configuration snapshot."""
    return request.app.state.haptic_runtime.configuration_snapshot().model_dump()


@router.post("/haptics/configuration")
async def update_haptic_configuration(
    payload: HapticConfigurationRequest,
    request: Request,
) -> dict:
    """Persist new haptic runtime preferences and return the refreshed snapshot."""
    try:
        snapshot = request.app.state.haptic_runtime.update_configuration(
            requested_backend=payload.requested_backend,
            sdk_roots=payload.sdk_roots,
            bridge_paths=payload.bridge_paths,
            device_selectors=payload.device_selectors,
        )
        request.app.state.haptic_backend = request.app.state.haptic_runtime.backend
        return snapshot.model_dump()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/braille/preview")
async def braille_preview(payload: BraillePreviewRequest) -> dict:
    """Translate plain text into a preview-ready Braille scene payload."""
    cells = translate_text_to_cells(payload.text)
    positioned = layout_braille_cells(cells, columns=payload.columns)
    return {
        "text": payload.text,
        "columns": payload.columns,
        "cell_count": len(cells),
        "cells": [cell.model_dump() for cell in positioned],
    }
