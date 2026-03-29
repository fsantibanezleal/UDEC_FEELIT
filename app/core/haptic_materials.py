"""Canonical haptic material profiles for FeelIT."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HapticMaterialProfile:
    """Describe a material profile that current desktop haptics can plausibly approximate."""

    slug: str
    title: str
    category: str
    summary: str
    stiffness_n_per_mm: float
    damping: float
    static_friction: float
    dynamic_friction: float
    texture_amplitude_mm: float
    texture_spacing_mm: float
    vibration_hz: int
    viscosity: float
    visual_color: str
    visual_roughness: float
    visual_metalness: float
    capability_note: str


MATERIAL_PROFILES: tuple[HapticMaterialProfile, ...] = (
    HapticMaterialProfile(
        slug="polished_metal",
        title="Polished Metal",
        category="rigid_surface",
        summary="High stiffness and low damping with a smooth low-friction contact feel.",
        stiffness_n_per_mm=2.6,
        damping=0.08,
        static_friction=0.12,
        dynamic_friction=0.08,
        texture_amplitude_mm=0.02,
        texture_spacing_mm=1.8,
        vibration_hz=40,
        viscosity=0.04,
        visual_color="#b7c6d8",
        visual_roughness=0.18,
        visual_metalness=0.95,
        capability_note=(
            "Maps well to current haptic devices because rigid surfaces, friction contrast, "
            "and fine vibration cues are readily approximated."
        ),
    ),
    HapticMaterialProfile(
        slug="carved_stone",
        title="Carved Stone",
        category="rigid_textured",
        summary="Rigid contact with higher friction and coarse surface variation.",
        stiffness_n_per_mm=2.9,
        damping=0.12,
        static_friction=0.36,
        dynamic_friction=0.28,
        texture_amplitude_mm=0.18,
        texture_spacing_mm=3.4,
        vibration_hz=55,
        viscosity=0.05,
        visual_color="#8b949e",
        visual_roughness=0.86,
        visual_metalness=0.04,
        capability_note=(
            "Rigid stone-like contact is achievable through high stiffness plus coarse "
            "periodic texture and elevated friction."
        ),
    ),
    HapticMaterialProfile(
        slug="unfinished_wood",
        title="Unfinished Wood",
        category="anisotropic_texture",
        summary="Medium-high stiffness with directional grain-like roughness.",
        stiffness_n_per_mm=2.0,
        damping=0.14,
        static_friction=0.31,
        dynamic_friction=0.22,
        texture_amplitude_mm=0.09,
        texture_spacing_mm=2.6,
        vibration_hz=70,
        viscosity=0.06,
        visual_color="#9b7b56",
        visual_roughness=0.72,
        visual_metalness=0.02,
        capability_note=(
            "Wood-like surfaces are usually approximated with medium stiffness and "
            "directional texture rather than full material simulation."
        ),
    ),
    HapticMaterialProfile(
        slug="rubber_pad",
        title="Rubber Pad",
        category="compliant_surface",
        summary="Moderate stiffness, high damping, and high friction for grippy compliant contact.",
        stiffness_n_per_mm=1.2,
        damping=0.34,
        static_friction=0.58,
        dynamic_friction=0.46,
        texture_amplitude_mm=0.04,
        texture_spacing_mm=2.2,
        vibration_hz=35,
        viscosity=0.16,
        visual_color="#2f3640",
        visual_roughness=0.88,
        visual_metalness=0.01,
        capability_note=(
            "Current devices can suggest rubber through compliance and damping, although "
            "deep bulk deformation remains an approximation."
        ),
    ),
    HapticMaterialProfile(
        slug="foam_block",
        title="Foam Block",
        category="soft_surface",
        summary="Low stiffness with heavy damping and muted texture for soft contact.",
        stiffness_n_per_mm=0.45,
        damping=0.42,
        static_friction=0.22,
        dynamic_friction=0.16,
        texture_amplitude_mm=0.03,
        texture_spacing_mm=4.2,
        vibration_hz=18,
        viscosity=0.24,
        visual_color="#d7c39f",
        visual_roughness=0.58,
        visual_metalness=0.0,
        capability_note=(
            "Soft foam is only partially representable with desktop haptics; the practical "
            "approximation relies on reduced stiffness and stronger damping."
        ),
    ),
    HapticMaterialProfile(
        slug="textured_polymer",
        title="Textured Polymer",
        category="engineered_surface",
        summary="Stable medium stiffness with crisp microtexture and moderate friction.",
        stiffness_n_per_mm=1.7,
        damping=0.11,
        static_friction=0.26,
        dynamic_friction=0.19,
        texture_amplitude_mm=0.07,
        texture_spacing_mm=1.4,
        vibration_hz=90,
        viscosity=0.08,
        visual_color="#3b82f6",
        visual_roughness=0.46,
        visual_metalness=0.08,
        capability_note=(
            "Microtextured polymer-like surfaces are well aligned with the simple periodic "
            "texture and friction cues supported by current haptic stacks."
        ),
    ),
)


def build_material_catalog() -> list[dict[str, object]]:
    """Return the public material catalog."""
    return [asdict(profile) for profile in MATERIAL_PROFILES]

