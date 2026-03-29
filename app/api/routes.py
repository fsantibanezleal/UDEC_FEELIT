"""REST API routes for the initial FeelIT bootstrap."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.braille import layout_braille_cells, translate_text_to_cells
from app.core.config import APP_NAME, APP_PORT, APP_VERSION
from app.core.demo_assets import build_demo_model_catalog
from app.core.haptic_materials import build_material_catalog
from app.core.library_assets import (
    build_audio_catalog,
    build_document_catalog,
    build_document_payload,
)
from app.core.modes import build_mode_catalog

router = APIRouter(prefix="/api")


class BraillePreviewRequest(BaseModel):
    """Payload for the Braille preview endpoint."""

    text: str = Field(..., min_length=1, max_length=4000)
    columns: int = Field(default=12, ge=1, le=40)


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
    """Return bundled real OBJ demo assets for the 3D explorer."""
    return {"models": build_demo_model_catalog()}


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


@router.get("/device/status")
async def device_status(request: Request) -> dict:
    """Return the current haptic backend state."""
    backend = request.app.state.haptic_backend
    return backend.status().model_dump()


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
