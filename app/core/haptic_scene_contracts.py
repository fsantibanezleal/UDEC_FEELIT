"""Scene-to-backend haptic interaction contracts for FeelIT modes."""

from __future__ import annotations


def _primitive_families() -> list[dict[str, object]]:
    """Return the reusable tactile primitive families that routed modes compose."""
    return [
        {
            "slug": "rigid_surface_following",
            "title": "Rigid Surface Following",
            "summary": (
                "Stable constrained contact against proxy surfaces, reading planes, or "
                "bounded object geometry."
            ),
            "canonical_force_channels": [
                "normal_force",
                "stiffness",
                "damping",
                "surface_friction",
            ],
            "canonical_events": ["contact_enter", "contact_hold", "contact_exit"],
            "typical_telemetry": [
                "contact_state",
                "surface_normal",
                "penetration_depth",
                "proxy_position",
            ],
            "safety_constraints": [
                "bounded_penetration",
                "force_clamp",
                "stable_proxy_geometry",
            ],
            "used_by_modes": [
                "3D Object Explorer",
                "Braille Reader",
            ],
        },
        {
            "slug": "button_actuation",
            "title": "Button Actuation",
            "summary": (
                "Thresholded spring-like controls for launcher tiles, return actions, "
                "segment changes, and transport actions."
            ),
            "canonical_force_channels": [
                "spring",
                "threshold",
                "snap-through",
                "release cue",
            ],
            "canonical_events": ["contact_enter", "threshold_activate", "contact_exit"],
            "typical_telemetry": [
                "button_state",
                "activation_target",
                "activation_count",
            ],
            "safety_constraints": [
                "activation_hysteresis",
                "travel_limit",
                "return_spring_limit",
            ],
            "used_by_modes": [
                "3D Object Explorer",
                "Braille Reader",
                "Haptic Desktop",
            ],
        },
        {
            "slug": "guidance_and_bounds",
            "title": "Guidance And Bounds",
            "summary": (
                "Rails, edge ridges, reading-plane limits, and typed file-browser forms "
                "that keep the user spatially oriented."
            ),
            "canonical_force_channels": [
                "plane_constraint",
                "edge_ridge",
                "soft_limit",
                "guidance_bias",
            ],
            "canonical_events": ["contact_enter", "guidance_follow", "contact_exit"],
            "typical_telemetry": [
                "zone_slug",
                "bound_state",
                "entry_kind",
                "guidance_progress",
            ],
            "safety_constraints": [
                "workspace_bounds",
                "soft_exit_zone",
                "orientation_anchor",
            ],
            "used_by_modes": [
                "Braille Reader",
                "Haptic Desktop",
            ],
        },
    ]


def _event_contract() -> list[dict[str, object]]:
    """Return backend-facing interaction events that scene primitives may emit."""
    return [
        {
            "slug": "contact_enter",
            "title": "Contact enter",
            "summary": "The stylus or device proxy first intersects one tactile primitive.",
            "emitted_telemetry": ["primitive_slug", "entry_point", "contact_normal"],
            "stability_expectation": "Should remain debounced and deterministic at servo-loop rates.",
        },
        {
            "slug": "contact_hold",
            "title": "Contact hold",
            "summary": (
                "The device remains constrained against a primitive and receives a stable response."
            ),
            "emitted_telemetry": ["contact_state", "penetration_depth", "proxy_position"],
            "stability_expectation": "Should not chatter while the proxy is stably constrained.",
        },
        {
            "slug": "contact_exit",
            "title": "Contact exit",
            "summary": (
                "The device leaves the primitive and the constraint or texture response is released."
            ),
            "emitted_telemetry": ["primitive_slug", "release_velocity"],
            "stability_expectation": "Should end force output cleanly without lingering constraints.",
        },
        {
            "slug": "threshold_activate",
            "title": "Threshold activation",
            "summary": (
                "A button-like primitive crosses its activation threshold and emits a scene action."
            ),
            "emitted_telemetry": ["activation_target", "travel_depth", "activation_count"],
            "stability_expectation": "Must honor hysteresis so buttons do not re-trigger accidentally.",
        },
        {
            "slug": "guidance_follow",
            "title": "Guidance follow",
            "summary": (
                "The device follows a rail, plane, or bound that should remain spatially legible."
            ),
            "emitted_telemetry": ["zone_slug", "guidance_progress", "constraint_strength"],
            "stability_expectation": "Guidance cues should remain continuous across small spatial steps.",
        },
    ]


