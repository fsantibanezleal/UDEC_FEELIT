"""Tests for FeelIT API endpoints."""

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
    assert payload["haptics"]["backend"] == "null"


def test_modes_endpoint_exposes_three_modes() -> None:
    with TestClient(app) as client:
        response = client.get("/api/modes")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["modes"]) == 3


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
    assert object_response.status_code == 200
    assert "3D Object Explorer" in object_response.text
    assert "Space activate" in object_response.text
    assert 'type="module" src="/static/js/object_explorer.js"' in object_response.text
    assert '/static/js/app.js" defer' not in object_response.text
    assert braille_response.status_code == 200
    assert "Braille Reader" in braille_response.text
    assert "Previous Page (Fallback)" in braille_response.text
    assert "WASD/QE pointer" in braille_response.text
    assert 'type="module" src="/static/js/braille_reader.js"' in braille_response.text
    assert '/static/js/app.js" defer' not in braille_response.text
    assert desktop_response.status_code == 200
    assert "Haptic Desktop" in desktop_response.text
    assert "Activate (Fallback)" in desktop_response.text
    assert "Space activate" in desktop_response.text
    assert 'type="module" src="/static/js/haptic_desktop.js"' in desktop_response.text
    assert '/static/js/app.js" defer' not in desktop_response.text


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


def test_demo_model_endpoint_exposes_local_obj_assets() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo-models")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["models"]) >= 4
    assert all(model["file_url"].endswith(".obj") for model in payload["models"])


def test_demo_model_static_assets_are_served() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo-models")
        assert response.status_code == 200
        models = response.json()["models"]
        for model in models:
            asset_response = client.get(model["file_url"])
            assert asset_response.status_code == 200
            assert "v " in asset_response.text


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
