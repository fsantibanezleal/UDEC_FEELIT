"""Static design baselines for haptic contact, force rendering, and material cues."""

from __future__ import annotations

from app.core.haptic_materials import build_material_catalog


def build_haptic_contact_design() -> dict[str, object]:
    """Return the current design baseline for the native haptic interaction loop."""
    return {
        "servo_loop_target_hz": 1000,
        "visual_loop_target_hz": 60,
        "collision_strategy": {
            "title": "Proxy-first collision and contact model",
            "summary": (
                "The future native backend should not drive the haptic servo loop directly "
                "against arbitrary raw render meshes. FeelIT should favor simplified haptic "
                "proxy geometry, bounded surfaces, and explicit interaction primitives."
            ),
            "pipeline": [
                {
                    "step": "Asset preprocessing",
                    "summary": (
                        "Convert imported or curated geometry into bounded haptic-friendly "
                        "contact representations before the device loop consumes them."
                    ),
                },
                {
                    "step": "Haptic scene reduction",
                    "summary": (
                        "Keep a separate collision scene for the servo loop with simplified "
                        "triangles, convex parts, planes, rails, and tactile buttons."
                    ),
                },
                {
                    "step": "Contact solve",
                    "summary": (
                        "Resolve surface following, penetration depth, boundary constraints, "
                        "and button thresholds at the high-frequency haptic update rate."
                    ),
                },
                {
                    "step": "Material response synthesis",
                    "summary": (
                        "Map stiffness, damping, friction, texture, and vibration cues into "
                        "force outputs that the active hardware can reproduce stably."
                    ),
                },
                {
                    "step": "Visual and telemetry mirror",
                    "summary": (
                        "Keep the browser scene as a debug mirror of the haptic world so "
                        "developers can inspect bounds, contact zones, and state transitions."
                    ),
                },
            ],
        },
        "interaction_primitives": [
            {
                "slug": "rigid_surface_following",
                "title": "Rigid surface following",
                "used_by": ["3D Object Explorer", "Haptic Desktop tiles", "Braille base"],
                "force_channels": ["normal_force", "stiffness", "damping"],
            },
            {
                "slug": "microtexture_modulation",
                "title": "Microtexture modulation",
                "used_by": ["3D materials", "Document-like surfaces"],
                "force_channels": ["friction", "vibration", "texture_waveform"],
            },
            {
                "slug": "button_actuation",
                "title": "Button actuation and confirmation",
                "used_by": ["Launcher controls", "Braille navigation", "Desktop controls"],
                "force_channels": ["spring", "snap-through", "threshold", "release cue"],
            },
            {
                "slug": "guidance_and_bounds",
                "title": "Guidance rails and workspace bounds",
                "used_by": ["Braille orientation", "Desktop roots", "Scene boundaries"],
                "force_channels": ["plane_constraint", "edge_ridge", "soft_limit"],
            },
        ],
        "mode_mappings": [
            {
                "mode": "3D Object Explorer",
                "contact_model": "Rigid object contact with proxy meshes and material overlays.",
                "primary_primitives": ["rigid_surface_following", "microtexture_modulation"],
            },
            {
                "mode": "Braille Reader",
                "contact_model": "Raised-dot array over a stable reading plane with tactile controls.",
                "primary_primitives": ["guidance_and_bounds", "button_actuation"],
            },
            {
                "mode": "Haptic Desktop",
                "contact_model": (
                    "Typed interactive tiles, gallery items, file browser objects, and "
                    "return controls embedded in a bounded workspace."
                ),
                "primary_primitives": ["button_actuation", "guidance_and_bounds"],
            },
        ],
    }


def build_haptic_material_rendering_matrix() -> list[dict[str, object]]:
    """Map the current material catalog to feasible haptic-rendering strategies."""
    matrix: list[dict[str, object]] = []
    for material in build_material_catalog():
        category = str(material["category"])
        rendering_channels = ["stiffness", "damping", "friction"]
        if float(material["texture_amplitude_mm"]) > 0.02:
            rendering_channels.append("texture_waveform")
        if int(material["vibration_hz"]) > 0:
            rendering_channels.append("vibration")

        if category in {"soft_surface", "compliant_surface"}:
            practical_model = "compliance_approximation"
            confidence = "partial"
        elif category in {"rigid_textured", "anisotropic_texture", "engineered_surface"}:
            practical_model = "rigid_texture_overlay"
            confidence = "strong"
        else:
            practical_model = "rigid_surface_response"
            confidence = "strong"

        matrix.append(
            {
                "slug": material["slug"],
                "title": material["title"],
                "category": category,
                "practical_model": practical_model,
                "confidence": confidence,
                "rendering_channels": rendering_channels,
                "summary": material["summary"],
                "capability_note": material["capability_note"],
            }
        )
    return matrix
