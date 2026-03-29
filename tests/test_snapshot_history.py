"""Tests for the sparse frontend snapshot archive workflow."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.browser_scene_smoke import (
    SceneSpec,
    archive_snapshot_set,
    build_current_manifest_entries,
    normalize_sparse_history,
    snapshot_image_name,
    write_snapshot_manifest,
)

TEST_ROUTES = (
    SceneSpec(route="/object-explorer", canvas_selector="#object-canvas", min_unique_colors=1),
    SceneSpec(route="/braille-reader", canvas_selector="#braille-canvas", min_unique_colors=1),
)


def write_snapshot(path: Path, payload: bytes) -> None:
    """Create one fake snapshot file with deterministic bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def read_manifest(version_dir: Path) -> dict[str, object]:
    """Load one snapshot manifest JSON document."""
    return json.loads((version_dir / "snapshot_manifest.json").read_text(encoding="utf-8"))


def route_entry(manifest: dict[str, object], route: str) -> dict[str, object]:
    """Return one route entry from a snapshot manifest."""
    routes = manifest["routes"]
    return next(entry for entry in routes if entry["route"] == route)


def test_archive_snapshot_set_only_copies_changed_routes(tmp_path: Path) -> None:
    history_root = tmp_path / "history"
    current_dir = tmp_path / "current"

    prior_dir = history_root / "v2.05.005"
    write_snapshot(prior_dir / snapshot_image_name("/object-explorer"), b"object-v1")
    write_snapshot(prior_dir / snapshot_image_name("/braille-reader"), b"braille-v1")

    write_snapshot(current_dir / snapshot_image_name("/object-explorer"), b"object-v1")
    write_snapshot(current_dir / snapshot_image_name("/braille-reader"), b"braille-v2")

    archive_dir = archive_snapshot_set(
        current_dir,
        "2.05.006",
        routes=TEST_ROUTES,
        history_root=history_root,
    )

    assert not (archive_dir / "object_explorer.png").exists()
    assert (archive_dir / "braille_reader.png").exists()

    manifest = read_manifest(archive_dir)
    object_entry = route_entry(manifest, "/object-explorer")
    braille_entry = route_entry(manifest, "/braille-reader")

    assert manifest["history_policy"] == "sparse_changed_routes_only"
    assert manifest["changed_routes"] == ["/braille-reader"]
    assert object_entry["archived"] is False
    assert object_entry["visual_source_version"] == "2.05.005"
    assert braille_entry["archived"] is True
    assert braille_entry["visual_source_version"] == "2.05.006"


def test_normalize_sparse_history_prunes_redundant_route_images(tmp_path: Path) -> None:
    history_root = tmp_path / "history"

    first_dir = history_root / "v2.05.004"
    second_dir = history_root / "v2.05.005"

    write_snapshot(first_dir / snapshot_image_name("/object-explorer"), b"object-v1")
    write_snapshot(first_dir / snapshot_image_name("/braille-reader"), b"braille-v1")
    write_snapshot(second_dir / snapshot_image_name("/object-explorer"), b"object-v1")
    write_snapshot(second_dir / snapshot_image_name("/braille-reader"), b"braille-v2")

    normalize_sparse_history(history_root, TEST_ROUTES)

    assert (first_dir / "object_explorer.png").exists()
    assert (first_dir / "braille_reader.png").exists()
    assert not (second_dir / "object_explorer.png").exists()
    assert (second_dir / "braille_reader.png").exists()

    second_manifest = read_manifest(second_dir)
    object_entry = route_entry(second_manifest, "/object-explorer")
    braille_entry = route_entry(second_manifest, "/braille-reader")

    assert second_manifest["history_policy"] == "sparse_changed_routes_only"
    assert second_manifest["changed_routes"] == ["/braille-reader"]
    assert object_entry["archived"] is False
    assert object_entry["visual_source_version"] == "2.05.004"
    assert braille_entry["archived"] is True
    assert braille_entry["visual_source_version"] == "2.05.005"


def test_write_snapshot_manifest_preserves_existing_timestamp_when_content_is_unchanged(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "current"
    routes = build_current_manifest_entries(TEST_ROUTES)

    write_snapshot_manifest(
        target_dir,
        base_url="local_smoke_capture",
        routes=TEST_ROUTES,
        version="2.06.002",
        route_entries=routes,
    )
    manifest_path = target_dir / "snapshot_manifest.json"
    first_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    write_snapshot_manifest(
        target_dir,
        base_url="local_smoke_capture",
        routes=TEST_ROUTES,
        version="2.06.002",
        route_entries=routes,
    )
    second_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert second_manifest == first_manifest
