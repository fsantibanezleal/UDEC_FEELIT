"""Tests for haptic runtime configuration and diagnostics."""

from __future__ import annotations

import textwrap
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
    assert any(tool.slug == "cmake" for tool in snapshot.toolchains)
    assert snapshot.bridge_workspace.probe_binary_name == "feelit_bridge_probe.exe"
    assert snapshot.contact_design["servo_loop_target_hz"] == 1000
    assert any(item["slug"] == "polished_metal" for item in snapshot.material_rendering)
    assert len(snapshot.scene_contract["mode_contracts"]) >= 3
    assert any(item["mode"] == "Braille Reader" for item in snapshot.scene_contract["mode_contracts"])
    assert any(
        item["slug"] == "button_actuation"
        for item in snapshot.scene_contract["primitive_families"]
    )
    assert any(
        item["backend_slug"] == "openhaptics-touch"
        for item in snapshot.scene_contract["backend_readiness"]
    )
    assert len(snapshot.contact_rollout["pilot_scenarios"]) >= 4
    assert any(
        item["backend_slug"] == "forcedimension-dhd"
        for item in snapshot.contact_rollout["pilot_scenarios"]
    )
    assert all(item["pilot_profile"] for item in snapshot.contact_rollout["pilot_scenarios"])
    assert len(snapshot.pilot_command_contract["commands"]) >= 4
    assert any(
        item["backend_slug"] == "openhaptics-touch"
        for item in snapshot.pilot_command_contract["commands"]
    )
    visual_backend = next(backend for backend in snapshot.backends if backend.slug == "visual-emulator")
    assert "scene_debug" in visual_backend.normalized_features
    assert "pointer_path" in visual_backend.normalized_features
    assert visual_backend.verified_features == visual_backend.normalized_features
    assert any(
        item["acknowledgement"]["state"] == "browser-mirror-acknowledged"
        for item in snapshot.pilot_command_contract["commands"]
        if item["backend_slug"] == "visual-emulator"
    )
    assert any(
        item["execution"]["state"] == "browser-mirror-executed"
        for item in snapshot.pilot_command_contract["commands"]
        if item["backend_slug"] == "visual-emulator"
    )


def test_haptic_runtime_update_persists_requested_backend(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "haptic_runtime_config.json"
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))

    manager = HapticRuntimeManager()
    snapshot = manager.update_configuration(
        requested_backend="openhaptics-touch",
        sdk_roots={"openhaptics": r"C:\SDKs\OpenHaptics"},
        bridge_paths={"openhaptics": r"D:\Bridges\openhaptics_bridge.exe"},
        device_selectors={"openhaptics": "Touch X Left"},
    )

    openhaptics = next(backend for backend in snapshot.backends if backend.slug == "openhaptics-touch")
    assert snapshot.requested_backend == "openhaptics-touch"
    assert snapshot.active_backend == "visual-emulator"
    assert openhaptics.configured_sdk_root == r"C:\SDKs\OpenHaptics"
    assert openhaptics.configured_bridge_path == r"D:\Bridges\openhaptics_bridge.exe"
    assert openhaptics.configured_device_selector == "Touch X Left"
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
    assert any(tool["slug"] == "ninja" for tool in payload["toolchains"])
    assert payload["bridge_workspace"]["probe_binary_name"] == "feelit_bridge_probe.exe"
    assert any(backend["slug"] == "chai3d-bridge" for backend in payload["backends"])
    assert len(payload["scene_contract"]["event_contract"]) >= 5
    assert len(payload["scene_contract"]["primitive_families"]) >= 3
    assert len(payload["scene_contract"]["backend_readiness"]) >= 4
    assert len(payload["contact_rollout"]["pilot_scenarios"]) >= 4
    assert any(
        item["capability_alignment"] in {"aligned", "partial", "insufficient", "not-needed"}
        for item in payload["contact_rollout"]["pilot_scenarios"]
    )
    assert any("normalized_features" in backend for backend in payload["backends"])
    assert len(payload["pilot_command_contract"]["commands"]) >= 4


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
                "device_selectors": {"forcedimension": "omega-left"},
            },
        )

    assert response.status_code == 200
    payload = response.json()
    forcedimension = next(backend for backend in payload["backends"] if backend["slug"] == "forcedimension-dhd")
    assert payload["requested_backend"] == "forcedimension-dhd"
    assert payload["active_backend"] == "visual-emulator"
    assert forcedimension["configured_sdk_root"] == r"C:\SDKs\ForceDimension"
    assert forcedimension["configured_bridge_path"] == r"D:\Bridges\fd_bridge.exe"
    assert forcedimension["configured_device_selector"] == "omega-left"


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


