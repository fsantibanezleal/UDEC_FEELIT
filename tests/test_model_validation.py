"""Tests for server-side local 3D model validation."""

from __future__ import annotations

import json

from app.core.model_validation import MAX_LOCAL_MODEL_FILE_BYTES, validate_local_model_file


def test_validate_obj_accepts_simple_geometry() -> None:
    result = validate_local_model_file(
        "triangle.obj",
        b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
    )
    assert result.can_stage_locally is True
    assert result.file_format == "obj"
    assert result.metrics["vertex_count"] == 3
    assert result.metrics["face_count"] == 1


def test_validate_obj_without_faces_is_blocked() -> None:
    result = validate_local_model_file(
        "points.obj",
        b"v 0 0 0\nv 1 0 0\nv 0 1 0\n",
    )
    assert result.can_stage_locally is False
    assert any("polygon faces" in blocker for blocker in result.blockers)


def test_validate_ascii_stl_without_facets_is_blocked() -> None:
    result = validate_local_model_file(
        "empty.stl",
        b"solid empty\nendsolid empty\n",
    )
    assert result.can_stage_locally is False
    assert result.metrics["triangle_count"] == 0


def test_validate_gltf_with_external_resources_is_blocked() -> None:
    payload = {
        "asset": {"version": "2.0"},
        "buffers": [{"uri": "mesh.bin", "byteLength": 12}],
        "meshes": [{"primitives": [{}]}],
    }
    result = validate_local_model_file("external.gltf", json.dumps(payload).encode("utf-8"))
    assert result.can_stage_locally is False
    assert result.metrics["external_resource_count"] == 1


def test_validate_glb_with_invalid_header_is_blocked() -> None:
    result = validate_local_model_file("broken.glb", b"not-a-valid-glb")
    assert result.can_stage_locally is False
    assert any("too small" in blocker.lower() or "magic" in blocker.lower() for blocker in result.blockers)


def test_validate_oversized_model_is_blocked() -> None:
    payload = b"x" * (MAX_LOCAL_MODEL_FILE_BYTES + 1)
    result = validate_local_model_file("heavy.obj", payload)
    assert result.can_stage_locally is False
    assert result.resource_mode == "oversized"
