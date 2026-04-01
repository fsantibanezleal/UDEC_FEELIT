"""Bridge-facing pilot command contracts for first haptic primitive execution."""

from __future__ import annotations

from typing import Any


def _command_transport(backend_slug: str) -> dict[str, str]:
    """Return the current transport assumptions for one backend command."""
    if backend_slug == "visual-emulator":
        return {
            "mode": "browser-mirror",
            "executor": "frontend-debug-runtime",
            "summary": "Dry-run only inside the visual emulator mirror path.",
        }
    return {
        "mode": "native-sidecar-json",
        "executor": "future-bridge-consumer",
        "summary": "Dry-run JSON payload intended for a native bridge or sidecar consumer.",
    }


def _force_model(scenario: dict[str, Any]) -> dict[str, Any]:
    """Return the bridge-facing force model summary for one pilot scenario."""
    profile = scenario["pilot_profile"]
    primitive_family = str(scenario["primitive_family"])
    required_force_channels = list(scenario["required_force_channels"])

    if primitive_family == "button_actuation":
        return {
            "model_slug": "thresholded_button_actuation",
            "channels": required_force_channels,
            "parameters": {
                "spring_k_n_per_mm": profile["spring_k_n_per_mm"],
                "activation_travel_mm": profile["activation_travel_mm"],
                "release_hysteresis_mm": profile["release_hysteresis_mm"],
                "damping": profile["damping"],
            },
        }

    return {
        "model_slug": "bounded_proxy_surface_following",
        "channels": required_force_channels,
        "parameters": {
            "normal_stiffness_n_per_mm": profile["normal_stiffness_n_per_mm"],
            "damping": profile["damping"],
            "static_friction": profile["static_friction"],
            "dynamic_friction": profile["dynamic_friction"],
            "max_penetration_mm": profile["max_penetration_mm"],
        },
    }


def _safety_envelope(scenario: dict[str, Any]) -> dict[str, Any]:
    """Return the bounded safety envelope for one pilot command."""
    profile = scenario["pilot_profile"]
    primitive_family = str(scenario["primitive_family"])
    limits: dict[str, Any] = {
        "max_force_n": profile["max_force_n"],
        "required_gates": list(scenario["safety_gates"]),
        "allow_scene_wide_force_loop": False,
    }
    if primitive_family == "button_actuation":
        limits["max_travel_mm"] = profile["activation_travel_mm"]
    else:
        limits["max_penetration_mm"] = profile["max_penetration_mm"]
    return limits


def _dry_run_expectations(scenario: dict[str, Any]) -> list[str]:
    """Return the expected dry-run checks for one pilot command."""
    expectations = [
        "The payload must remain serializable and deterministic for CI validation.",
        "The command must not imply that the full scene is executing a servo loop.",
        "The pilot should remain bounded to one primitive family and one route.",
    ]
    primitive_family = str(scenario["primitive_family"])
    if primitive_family == "button_actuation":
        expectations.append(
            "Dry-run validation should preserve activation hysteresis and release-cue thresholds.",
        )
    else:
        expectations.append(
            "Dry-run validation should preserve bounded penetration depth and contact-normal semantics.",
        )
    return expectations


def build_haptic_pilot_commands(contact_rollout: dict[str, Any]) -> dict[str, Any]:
    """Return bridge-facing dry-run pilot commands derived from the rollout plan."""
    commands: list[dict[str, Any]] = []

    for scenario in contact_rollout["pilot_scenarios"]:
        command_slug = f"{scenario['backend_slug']}::{scenario['pilot_primitive_slug']}"
        commands.append(
            {
                "command_slug": command_slug,
                "schema_version": "1",
                "backend_slug": scenario["backend_slug"],
                "pilot_mode": scenario["pilot_mode"],
                "pilot_route": scenario["pilot_route"],
                "primitive_slug": scenario["pilot_primitive_slug"],
                "primitive_family": scenario["primitive_family"],
                "transport": _command_transport(str(scenario["backend_slug"])),
                "readiness_state": scenario["readiness_state"],
                "capability_alignment": scenario["capability_alignment"],
                "required_runtime_features": list(scenario["required_runtime_features"]),
                "missing_runtime_features": list(scenario["missing_runtime_features"]),
                "material_preset_slug": scenario["material_preset_slug"],
                "geometry_profile": dict(scenario["pilot_profile"]),
                "force_model": _force_model(scenario),
                "safety_envelope": _safety_envelope(scenario),
                "telemetry_contract": {
                    "minimum_fields": [
                        "command_slug",
                        "primitive_slug",
                        "backend_slug",
                        "contact_state",
                        "constraint_state",
                        "scene_route",
                    ],
                    "scene_expectations": [
                        scenario["pilot_mode"],
                        scenario["pilot_route"],
                        scenario["pilot_primitive_slug"],
                    ],
                },
                "dry_run_expectations": _dry_run_expectations(scenario),
                "next_engineering_step": scenario["next_engineering_step"],
            }
        )

    return {
        "summary": (
            "Each pilot command is a bounded dry-run payload that a future native bridge can "
            "consume before FeelIT attempts any full scene-wide force execution."
        ),
        "transport_boundary": (
            "The current contract stops at serialized command generation. Native execution, "
            "acknowledgement, and force-loop ownership remain future work."
        ),
        "commands": commands,
    }
