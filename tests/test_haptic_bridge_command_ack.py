"""Tests for bridge-side acknowledgement of dry-run pilot commands."""

from __future__ import annotations

import textwrap

from app.core.haptic_contact_rollout import build_haptic_contact_rollout
from app.core.haptic_pilot_commands import build_haptic_pilot_commands
from app.haptics.bridge_probe import acknowledge_native_bridge_command


def _mock_bridge_script(script_path) -> None:
    """Write a mock bridge that supports both probe and command-ack modes."""
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
