"""Server-side validation for locally staged 3D model files."""

from __future__ import annotations

import json
import struct
from typing import Any

from pydantic import BaseModel, Field


MAX_LOCAL_MODEL_FILE_BYTES = 60 * 1024 * 1024
LARGE_MODEL_WARNING_BYTES = 20 * 1024 * 1024

SUPPORTED_MODEL_FORMATS = ("obj", "stl", "gltf", "glb")
FORMAT_LABELS = {
    "obj": "OBJ",
    "stl": "STL",
    "gltf": "glTF",
    "glb": "GLB",
}


class ModelValidationResult(BaseModel):
    """Describe whether one local model file is safe to stage in the current browser flow."""

    filename: str
    file_format: str
    format_label: str
    file_size_bytes: int
    can_stage_locally: bool
    summary: str
    resource_mode: str
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


def _normalized_model_format(filename: str) -> str:
    token = str(filename).strip().lower()
    if not token:
        raise ValueError("A local model file name is required for validation.")
    dot_index = token.rfind(".")
    if dot_index < 0:
        raise ValueError("The local model file must have an extension.")
    extension = token[dot_index + 1 :]
    if extension not in SUPPORTED_MODEL_FORMATS:
        raise ValueError(
            f"Unsupported 3D model format. Expected one of: {', '.join('.' + item for item in SUPPORTED_MODEL_FORMATS)}.",
        )
    return extension


def _large_file_warnings(file_size_bytes: int) -> list[str]:
    warnings: list[str] = []
    if file_size_bytes > LARGE_MODEL_WARNING_BYTES:
        warnings.append(
            "Large model file detected. Browser-side parsing and scene normalization may feel slow on lower-end hardware.",
        )
    return warnings