def test_haptic_runtime_runs_python_bridge_probe(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "haptic_runtime_config.json"
    bridge_script = tmp_path / "mock_bridge_probe.py"
    bridge_script.write_text(
        textwrap.dedent(
            """
            import json

            print(json.dumps({
                "backend": "openhaptics-touch",
                "status": "scaffold-only",
                "summary": "Mock bridge responded successfully.",
                "device_count": 0,
                "devices": [],
                "enumeration_mode": "analysis-only",
                "capability_scope": "probe-contract",
                "reported_capabilities": ["diagnostics-only"],
                "probe_notes": ["Mock note"]
            }))
            """,
        ).strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))

    manager = HapticRuntimeManager()
    snapshot = manager.update_configuration(
        requested_backend="openhaptics-touch",
        sdk_roots={},
        bridge_paths={"openhaptics": str(bridge_script)},
        device_selectors={"openhaptics": "Mock Touch X"},
    )

    openhaptics = next(backend for backend in snapshot.backends if backend.slug == "openhaptics-touch")
    assert openhaptics.detected_bridge_path == str(bridge_script.resolve())
    assert openhaptics.bridge_probe_state == "scaffold-only"
    assert openhaptics.bridge_probe_summary == "Mock bridge responded successfully."
    assert openhaptics.configured_device_selector == "Mock Touch X"
    assert openhaptics.probe_enumeration_mode == "analysis-only"
    assert openhaptics.probe_capability_scope == "probe-contract"
    assert openhaptics.reported_capabilities == ["diagnostics-only"]
    assert openhaptics.normalized_features == []
    assert openhaptics.probe_notes == ["Mock note"]


def test_haptic_runtime_snapshot_surfaces_pilot_command_acknowledgement(
    tmp_path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "haptic_runtime_config.json"
    bridge_script = tmp_path / "mock_bridge_probe.py"
    bridge_script.write_text(
        textwrap.dedent(
            """
            import json
            import pathlib
            import sys

            args = sys.argv[1:]

            def value(option, fallback=""):
                if option in args:
                    index = args.index(option)
                    if index + 1 < len(args):
                        return args[index + 1]
                return fallback

            backend = value("--backend", "openhaptics-touch")
            command_path = value("--consume-pilot-command-file")
            execution_path = value("--execute-pilot-command-file")

            if command_path:
                payload = json.loads(pathlib.Path(command_path).read_text(encoding="utf-8"))
                print(json.dumps({
                    "mode": "pilot-command-ack",
                    "backend": backend,
                    "status": "command-acknowledged-dry-run",
                    "summary": "Mock bridge accepted the pilot command payload.",
                    "accepted": True,
                    "command_slug": payload["command_slug"],
                    "validated_fields": ["command_slug", "backend_slug", "primitive_slug"],
                    "missing_fields": [],
                    "notes": ["Mock acknowledgement only."]
                }))
            elif execution_path:
                payload = json.loads(pathlib.Path(execution_path).read_text(encoding="utf-8"))
                print(json.dumps({
                    "mode": "pilot-command-execution",
                    "backend": backend,
                    "status": "command-executed-bounded-no-force",
                    "summary": "Mock bridge executed the bounded pilot command.",
                    "executed": True,
                    "command_slug": payload["command_slug"],
                    "primitive_slug": payload["primitive_slug"],
                    "primitive_family": payload["primitive_family"],
                    "pilot_mode": payload["pilot_mode"],
                    "pilot_route": payload["pilot_route"],
                    "execution_mode": "mock-bounded-no-force",
                    "safety_state": "mock-safe",
                    "device_selector_used": value("--device-selector", ""),
                    "telemetry_fields": ["command_slug", "primitive_slug", "scene_route"],
                    "notes": ["Mock execution only."]
                }))
            else:
                print(json.dumps({
                    "backend": backend,
                    "status": "runtime-loaded-capability-ready",
                    "summary": "Mock bridge runtime load state.",
                    "device_count": 0,
                    "devices": [],
                    "enumeration_mode": "analysis-only",
                    "capability_scope": "probe-contract",
                    "reported_capabilities": ["force-output-path", "button-proxy-input-path", "scheduler-control"],
                    "probe_notes": ["Mock note"]
                }))
            """,
        ).strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))

    manager = HapticRuntimeManager()
    snapshot = manager.update_configuration(
        requested_backend="openhaptics-touch",
        sdk_roots={},
        bridge_paths={"openhaptics": str(bridge_script)},
        device_selectors={"openhaptics": "Mock Touch X"},
    )

    openhaptics_command = next(
        item
        for item in snapshot.pilot_command_contract["commands"]
        if item["backend_slug"] == "openhaptics-touch"
    )
    openhaptics_backend = next(
        backend for backend in snapshot.backends if backend.slug == "openhaptics-touch"
    )
    assert "force_path" in openhaptics_backend.normalized_features
    assert "input_path" in openhaptics_backend.normalized_features
    assert openhaptics_backend.verified_features == []
    assert "force_path" in openhaptics_backend.inferred_features
    assert openhaptics_command["acknowledgement"]["state"] == "command-acknowledged-dry-run"
    assert openhaptics_command["acknowledgement"]["accepted"] is True
    assert openhaptics_command["execution"]["state"] == "command-executed-bounded-no-force"
    assert openhaptics_command["execution"]["executed"] is True


