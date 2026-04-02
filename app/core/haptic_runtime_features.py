"""Shared normalized feature schema for haptic runtime and bridge capability reporting."""

from __future__ import annotations

from typing import Iterable


FEATURE_ALIASES: dict[str, set[str]] = {
    "scene_debug": {"scene-debug"},
    "pointer_path": {"pointer-emulation", "button-proxy-input-path", "button-and-proxy-input"},
    "input_path": {"button-proxy-input-path", "button-and-proxy-input"},
    "force_path": {
        "force-output-path",
        "force-feedback-path",
        "force-feedback",
        "scene-level-haptics",
        "proxy-based-contact",
    },
    "state_query": {"device-state-query", "servo-loop-telemetry"},
    "device_characteristics_query": {"device-characteristics-query"},
    "device_identity_query": {"device-detection"},
    "device_open_close": {"device-open-close"},
    "error_reporting": {"error-reporting"},
    "scheduler_or_servo_loop": {"scheduler-control", "servo-loop-telemetry"},
    "workspace_alignment": {"workspace-alignment", "device-context-query"},
    "calibration_interface": {"calibration-interface"},
    "compatibility_bridge": {"compatibility-abstraction", "scene-level-haptics"},
}


def normalize_runtime_features(
    raw_values: Iterable[str] | None = None,
    *,
    direct_features: Iterable[str] | None = None,
) -> list[str]:
    """Return one stable normalized feature list from direct and legacy capability values."""
    normalized = {
        str(item).strip()
        for item in (direct_features or [])
        if str(item).strip()
    }
    raw_capabilities = {
        str(item).strip()
        for item in (raw_values or [])
        if str(item).strip()
    }
    for feature_slug, aliases in FEATURE_ALIASES.items():
        if raw_capabilities & aliases:
            normalized.add(feature_slug)
    return sorted(normalized)
