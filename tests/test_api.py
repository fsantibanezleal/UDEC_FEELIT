"""Tests for FeelIT API endpoints."""

import json

from fastapi.testclient import TestClient

from app.core.version import APP_VERSION
from app.main import app


def test_health_endpoint_reports_port_and_backend() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["public_port"] == 8101
    assert payload["haptics"]["backend"] == "visual-emulator"


def test_modes_endpoint_exposes_four_modes() -> None:
    with TestClient(app) as client:
        response = client.get("/api/modes")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["modes"]) == 5


def test_meta_endpoint_reports_version_and_routes() -> None:
    with TestClient(app) as client:
        response = client.get("/api/meta")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == APP_VERSION
    assert {mode["route"] for mode in payload["modes"]} == {
        "/object-explorer",
        "/braille-reader",
        "/haptic-desktop",
        "/haptic-workspace-manager",
        "/haptic-configuration",
    }


def test_root_redirects_to_braille_reader() -> None:
    with TestClient(app) as client:
        response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/braille-reader"


def test_frontend_mode_routes_are_served() -> None:
    with TestClient(app) as client:
        object_response = client.get("/object-explorer")
        braille_response = client.get("/braille-reader")
        desktop_response = client.get("/haptic-desktop")
        manager_response = client.get("/haptic-workspace-manager")
        configuration_response = client.get("/haptic-configuration")
    assert object_response.status_code == 200
    assert "3D Object Explorer" in object_response.text
    assert "Space activate" in object_response.text
    assert "Scene-native launcher plus bounded exploration world" in object_response.text
    assert "Scene mode" in object_response.text
    assert "Local Upload Validation" in object_response.text
    assert "Main model file" in object_response.text
    assert "Clear Local Bundle" in object_response.text
    assert 'type="module" src="/static/js/object_explorer.js"' in object_response.text
    assert '/static/js/app.js" defer' not in object_response.text
    assert braille_response.status_code == 200
    assert "Braille Reader" in braille_response.text
    assert "3D tactile library launcher plus reading world" in braille_response.text
    assert "Load Document" in braille_response.text
    assert "Previous Segment" in braille_response.text
    assert "Companion audio" in braille_response.text
    assert "Library launcher" in braille_response.text
    assert "WASD/QE pointer" in braille_response.text
    assert 'type="module" src="/static/js/braille_reader.js"' in braille_response.text
    assert '/static/js/app.js" defer' not in braille_response.text
    assert desktop_response.status_code == 200
    assert "Haptic Desktop" in desktop_response.text
    assert "Load Workspace" in desktop_response.text
    assert "Virtual Desktop Workspace" in desktop_response.text
    assert "Space activate" in desktop_response.text
    assert 'type="module" src="/static/js/haptic_desktop.js"' in desktop_response.text
    assert '/static/js/app.js" defer' not in desktop_response.text
    assert manager_response.status_code == 200
    assert "Haptic Workspace Manager" in manager_response.text
    assert "Create Workspace" in manager_response.text
    assert 'type="module" src="/static/js/haptic_workspace_manager.js"' in manager_response.text
    assert configuration_response.status_code == 200
    assert "Haptic Configuration" in configuration_response.text
    assert "Runtime Selection" in configuration_response.text
    assert "Scene Primitive Families" in configuration_response.text
    assert "Backend Contract Readiness" in configuration_response.text
    assert "Contact Pilot Rollout" in configuration_response.text
    assert "Pilot Command Contract" in configuration_response.text
    assert 'type="module" src="/static/js/haptic_configuration.js"' in configuration_response.text


def test_three_vendor_runtime_assets_are_served() -> None:
    with TestClient(app) as client:
        module_response = client.get("/static/vendor/three/three.module.js")
        core_response = client.get("/static/vendor/three/three.core.js")
    assert module_response.status_code == 200
    assert core_response.status_code == 200
    assert "from './three.core.js'" in module_response.text
    assert "class Quaternion" in core_response.text


def test_material_catalog_endpoint_exposes_realistic_profiles() -> None:
    with TestClient(app) as client:
        response = client.get("/api/materials")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["materials"]) >= 5
    assert any(material["slug"] == "polished_metal" for material in payload["materials"])


def test_demo_model_endpoint_exposes_multi_format_assets() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo-models")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["models"]) >= 13
    formats = {model["file_format"] for model in payload["models"]}
    assert {"obj", "stl", "gltf", "glb"} <= formats
    assert all(model["file_url"].endswith(f".{model['file_format']}") for model in payload["models"])
    assert all(model["format_label"] for model in payload["models"])


