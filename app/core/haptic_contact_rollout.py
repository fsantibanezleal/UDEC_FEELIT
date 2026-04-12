"""Dynamic rollout planning for the first scene-coupled haptic contact milestones."""

from __future__ import annotations

from typing import Any

from app.core.haptic_materials import build_material_catalog
from app.core.haptic_runtime_features import normalize_runtime_features

ROLLOUT_BLUEPRINTS: tuple[dict[str, object], ...] = (
    {
        "backend_slug": "visual-emulator",
        "backend_title": "Visual Pointer Emulator",
        "pilot_mode": "3D Object Explorer",
        "pilot_route": "/object-explorer",
        "pilot_primitive_slug": "proxy_object_surface",
        "primitive_family": "rigid_surface_following",
        "material_preset_slug": "polished_metal",
        "pilot_goal": (
            "Keep the browser-side mirror faithful while native stacks converge on the same "
            "contact surface, telemetry, and return-flow semantics."
        ),
        "required_force_channels": ["normal_force", "stiffness", "damping"],
        "required_capability_scope": "scene-debug",
        "required_runtime_features": ["scene_debug", "pointer_path"],
        "safety_gates": [
            "bounded workspace scale",
            "stable proxy geometry",
            "deterministic contact-state transitions",
        ],
        "runtime_ready_step": "No physical runtime needed. Use this path to verify scene geometry and telemetry.",
        "device_ready_step": "Not applicable because this is the no-device mirror path.",
        "blocked_step": "No blocker. This path remains the debug baseline for all native rollout work.",
    },
    {
        "backend_slug": "openhaptics-touch",
        "backend_title": "OpenHaptics Touch Stack",
        "pilot_mode": "Haptic Desktop",
        "pilot_route": "/haptic-desktop",
        "pilot_primitive_slug": "launcher_and_gallery_tiles",
        "primitive_family": "button_actuation",
        "material_preset_slug": "textured_polymer",
        "pilot_goal": (
            "Implement one bounded tactile tile with thresholded activation and explicit "
            "return-flow semantics before attempting richer scene contact."
        ),
        "required_force_channels": ["spring", "threshold", "snap-through", "release cue"],
        "required_capability_scope": "runtime-loaded-capability-ready",
        "required_runtime_features": ["force_path", "input_path", "scheduler_or_servo_loop"],
        "safety_gates": [
            "activation hysteresis",
            "travel clamp",
            "safe force envelope",
        ],
        "runtime_ready_step": (
            "Bind one launcher tile to a conservative thresholded force profile using the "
            "current preferred selector and capability diagnostics."
        ),
        "device_ready_step": (
            "Validate tile activation, release cues, and launcher-return semantics on real "
            "OpenHaptics hardware."
        ),
        "blocked_step": (
            "Finish reliable runtime loading and device bring-up before scene-coupled control "
            "is attempted."
        ),
    },
    {
        "backend_slug": "forcedimension-dhd",
        "backend_title": "Force Dimension DHD Stack",
        "pilot_mode": "3D Object Explorer",
        "pilot_route": "/object-explorer",
        "pilot_primitive_slug": "proxy_object_surface",
        "primitive_family": "rigid_surface_following",
        "material_preset_slug": "polished_metal",
        "pilot_goal": (
            "Map one reduced proxy object surface into stable continuous contact with explicit "
            "surface-normal and penetration telemetry."
        ),
        "required_force_channels": ["normal_force", "stiffness", "surface_friction"],
        "required_capability_scope": "device-enumeration-ready",
        "required_runtime_features": [
            "force_path",
            "state_query",
            "workspace_alignment",
            "scheduler_or_servo_loop",
        ],
        "safety_gates": [
            "force clamp",
            "bounded penetration depth",
            "stable contact normal",
        ],
        "runtime_ready_step": (
            "Translate runtime enumeration into one bounded surface-following primitive with "
            "telemetry capture, but keep force output conservative until device validation."
        ),
        "device_ready_step": (
            "Validate stable surface following, contact entry or exit, and proxy geometry "
            "alignment on a detected DHD-compatible device."
        ),
        "blocked_step": (
            "Keep the DHD path in diagnostics and enumeration mode until one real contact "
            "primitive can be bounded safely."
        ),
    },
    {
        "backend_slug": "chai3d-bridge",
        "backend_title": "CHAI3D Bridge Stack",
        "pilot_mode": "Braille Reader",
        "pilot_route": "/braille-reader",
        "pilot_primitive_slug": "reading_plane",
        "primitive_family": "rigid_surface_following",
        "material_preset_slug": "coated_paper",
        "pilot_goal": (
            "Use the compatibility bridge to prove one planar reading surface and one explicit "
            "Braille navigation control before broader multi-device abstraction."
        ),
        "required_force_channels": ["plane_constraint", "damping", "spring"],
        "required_capability_scope": "compatibility-abstraction",
        "required_runtime_features": ["compatibility_bridge", "force_path"],
        "safety_gates": [
            "reading-plane bounds",
            "soft edge exit",
            "control reachability",
        ],
        "runtime_ready_step": (
            "Promote the scaffold into a minimal compatibility runtime that can consume one "
            "reading plane plus one navigation button."
        ),
        "device_ready_step": (
            "Validate that the compatibility bridge preserves the same scene semantics as the "
            "vendor-specific stacks."
        ),
        "blocked_step": (
            "Move the CHAI3D path beyond scaffold-only state before trying to carry scene "
            "primitives through it."
        ),
    },
)

