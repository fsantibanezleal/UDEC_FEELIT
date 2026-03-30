"""Tests for haptic runtime configuration and diagnostics."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.haptics.runtime_manager import HapticRuntimeManager
from app.main import app


def test_haptic_runtime_snapshot_defaults_to_visual_emulator(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "haptic_runtime_config.json"
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))

    manager = HapticRuntimeManager()
    snapshot = manager.configuration_snapshot()

    assert snapshot.requested_backend == "visual-emulator"
    assert snapshot.active_backend == "visual-emulator"
    assert any(backend.slug == "openhaptics-touch" for backend in snapshot.backends)
    assert snapshot.contact_design["servo_loop_target_hz"] == 1000
    assert any(item["slug"] == "polished_metal" for item in snapshot.material_rendering)


def test_haptic_runtime_update_persists_requested_backend(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "haptic_runtime_config.json"
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))

    manager = HapticRuntimeManager()
    snapshot = manager.update_configuration(
        requested_backend="openhaptics-touch",
        sdk_roots={"openhaptics": r"C:\SDKs\OpenHaptics"},
        bridge_paths={"openhaptics": r"D:\Bridges\openhaptics_bridge.exe"},
    )

    openhaptics = next(backend for backend in snapshot.backends if backend.slug == "openhaptics-touch")
    assert snapshot.requested_backend == "openhaptics-touch"
    assert snapshot.active_backend == "visual-emulator"
    assert openhaptics.configured_sdk_root == r"C:\SDKs\OpenHaptics"
    assert openhaptics.configured_bridge_path == r"D:\Bridges\openhaptics_bridge.exe"
    assert config_path.exists()


def test_haptic_configuration_api_returns_runtime_snapshot(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "haptic_runtime_config.json"
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))

    with TestClient(app) as client:
        response = client.get("/api/haptics/configuration")

    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_backend"] == "visual-emulator"
    assert payload["active_backend"] == "visual-emulator"
    assert payload["config_file_label"] == Path(config_path).name
    assert any(backend["slug"] == "chai3d-bridge" for backend in payload["backends"])


def test_haptic_configuration_api_updates_requested_backend(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "haptic_runtime_config.json"
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/haptics/configuration",
            json={
                "requested_backend": "forcedimension-dhd",
                "sdk_roots": {"forcedimension": r"C:\SDKs\ForceDimension"},
                "bridge_paths": {"forcedimension": r"D:\Bridges\fd_bridge.exe"},
            },
        )

    assert response.status_code == 200
    payload = response.json()
    forcedimension = next(backend for backend in payload["backends"] if backend["slug"] == "forcedimension-dhd")
    assert payload["requested_backend"] == "forcedimension-dhd"
    assert payload["active_backend"] == "visual-emulator"
    assert forcedimension["configured_sdk_root"] == r"C:\SDKs\ForceDimension"
    assert forcedimension["configured_bridge_path"] == r"D:\Bridges\fd_bridge.exe"


def test_haptic_configuration_api_rejects_unknown_backend(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "haptic_runtime_config.json"
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))

    with TestClient(app) as client:
        response = client.post(
            "/api/haptics/configuration",
            json={"requested_backend": "unknown-backend"},
        )

    assert response.status_code == 400
    assert "Unsupported haptic backend selection" in response.json()["detail"]