def _validate_obj(filename: str, file_bytes: bytes) -> ModelValidationResult:
    text = file_bytes.decode("utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    vertex_count = sum(1 for line in lines if line.startswith("v "))
    face_count = sum(1 for line in lines if line.startswith("f "))
    material_refs = [line.split(maxsplit=1)[1].strip() for line in lines if line.startswith("mtllib ")]

    blockers: list[str] = []
    warnings = _large_file_warnings(len(file_bytes))
    if vertex_count == 0:
        blockers.append("OBJ file does not declare any vertex positions.")
    if face_count == 0:
        blockers.append("OBJ file does not declare any polygon faces, so there is no staged surface to explore.")
    if material_refs:
        warnings.append(
            "OBJ references external material libraries. Geometry can still be staged, but external shading data is ignored in the current browser workflow.",
        )
    if vertex_count > 250_000:
        warnings.append("High vertex count detected. Interaction may become sluggish in browser-based staging.")
    if face_count > 250_000:
        warnings.append("High face count detected. Consider preprocessing the model before staging it in FeelIT.")

    can_stage = not blockers
    summary = (
        "OBJ validation passed for direct browser staging."
        if can_stage
        else "OBJ validation failed. Resolve the blocking geometry issues before staging this file."
    )
    return ModelValidationResult(
        filename=filename,
        file_format="obj",
        format_label=FORMAT_LABELS["obj"],
        file_size_bytes=len(file_bytes),
        can_stage_locally=can_stage,
        summary=summary,
        resource_mode="single-file-geometry",
        warnings=warnings,
        blockers=blockers,
        metrics={
            "vertex_count": vertex_count,
            "face_count": face_count,
            "material_library_count": len(material_refs),
        },
    )


def _looks_like_binary_stl(file_bytes: bytes) -> bool:
    if len(file_bytes) < 84:
        return False
    triangle_count = struct.unpack_from("<I", file_bytes, 80)[0]
    expected_binary_size = 84 + triangle_count * 50
    if expected_binary_size == len(file_bytes):
        return True
    header_prefix = file_bytes[:80].lower().strip()
    return not header_prefix.startswith(b"solid")


def _validate_stl(filename: str, file_bytes: bytes) -> ModelValidationResult:
    blockers: list[str] = []
    warnings = _large_file_warnings(len(file_bytes))
    metrics: dict[str, Any] = {}

    if _looks_like_binary_stl(file_bytes):
        triangle_count = struct.unpack_from("<I", file_bytes, 80)[0] if len(file_bytes) >= 84 else 0
        metrics["encoding"] = "binary"
        metrics["triangle_count"] = triangle_count
        if triangle_count == 0:
            blockers.append("Binary STL does not contain any triangles.")
    else:
        text = file_bytes.decode("utf-8", errors="ignore")
        triangle_count = text.lower().count("facet normal")
        metrics["encoding"] = "ascii"
        metrics["triangle_count"] = triangle_count
        if triangle_count == 0:
            blockers.append("ASCII STL does not contain any facet definitions.")

    if triangle_count > 400_000:
        warnings.append("High STL triangle count detected. Consider preprocessing or decimating the asset before staging.")

    can_stage = not blockers
    summary = (
        "STL validation passed for direct browser staging."
        if can_stage
        else "STL validation failed. Resolve the blocking mesh issues before staging this file."
    )
    return ModelValidationResult(
        filename=filename,
        file_format="stl",
        format_label=FORMAT_LABELS["stl"],
        file_size_bytes=len(file_bytes),
        can_stage_locally=can_stage,
        summary=summary,
        resource_mode="single-file-mesh",
        warnings=warnings,
        blockers=blockers,
        metrics=metrics,
    )


def _external_resource_uris(payload: dict[str, Any]) -> list[str]:
    uris: list[str] = []
    for key in ("buffers", "images"):
        for item in payload.get(key, []):
            uri = str(item.get("uri", "")).strip()
            if not uri:
                continue
            if uri.startswith("data:"):
                continue
            uris.append(uri)
    return uris


def _validate_gltf_payload(filename: str, file_bytes: bytes, *, format_name: str) -> ModelValidationResult:
    blockers: list[str] = []
    warnings = _large_file_warnings(len(file_bytes))
    try:
        payload = json.loads(file_bytes.decode("utf-8-sig"))
    except json.JSONDecodeError as error:
        blockers.append(f"glTF JSON could not be parsed: {error.msg}.")
        payload = {}

    mesh_count = len(payload.get("meshes", []))
    node_count = len(payload.get("nodes", []))
    scene_count = len(payload.get("scenes", []))
    external_uris = _external_resource_uris(payload)
    asset_version = str(payload.get("asset", {}).get("version", "")).strip()

    if mesh_count == 0:
        blockers.append("glTF payload does not declare any meshes.")
    if external_uris:
        blockers.append(
            "Current local browser staging only supports self-contained glTF assets. External buffer or image references were detected.",
        )
    if asset_version and asset_version != "2.0":
        warnings.append(f"glTF asset version '{asset_version}' was detected. FeelIT is validated primarily against glTF 2.0.")

    can_stage = not blockers
    summary = (
        "glTF validation passed for direct browser staging."
        if can_stage
        else "glTF validation failed. Use a self-contained asset with at least one mesh."
    )
    return ModelValidationResult(
        filename=filename,
        file_format=format_name,
        format_label=FORMAT_LABELS[format_name],
        file_size_bytes=len(file_bytes),
        can_stage_locally=can_stage,
        summary=summary,
        resource_mode="self-contained" if not external_uris else "external-resources-detected",
        warnings=warnings,
        blockers=blockers,
        metrics={
            "mesh_count": mesh_count,
            "node_count": node_count,
            "scene_count": scene_count,
            "external_resource_count": len(external_uris),
        },
    )


def _validate_glb(filename: str, file_bytes: bytes) -> ModelValidationResult:
    blockers: list[str] = []
    warnings = _large_file_warnings(len(file_bytes))

    if len(file_bytes) < 20:
        blockers.append("GLB file is too small to contain a valid header and JSON chunk.")
        return ModelValidationResult(
            filename=filename,
            file_format="glb",
            format_label=FORMAT_LABELS["glb"],
            file_size_bytes=len(file_bytes),
            can_stage_locally=False,
            summary="GLB validation failed. The file is too small to be a valid binary glTF container.",
            resource_mode="invalid-container",
            warnings=warnings,
            blockers=blockers,
            metrics={},
        )

    magic, version, declared_length = struct.unpack_from("<4sII", file_bytes, 0)
    if magic != b"glTF":
        blockers.append("GLB header magic is invalid.")
    if version != 2:
        warnings.append(f"GLB version {version} was detected. FeelIT is validated primarily against glTF 2.0.")
    if declared_length != len(file_bytes):
        blockers.append("GLB declared length does not match the actual file size.")

    json_payload: dict[str, Any] = {}
    if not blockers:
        json_chunk_length, json_chunk_type = struct.unpack_from("<I4s", file_bytes, 12)
        if json_chunk_type != b"JSON":
            blockers.append("GLB is missing the leading JSON chunk.")
        else:
            json_chunk_start = 20
            json_chunk_end = json_chunk_start + json_chunk_length
            try:
                json_payload = json.loads(file_bytes[json_chunk_start:json_chunk_end].decode("utf-8"))
            except json.JSONDecodeError as error:
                blockers.append(f"GLB JSON chunk could not be parsed: {error.msg}.")

    mesh_count = len(json_payload.get("meshes", []))
    node_count = len(json_payload.get("nodes", []))
    scene_count = len(json_payload.get("scenes", []))
    external_uris = _external_resource_uris(json_payload)
    if not blockers and mesh_count == 0:
        blockers.append("GLB payload does not declare any meshes.")
    if external_uris:
        blockers.append(
            "Current local browser staging only supports self-contained GLB assets. External buffer or image references were detected.",
        )

    can_stage = not blockers
    summary = (
        "GLB validation passed for direct browser staging."
        if can_stage
        else "GLB validation failed. Use a valid self-contained binary glTF asset with at least one mesh."
    )
    return ModelValidationResult(
        filename=filename,
        file_format="glb",
        format_label=FORMAT_LABELS["glb"],
        file_size_bytes=len(file_bytes),
        can_stage_locally=can_stage,
        summary=summary,
        resource_mode="self-contained" if not external_uris else "external-resources-detected",
        warnings=warnings,
        blockers=blockers,
        metrics={
            "mesh_count": mesh_count,
            "node_count": node_count,
            "scene_count": scene_count,
            "external_resource_count": len(external_uris),
            "glb_version": version,
        },
    )


def validate_local_model_file(filename: str, file_bytes: bytes) -> ModelValidationResult:
    """Validate one locally staged model before the browser attempts to parse it."""
    file_format = _normalized_model_format(filename)
    file_size_bytes = len(file_bytes)

    if file_size_bytes > MAX_LOCAL_MODEL_FILE_BYTES:
        return ModelValidationResult(
            filename=filename,
            file_format=file_format,
            format_label=FORMAT_LABELS[file_format],
            file_size_bytes=file_size_bytes,
            can_stage_locally=False,
            summary="The selected file exceeds the current direct-staging size limit for the browser workflow.",
            resource_mode="oversized",
            warnings=[],
            blockers=[
                f"Model file is larger than {MAX_LOCAL_MODEL_FILE_BYTES // (1024 * 1024)} MB. Use preprocessing before staging it in-browser.",
            ],
            metrics={},
        )

    if file_format == "obj":
        return _validate_obj(filename, file_bytes)
    if file_format == "stl":
        return _validate_stl(filename, file_bytes)
    if file_format == "gltf":
        return _validate_gltf_payload(filename, file_bytes, format_name="gltf")
    if file_format == "glb":
        return _validate_glb(filename, file_bytes)
    raise ValueError(f"Unsupported 3D model format: {file_format}")