def _backend_readiness() -> list[dict[str, object]]:
    """Return the current readiness matrix between primitive families and backend paths."""
    return [
        {
            "backend_slug": "visual-emulator",
            "title": "Visual Pointer Emulator",
            "current_maturity": "scene-debug-only",
            "ready_primitive_families": [
                "rigid_surface_following",
                "button_actuation",
                "guidance_and_bounds",
            ],
            "blocked_primitive_families": [],
            "next_milestone": (
                "Continue mirroring scene contracts visually while native stacks absorb the same "
                "semantic surface."
            ),
            "notes": [
                "No physical force output.",
                "Useful for verifying scene topology, return-flow logic, and control reachability.",
            ],
        },
        {
            "backend_slug": "openhaptics-touch",
            "title": "OpenHaptics Touch Stack",
            "current_maturity": "runtime-loaded-capability-ready",
            "ready_primitive_families": [],
            "blocked_primitive_families": [
                "rigid_surface_following",
                "button_actuation",
                "guidance_and_bounds",
            ],
            "next_milestone": (
                "Map one bounded scene primitive to a conservative force loop using the current "
                "device selector, calibration, and capability diagnostics."
            ),
            "notes": [
                "Current path reaches runtime loading, conservative open attempts, and capability reporting.",
                "Scene-coupled contact and force synthesis are still pending.",
            ],
        },
        {
            "backend_slug": "forcedimension-dhd",
            "title": "Force Dimension DHD Stack",
            "current_maturity": "device-enumeration-ready",
            "ready_primitive_families": [],
            "blocked_primitive_families": [
                "rigid_surface_following",
                "button_actuation",
                "guidance_and_bounds",
            ],
            "next_milestone": (
                "Translate DHD runtime enumeration into one controlled contact primitive with "
                "telemetry and a bounded force envelope."
            ),
            "notes": [
                "Current path can enumerate devices and report runtime state.",
                "It still lacks scene-native contact synthesis and control activation semantics.",
            ],
        },
        {
            "backend_slug": "chai3d-bridge",
            "title": "CHAI3D Bridge Stack",
            "current_maturity": "scaffold-only",
            "ready_primitive_families": [],
            "blocked_primitive_families": [
                "rigid_surface_following",
                "button_actuation",
                "guidance_and_bounds",
            ],
            "next_milestone": (
                "Move from bridge scaffold to a compatibility-oriented runtime that can consume "
                "the same primitive families as the vendor stacks."
            ),
            "notes": [
                "Best candidate for a unified future scene contract bridge.",
                "Still behind the vendor stacks in runtime maturity.",
            ],
        },
    ]


