"""Tests for bridge-side acknowledgement of dry-run pilot commands."""

from __future__ import annotations

import textwrap

from app.core.haptic_contact_rollout import build_haptic_contact_rollout
from app.core.haptic_pilot_commands import build_haptic_pilot_commands
from app.haptics.bridge_probe import (
    acknowledge_native_bridge_command,
    execute_native_bridge_command,
)


def _mock_bridge_script(script_path) -> None:
    """Write a mock bridge that supports probe, ack, and bounded execution modes."""
    script_path.write_text(
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
                    "status": "scaffold-only",
                    "summary": "Mock bridge probe response.",
                    "device_count": 0,
                    "devices": []
                }))
            """,
        ).strip(),
        encoding="utf-8",
    )


def test_acknowledge_native_bridge_command_returns_ack_payload(tmp_path) -> None:
    script_path = tmp_path / "mock_bridge.py"
    _mock_bridge_script(script_path)

    rollout = build_haptic_contact_rollout(
        [
            {
                "slug": "openhaptics-touch",
                "bridge_probe_state": "runtime-loaded-capability-ready",
                "reported_capabilities": ["force-output-path", "button-proxy-input-path", "scheduler-control"],
            }
        ]
    )
    contract = build_haptic_pilot_commands(rollout)
    command = next(item for item in contract["commands"] if item["backend_slug"] == "openhaptics-touch")

    ack = acknowledge_native_bridge_command(
        str(script_path),
        backend_slug="openhaptics-touch",
        command_payload=command,
        sdk_root=None,
        device_selector="Touch X Left",
    )

    assert ack.state == "command-acknowledged-dry-run"
    assert ack.accepted is True
    assert ack.command_slug == command["command_slug"]
    assert ack.payload["mode"] == "pilot-command-ack"


def test_execute_native_bridge_command_returns_execution_payload(tmp_path) -> None:
    script_path = tmp_path / "mock_bridge.py"
    _mock_bridge_script(script_path)

    rollout = build_haptic_contact_rollout(
        [
            {
                "slug": "openhaptics-touch",
                "bridge_probe_state": "ready",
                "reported_capabilities": [
                    "force-output-path",
                    "button-proxy-input-path",
                    "scheduler-control",
                ],
                "normalized_features": [
                    "force_path",
                    "input_path",
                    "scheduler_or_servo_loop",
                ],
            }
        ]
    )
    contract = build_haptic_pilot_commands(rollout)
    command = next(item for item in contract["commands"] if item["backend_slug"] == "openhaptics-touch")

    execution = execute_native_bridge_command(
        str(script_path),
        backend_slug="openhaptics-touch",
        command_payload=command,
        sdk_root=None,
        device_selector="Touch X Left",
    )

    assert execution.state == "command-executed-bounded-no-force"
    assert execution.executed is True
    assert execution.command_slug == command["command_slug"]
    assert execution.payload["mode"] == "pilot-command-execution"
