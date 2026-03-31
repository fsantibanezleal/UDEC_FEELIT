"""Tests for the scene-to-backend haptic contract baseline."""

from app.core.haptic_scene_contracts import build_haptic_scene_contract


def test_scene_contract_covers_all_primary_haptic_modes() -> None:
    contract = build_haptic_scene_contract()

    mode_names = {item["mode"] for item in contract["mode_contracts"]}
    assert {"3D Object Explorer", "Braille Reader", "Haptic Desktop"} <= mode_names
    assert len(contract["event_contract"]) >= 5
    assert len(contract["primitive_families"]) >= 3
    assert len(contract["backend_readiness"]) >= 4


def test_scene_contract_describes_backend_primitives_and_telemetry() -> None:
    contract = build_haptic_scene_contract()
    explorer = next(item for item in contract["mode_contracts"] if item["mode"] == "3D Object Explorer")

    primitive_slugs = {item["slug"] for item in explorer["scene_primitives"]}
    assert "proxy_object_surface" in primitive_slugs
    assert "material_cycle_button" in primitive_slugs
    assert all(item["telemetry_fields"] for item in explorer["scene_primitives"])
    assert all(item["expected_events"] for item in explorer["scene_primitives"])


def test_scene_contract_declares_reusable_families_and_backend_readiness() -> None:
    contract = build_haptic_scene_contract()

    family_slugs = {item["slug"] for item in contract["primitive_families"]}
    assert {
        "rigid_surface_following",
        "button_actuation",
        "guidance_and_bounds",
    } <= family_slugs

    backend_slugs = {item["backend_slug"] for item in contract["backend_readiness"]}
    assert {
        "visual-emulator",
        "openhaptics-touch",
        "forcedimension-dhd",
        "chai3d-bridge",
    } <= backend_slugs
    assert all(item["next_milestone"] for item in contract["backend_readiness"])