def _material_map() -> dict[str, dict[str, Any]]:
    """Return the haptic material catalog keyed by slug."""
    return {str(item["slug"]): item for item in build_material_catalog()}


def _find_backend(backends: list[dict[str, Any]], slug: str) -> dict[str, Any]:
    """Return one backend snapshot row by slug."""
    return next((item for item in backends if item.get("slug") == slug), {})


def _resolve_readiness_state(backend: dict[str, Any]) -> tuple[str, str]:
    """Return the current rollout readiness state and a concise reason."""
    slug = str(backend.get("slug", ""))
    if slug == "visual-emulator":
        return (
            "debug-path-ready",
            "The visual emulator already mirrors the routed scenes and can validate geometry or telemetry.",
        )

    probe_state = str(backend.get("bridge_probe_state", "not-run"))
    detected_device_count = int(backend.get("detected_device_count") or 0)
    availability = str(backend.get("availability", ""))

    if probe_state == "ready" and detected_device_count > 0:
        return (
            "device-ready-for-pilot",
            "A native runtime is present and at least one device identity was reported.",
        )
    if probe_state in {"runtime-loaded-capability-ready", "runtime-loaded-no-devices"}:
        return (
            "runtime-ready-awaiting-scene-coupling",
            "The runtime can load and report capability state, but scene-coupled contact is not wired yet.",
        )
    if availability in {
        "bridge-scaffold-detected",
        "sdk-driver-and-bridge-detected",
        "sdk-and-bridge-detected",
        "sdk-detected",
    }:
        return (
            "dependency-ready-but-not-runtime-ready",
            "Dependencies are partially present, but runtime loading or usable device control is not ready.",
        )
    return (
        "blocked-by-runtime-readiness",
        "The backend is still blocked by missing runtime dependencies, probe failures, or absent device paths.",
    )


def _available_runtime_features(backend: dict[str, Any]) -> set[str]:
    """Map reported backend capabilities into abstract runtime features."""
    return set(
        normalize_runtime_features(
            backend.get("reported_capabilities", []),
            direct_features=backend.get("normalized_features", []),
        )
    )


def _build_capability_alignment(
    backend: dict[str, Any],
    required_runtime_features: list[str],
) -> tuple[str, list[str], list[str]]:
    """Return abstract capability coverage for one pilot scenario."""
    available_features = _available_runtime_features(backend)
    missing_features = [
        feature for feature in required_runtime_features if feature not in available_features
    ]
    available_list = sorted(available_features)

    if not required_runtime_features:
        return "not-needed", available_list, missing_features
    if not missing_features:
        return "aligned", available_list, missing_features
    if len(missing_features) == len(required_runtime_features):
        return "insufficient", available_list, missing_features
    return "partial", available_list, missing_features