def _mode_contracts() -> list[dict[str, object]]:
    """Return per-mode scene contracts for tactile primitives and return flows."""
    return [
        {
            "mode": "3D Object Explorer",
            "route": "/object-explorer",
            "bridge_goal": (
                "Rigid object exploration with bounded scene controls, material overlays, and "
                "reachable return actions inside the same 3D workspace."
            ),
            "return_contract": {
                "launcher_target": "Object Explorer launcher scene",
                "home_target": "Current launcher page or object session origin",
            },
            "scene_primitives": [
                {
                    "slug": "proxy_object_surface",
                    "primitive_family": "rigid_surface_following",
                    "trigger_type": "continuous_contact",
                    "expected_events": ["contact_enter", "contact_hold", "contact_exit"],
                    "material_channels": [
                        "stiffness",
                        "damping",
                        "friction",
                        "texture_waveform",
                    ],
                    "telemetry_fields": [
                        "contact_state",
                        "surface_normal",
                        "penetration_depth",
                    ],
                },
                {
                    "slug": "launcher_return_button",
                    "primitive_family": "button_actuation",
                    "trigger_type": "threshold_activate",
                    "expected_events": ["contact_enter", "threshold_activate", "contact_exit"],
                    "material_channels": ["spring", "snap-through", "release cue"],
                    "telemetry_fields": ["button_state", "activation_count"],
                },
                {
                    "slug": "material_cycle_button",
                    "primitive_family": "button_actuation",
                    "trigger_type": "threshold_activate",
                    "expected_events": ["contact_enter", "threshold_activate", "contact_exit"],
                    "material_channels": ["spring", "snap-through"],
                    "telemetry_fields": ["button_state", "selected_material_slug"],
                },
            ],
        },
        {
            "mode": "Braille Reader",
            "route": "/braille-reader",
            "bridge_goal": (
                "Stable reading plane with dot relief, segment controls, library navigation, "
                "and orientation guidance inside the same tactile world."
            ),
            "return_contract": {
                "launcher_target": "Braille library launcher",
                "home_target": "Current reading or library page origin",
            },
            "scene_primitives": [
                {
                    "slug": "braille_dot_array",
                    "primitive_family": "guidance_and_bounds",
                    "trigger_type": "continuous_contact",
                    "expected_events": ["contact_enter", "guidance_follow", "contact_exit"],
                    "material_channels": ["edge_ridge", "soft_limit", "micro_relief"],
                    "telemetry_fields": ["cell_row", "cell_column", "dot_mask"],
                },
                {
                    "slug": "reading_plane",
                    "primitive_family": "rigid_surface_following",
                    "trigger_type": "guidance_follow",
                    "expected_events": ["contact_enter", "contact_hold", "guidance_follow"],
                    "material_channels": ["plane_constraint", "damping"],
                    "telemetry_fields": ["contact_state", "plane_zone"],
                },
                {
                    "slug": "segment_and_library_controls",
                    "primitive_family": "button_actuation",
                    "trigger_type": "threshold_activate",
                    "expected_events": ["contact_enter", "threshold_activate", "contact_exit"],
                    "material_channels": ["spring", "snap-through", "release cue"],
                    "telemetry_fields": ["button_state", "target_action"],
                },
            ],
        },
        {
            "mode": "Haptic Desktop",
            "route": "/haptic-desktop",
            "bridge_goal": (
                "Typed tactile tiles, galleries, file-browser entries, and return controls "
                "inside one bounded desktop workspace."
            ),
            "return_contract": {
                "launcher_target": "Desktop workspace launcher",
                "home_target": "Current gallery root or file-browser root",
            },
            "scene_primitives": [
                {
                    "slug": "launcher_and_gallery_tiles",
                    "primitive_family": "button_actuation",
                    "trigger_type": "threshold_activate",
                    "expected_events": ["contact_enter", "threshold_activate", "contact_exit"],
                    "material_channels": ["spring", "threshold", "release cue"],
                    "telemetry_fields": ["tile_kind", "activation_target"],
                },
                {
                    "slug": "file_browser_entries",
                    "primitive_family": "guidance_and_bounds",
                    "trigger_type": "contact_enter",
                    "expected_events": ["contact_enter", "guidance_follow", "contact_exit"],
                    "material_channels": [
                        "edge_ridge",
                        "shape-coded profile",
                        "soft_limit",
                    ],
                    "telemetry_fields": ["entry_kind", "entry_slug", "entry_page"],
                },
                {
                    "slug": "audio_transport_and_return_controls",
                    "primitive_family": "button_actuation",
                    "trigger_type": "threshold_activate",
                    "expected_events": ["contact_enter", "threshold_activate", "contact_exit"],
                    "material_channels": ["spring", "snap-through"],
                    "telemetry_fields": ["button_state", "transport_action", "origin_scene"],
                },
            ],
        },
    ]


def build_haptic_scene_contract() -> dict[str, object]:
    """Return the current scene-to-backend haptic contract baseline."""
    return {
        "summary": (
            "FeelIT translates scene-native tactile controls and surfaces into reusable "
            "primitive families, backend-facing event transitions, and bounded material or "
            "constraint channels before a native device loop can be considered complete."
        ),
        "primitive_families": _primitive_families(),
        "event_contract": _event_contract(),
        "backend_readiness": _backend_readiness(),
        "mode_contracts": _mode_contracts(),
        "safety_contract": [
            {
                "slug": "servo_visual_separation",
                "title": "Servo and visual separation",
                "summary": (
                    "The haptic servo loop must consume reduced contact representations rather "
                    "than arbitrary render meshes."
                ),
            },
            {
                "slug": "force_and_travel_clamps",
                "title": "Force and travel clamps",
                "summary": (
                    "Buttons, guidance rails, and rigid surfaces should stay inside bounded "
                    "travel and force envelopes."
                ),
            },
            {
                "slug": "return_flow_legibility",
                "title": "Return-flow legibility",
                "summary": (
                    "Launcher and home actions must remain spatially reachable and semantically "
                    "consistent across scene changes."
                ),
            },
        ],
    }