def test_demo_model_static_assets_are_served() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo-models")
        assert response.status_code == 200
        models = response.json()["models"]
        for model in models:
            asset_response = client.get(model["file_url"])
            assert asset_response.status_code == 200
            if model["file_format"] == "obj":
                assert "v " in asset_response.text
            elif model["file_format"] == "stl":
                assert asset_response.text.startswith("solid ")
            elif model["file_format"] == "gltf":
                assert '"asset"' in asset_response.text
            elif model["file_format"] == "glb":
                assert asset_response.content[:4] == b"glTF"


def test_local_model_validation_endpoint_accepts_simple_obj_upload() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/models/validate-local-upload",
            files={"file": ("sample.obj", b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n", "text/plain")},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["can_stage_locally"] is True
    assert payload["file_format"] == "obj"
    assert payload["metrics"]["vertex_count"] == 3
    assert payload["metrics"]["face_count"] == 1
    assert payload["staging_profile"]["bounds_available"] is True
    assert payload["staging_profile"]["recommended_workspace_scale_percent"] == 120


def test_local_model_validation_endpoint_blocks_external_resource_gltf() -> None:
    gltf_payload = (
        b'{"asset":{"version":"2.0"},"buffers":[{"uri":"mesh.bin","byteLength":12}],"meshes":[{"primitives":[{}]}]}'
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/models/validate-local-upload",
            files={"file": ("sample.gltf", gltf_payload, "model/gltf+json")},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["can_stage_locally"] is False
    assert payload["file_format"] == "gltf"
    assert any("External buffer or image references" in blocker for blocker in payload["blockers"])


def test_local_model_validation_endpoint_rejects_unsupported_format() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/models/validate-local-upload",
            files={"file": ("sample.fbx", b"placeholder", "application/octet-stream")},
        )
    assert response.status_code == 400
    assert "Unsupported 3D model format" in response.json()["detail"]


def test_local_model_bundle_validation_endpoint_accepts_gltf_with_sidecars() -> None:
    gltf_payload = json.dumps(
        {
            "asset": {"version": "2.0"},
            "buffers": [{"uri": "mesh.bin", "byteLength": 12}],
            "accessors": [{"min": [0, 0, 0], "max": [1, 2, 1]}],
            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        },
    ).encode("utf-8")
    with TestClient(app) as client:
        response = client.post(
            "/api/models/validate-local-bundle",
            data={"main_filename": "bundle.gltf"},
            files=[
                ("files", ("bundle.gltf", gltf_payload, "model/gltf+json")),
                ("files", ("mesh.bin", b"\x00" * 12, "application/octet-stream")),
            ],
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["can_stage_locally"] is True
    assert payload["resource_mode"] == "bundle-resolved"
    assert payload["metrics"]["resolved_external_resource_count"] == 1
    assert payload["metrics"]["resolved_external_resources"] == ["mesh.bin"]


def test_local_model_bundle_validation_endpoint_blocks_incomplete_gltf_bundle() -> None:
    gltf_payload = json.dumps(
        {
            "asset": {"version": "2.0"},
            "buffers": [{"uri": "mesh.bin", "byteLength": 12}],
            "meshes": [{"primitives": [{}]}],
        },
    ).encode("utf-8")
    with TestClient(app) as client:
        response = client.post(
            "/api/models/validate-local-bundle",
            data={"main_filename": "bundle.gltf"},
            files=[("files", ("bundle.gltf", gltf_payload, "model/gltf+json"))],
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["can_stage_locally"] is False
    assert payload["resource_mode"] == "bundle-incomplete"
    assert payload["metrics"]["missing_external_resources"] == ["mesh.bin"]


def test_braille_preview_returns_positioned_cells() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/braille/preview",
            json={"text": "FeelIT", "columns": 3},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["cell_count"] == 6
    assert payload["cells"][0]["row"] == 0
    assert payload["cells"][3]["row"] == 1


def test_library_document_catalog_endpoint_exposes_bundled_formats() -> None:
    with TestClient(app) as client:
        response = client.get("/api/library/documents")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload["supported_formats"]) == {"txt", "html", "epub"}
    assert len(payload["documents"]) >= 5
    assert all(document["file_size_bytes"] < 60 * 1024 * 1024 for document in payload["documents"])


def test_library_document_payload_endpoint_returns_segmented_text() -> None:
    with TestClient(app) as client:
        response = client.get("/api/library/documents/alice_in_wonderland_txt?offset=0&max_chars=900")
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Alice's Adventures in Wonderland"
    assert "Alice" in payload["text"]
    assert payload["loaded_characters"] <= 900
    assert payload["next_offset"] is not None


def test_library_audio_catalog_endpoint_exposes_tracks() -> None:
    with TestClient(app) as client:
        response = client.get("/api/library/audio")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["audio"]) >= 4
    assert all(track["file_url"].endswith(".mp3") for track in payload["audio"])
    assert all(track["file_size_bytes"] < 60 * 1024 * 1024 for track in payload["audio"])
