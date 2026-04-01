"""Tests for bridge-facing haptic pilot command contracts."""

from app.core.haptic_contact_rollout import build_haptic_contact_rollout
from app.core.haptic_pilot_commands import build_haptic_pilot_commands


def test_pilot_command_contract_covers_each_rollout_backend() -> None:
    rollout = build_haptic_contact_rollout(
        [
            {"slug": "visual-emulator", "supported_capabilities": ["scene-debug", "pointer-emulation"]},
            {
                "slug": "openhaptics-touch",
                "bridge_probe_state": "runtime-loaded-capability-ready",
                "reported_capabilities": ["force-output-path", "button-proxy-input-path", "scheduler-control"],
            },
            {
                "slug": "forcedimension-dhd",
                "bridge_probe_state": "ready",
                "detected_device_count": 1,
                "reported_capabilities": ["force-feedback-path", "servo-loop-telemetry", "workspace-alignment"],
            },
            {"slug": "chai3d-bridge", "bridge_probe_state": "scaffold-only"},
        ]
    )
    contract = build_haptic_pilot_commands(rollout)

    backend_slugs = {item["backend_slug"] for item in contract["commands"]}
    assert {"visual-emulator", "openhaptics-touch", "forcedimension-dhd", "chai3d-bridge"} <= backend_slugs


def test_pilot_command_contract_generates_bounded_force_payloads() -> None:
    rollout = build_haptic_contact_rollout(
        [
            {
                "slug": "forcedimension-dhd",
                "bridge_probe_state": "ready",
                "detected_device_count": 1,
                "reported_capabilities": ["force-feedback-path", "servo-loop-telemetry", "workspace-alignment"],
            }
        ]
    )
    contract = build_haptic_pilot_commands(rollout)

    forcedimension = next(
        item for item in contract["commands"] if item["backend_slug"] == "forcedimension-dhd"
    )
    assert forcedimension["force_model"]["model_slug"] == "bounded_proxy_surface_following"
    assert forcedimension["safety_envelope"]["max_force_n"] > 0
    assert forcedimension["telemetry_contract"]["minimum_fields"]
    assert forcedimension["transport"]["mode"] == "native-sidecar-json"
