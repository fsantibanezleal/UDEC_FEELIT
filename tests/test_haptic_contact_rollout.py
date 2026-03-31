"""Tests for backend-aware contact rollout planning."""

from app.core.haptic_contact_rollout import build_haptic_contact_rollout


def test_contact_rollout_covers_all_primary_backends() -> None:
    rollout = build_haptic_contact_rollout(
        [
            {"slug": "visual-emulator", "bridge_probe_state": "not-run"},
            {"slug": "openhaptics-touch", "bridge_probe_state": "runtime-loaded-capability-ready"},
            {
                "slug": "forcedimension-dhd",
                "bridge_probe_state": "ready",
                "detected_device_count": 1,
                "detected_devices": ["Force Dimension Demo"],
            },
            {"slug": "chai3d-bridge", "bridge_probe_state": "scaffold-only"},
        ]
    )

    scenario_slugs = {item["backend_slug"] for item in rollout["pilot_scenarios"]}
    assert {
        "visual-emulator",
        "openhaptics-touch",
        "forcedimension-dhd",
        "chai3d-bridge",
    } <= scenario_slugs


def test_contact_rollout_marks_device_ready_backend_for_pilot() -> None:
    rollout = build_haptic_contact_rollout(
        [
            {
                "slug": "forcedimension-dhd",
                "bridge_probe_state": "ready",
                "detected_device_count": 1,
                "detected_devices": ["Device A"],
                "reported_capabilities": [
                    "force-feedback-path",
                    "servo-loop-telemetry",
                    "workspace-alignment",
                ],
            }
        ]
    )

    forcedimension = next(
        item for item in rollout["pilot_scenarios"] if item["backend_slug"] == "forcedimension-dhd"
    )
    assert forcedimension["readiness_state"] == "device-ready-for-pilot"
    assert forcedimension["current_detected_devices"] == ["Device A"]
    assert forcedimension["required_force_channels"]
    assert forcedimension["capability_alignment"] == "aligned"
    assert forcedimension["pilot_profile"]["geometry_kind"] == "reduced_proxy_surface"
    assert forcedimension["pilot_profile"]["material_preset_slug"] == "polished_metal"


def test_contact_rollout_marks_missing_runtime_features_when_probe_is_partial() -> None:
    rollout = build_haptic_contact_rollout(
        [
            {
                "slug": "openhaptics-touch",
                "bridge_probe_state": "runtime-loaded-capability-ready",
                "reported_capabilities": ["force-output-path", "scheduler-control"],
            }
        ]
    )

    openhaptics = next(
        item for item in rollout["pilot_scenarios"] if item["backend_slug"] == "openhaptics-touch"
    )
    assert openhaptics["readiness_state"] == "runtime-ready-awaiting-scene-coupling"
    assert openhaptics["capability_alignment"] == "partial"
    assert "input_path" in openhaptics["missing_runtime_features"]