def test_haptic_runtime_snapshot_surfaces_forcedimension_execution(
    tmp_path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "haptic_runtime_config.json"
    bridge_script = tmp_path / "mock_forcedimension_bridge_probe.py"
    bridge_script.write_text(
        textwrap.dedent(
            """
            import json
            import pathlib
            import sys

            args = sys.argv[1:]

            def value(option, fallback=""):
                if option in args:
                    index = args.index(option)
                    if index + 1 < len(args):
                        return args[index + 1]
                return fallback

            backend = value("--backend", "forcedimension-dhd")
            command_path = value("--consume-pilot-command-file")
            execution_path = value("--execute-pilot-command-file")

            if command_path:
                payload = json.loads(pathlib.Path(command_path).read_text(encoding="utf-8"))
                print(json.dumps({
                    "mode": "pilot-command-ack",
                    "backend": backend,
                    "status": "command-acknowledged-dry-run",
                    "summary": "Mock Force Dimension bridge accepted the pilot command payload.",
                    "accepted": True,
                    "command_slug": payload["command_slug"],
                    "validated_fields": ["command_slug", "backend_slug", "primitive_slug"],
                    "missing_fields": [],
                    "notes": ["Mock acknowledgement only."]
                }))
            elif execution_path:
                payload = json.loads(pathlib.Path(execution_path).read_text(encoding="utf-8"))
                print(json.dumps({
                    "mode": "pilot-command-execution",
                    "backend": backend,
                    "status": "command-executed-bounded-no-force",
                    "summary": "Mock Force Dimension bridge executed the bounded pilot command.",
                    "executed": True,
                    "command_slug": payload["command_slug"],
                    "primitive_slug": payload["primitive_slug"],
                    "primitive_family": payload["primitive_family"],
                    "pilot_mode": payload["pilot_mode"],
                    "pilot_route": payload["pilot_route"],
                    "execution_mode": "forcedimension-rigid-surface-bounded-no-force",
                    "safety_state": "mock-safe",
                    "device_selector_used": value("--device-selector", ""),
                    "telemetry_fields": ["command_slug", "primitive_slug", "scene_route", "surface_normal", "penetration_depth_mm"],
                    "notes": ["Mock execution only."]
                }))
            else:
                print(json.dumps({
                    "backend": backend,
                    "status": "ready",
                    "summary": "Mock Force Dimension runtime load state.",
                    "device_count": 2,
                    "devices": ["Mock SIGMA.7", "Mock OMEGA.7 Left"],
                    "enumeration_mode": "per-device-open-id",
                    "capability_scope": "runtime-and-live-device-enumeration",
                    "reported_capabilities": ["device-detection", "workspace-alignment", "force-feedback-path", "servo-loop-telemetry"],
                    "normalized_features": ["device_open_close", "device_identity_query", "state_query", "force_path", "scheduler_or_servo_loop", "workspace_alignment"],
                    "verified_features": ["device_open_close", "device_identity_query", "state_query"],
                    "inferred_features": ["force_path", "scheduler_or_servo_loop", "workspace_alignment"],
                    "probe_notes": ["Mock note"]
                }))
            """,
        ).strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))

    manager = HapticRuntimeManager()
    snapshot = manager.update_configuration(
        requested_backend="forcedimension-dhd",
        sdk_roots={},
        bridge_paths={"forcedimension": str(bridge_script)},
        device_selectors={"forcedimension": "Mock SIGMA.7"},
    )

    forcedimension_command = next(
        item
        for item in snapshot.pilot_command_contract["commands"]
        if item["backend_slug"] == "forcedimension-dhd"
    )
    forcedimension_backend = next(
        backend for backend in snapshot.backends if backend.slug == "forcedimension-dhd"
    )
    assert forcedimension_backend.bridge_probe_state == "ready"
    assert forcedimension_backend.detected_devices == ["Mock SIGMA.7", "Mock OMEGA.7 Left"]
    assert "workspace_alignment" in forcedimension_backend.normalized_features
    assert "state_query" in forcedimension_backend.verified_features
    assert "force_path" in forcedimension_backend.inferred_features
    assert forcedimension_command["acknowledgement"]["state"] == "command-acknowledged-dry-run"
    assert forcedimension_command["acknowledgement"]["accepted"] is True
    assert forcedimension_command["execution"]["state"] == "command-executed-bounded-no-force"
    assert forcedimension_command["execution"]["executed"] is True
    assert (
        forcedimension_command["execution"]["payload"]["execution_mode"]
        == "forcedimension-rigid-surface-bounded-no-force"
    )