def _build_pilot_profile(
    primitive_family: str,
    material_profile: dict[str, Any],
) -> dict[str, Any]:
    """Return a first bridge-facing pilot profile for one primitive family."""
    if primitive_family == "button_actuation":
        activation_travel_mm = 1.4
        return {
            "geometry_kind": "bounded_tactile_button",
            "material_preset_slug": material_profile["slug"],
            "spring_k_n_per_mm": round(float(material_profile["stiffness_n_per_mm"]) * 0.55, 3),
            "damping": round(float(material_profile["damping"]), 3),
            "activation_travel_mm": activation_travel_mm,
            "release_hysteresis_mm": 0.35,
            "max_force_n": round(float(material_profile["stiffness_n_per_mm"]) * activation_travel_mm, 3),
        }
    return {
        "geometry_kind": "reduced_proxy_surface",
        "material_preset_slug": material_profile["slug"],
        "normal_stiffness_n_per_mm": round(float(material_profile["stiffness_n_per_mm"]), 3),
        "damping": round(float(material_profile["damping"]), 3),
        "static_friction": round(float(material_profile["static_friction"]), 3),
        "dynamic_friction": round(float(material_profile["dynamic_friction"]), 3),
        "max_penetration_mm": 1.6,
        "max_force_n": round(float(material_profile["stiffness_n_per_mm"]) * 1.6, 3),
    }


def build_haptic_contact_rollout(backends: list[dict[str, Any]]) -> dict[str, object]:
    """Return the backend-aware rollout plan for first scene-coupled haptic milestones."""
    material_map = _material_map()
    pilot_scenarios: list[dict[str, object]] = []

    for blueprint in ROLLOUT_BLUEPRINTS:
        backend = _find_backend(backends, str(blueprint["backend_slug"]))
        readiness_state, readiness_reason = _resolve_readiness_state(backend)
        capability_alignment, available_features, missing_features = _build_capability_alignment(
            backend,
            list(blueprint["required_runtime_features"]),
        )
        material_profile = material_map[str(blueprint["material_preset_slug"])]
        pilot_profile = _build_pilot_profile(
            str(blueprint["primitive_family"]),
            material_profile,
        )

        if readiness_state == "debug-path-ready":
            next_engineering_step = str(blueprint["runtime_ready_step"])
        elif readiness_state == "device-ready-for-pilot":
            next_engineering_step = str(blueprint["device_ready_step"])
        elif readiness_state == "runtime-ready-awaiting-scene-coupling":
            next_engineering_step = str(blueprint["runtime_ready_step"])
        else:
            next_engineering_step = str(blueprint["blocked_step"])

        pilot_scenarios.append(
            {
                "backend_slug": blueprint["backend_slug"],
                "backend_title": blueprint["backend_title"],
                "pilot_mode": blueprint["pilot_mode"],
                "pilot_route": blueprint["pilot_route"],
                "pilot_primitive_slug": blueprint["pilot_primitive_slug"],
                "primitive_family": blueprint["primitive_family"],
                "material_preset_slug": material_profile["slug"],
                "pilot_goal": blueprint["pilot_goal"],
                "required_force_channels": blueprint["required_force_channels"],
                "required_capability_scope": blueprint["required_capability_scope"],
                "required_runtime_features": blueprint["required_runtime_features"],
                "safety_gates": blueprint["safety_gates"],
                "readiness_state": readiness_state,
                "readiness_reason": readiness_reason,
                "capability_alignment": capability_alignment,
                "available_runtime_features": available_features,
                "missing_runtime_features": missing_features,
                "pilot_profile": pilot_profile,
                "current_probe_state": backend.get("bridge_probe_state", "not-run"),
                "current_capability_scope": backend.get("probe_capability_scope"),
                "current_detected_devices": backend.get("detected_devices", []),
                "next_engineering_step": next_engineering_step,
            }
        )

    return {
        "summary": (
            "The first native haptic milestone should be a bounded pilot primitive per backend, "
            "not a jump straight into a full scene-wide force loop."
        ),
        "pilot_scenarios": pilot_scenarios,
    }
