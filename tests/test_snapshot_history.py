"""Tests for the sparse frontend snapshot archive workflow."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.browser_scene_smoke import (
    CaptureSpec,
    archive_snapshot_set,
    build_current_manifest_entries,
    capture_image_name,
    normalize_sparse_history,
    sync_curated_docs_png,
    write_snapshot_manifest,
)

TEST_CAPTURES = (
    CaptureSpec(
        slug="object-explorer",
        route="/object-explorer",
        image_name="frontend_3d_objects.png",
    ),
    CaptureSpec(
        slug="braille-launcher",
        route="/braille-reader",
        image_name="frontend_braille_launcher.png",
    ),
    CaptureSpec(
        slug="braille-reading-world",
        route="/braille-reader",
        image_name="frontend_braille_hapticreader.png",
    ),
)


def write_snapshot(path: Path, payload: bytes) -> None:
    """Create one fake snapshot file with deterministic bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def read_manifest(version_dir: Path) -> dict[str, object]:
    """Load one snapshot manifest JSON document."""
    return json.loads((version_dir / "snapshot_manifest.json").read_text(encoding="utf-8"))


def capture_entry(manifest: dict[str, object], slug: str) -> dict[str, object]:
    """Return one capture entry from a snapshot manifest."""
    routes = manifest["routes"]
    return next(entry for entry in routes if entry["capture_slug"] == slug)


def test_archive_snapshot_set_only_copies_changed_routes(tmp_path: Path) -> None:
    history_root = tmp_path / "history"
    current_dir = tmp_path / "current"

    prior_dir = history_root / "v2.05.005"
    write_snapshot(prior_dir / capture_image_name("frontend_3d_objects.png"), b"object-v1")
    write_snapshot(prior_dir / capture_image_name("frontend_braille_launcher.png"), b"braille-launcher-v1")
    write_snapshot(
        prior_dir / capture_image_name("frontend_braille_hapticreader.png"),
        b"braille-reading-v1",
    )

    write_snapshot(current_dir / capture_image_name("frontend_3d_objects.png"), b"object-v1")
    write_snapshot(
        current_dir / capture_image_name("frontend_braille_launcher.png"),
        b"braille-launcher-v1",
    )
    write_snapshot(
        current_dir / capture_image_name("frontend_braille_hapticreader.png"),
        b"braille-reading-v2",
    )

    archive_dir = archive_snapshot_set(
        current_dir,
        "2.05.006",
        captures=TEST_CAPTURES,
        history_root=history_root,
    )

    assert not (archive_dir / "frontend_3d_objects.png").exists()
    assert not (archive_dir / "frontend_braille_launcher.png").exists()
    assert (archive_dir / "frontend_braille_hapticreader.png").exists()

    manifest = read_manifest(archive_dir)
    object_entry = capture_entry(manifest, "object-explorer")
    braille_launcher_entry = capture_entry(manifest, "braille-launcher")
    braille_reading_entry = capture_entry(manifest, "braille-reading-world")

    assert manifest["history_policy"] == "sparse_changed_routes_only"
    assert manifest["changed_routes"] == ["/braille-reader"]
    assert object_entry["archived"] is False
    assert object_entry["visual_source_version"] == "2.05.005"
    assert braille_launcher_entry["archived"] is False
    assert braille_launcher_entry["visual_source_version"] == "2.05.005"
    assert braille_reading_entry["archived"] is True
    assert braille_reading_entry["visual_source_version"] == "2.05.006"


def test_normalize_sparse_history_prunes_redundant_route_images(tmp_path: Path) -> None:
    history_root = tmp_path / "history"

    first_dir = history_root / "v2.05.004"
    second_dir = history_root / "v2.05.005"

    write_snapshot(first_dir / capture_image_name("frontend_3d_objects.png"), b"object-v1")
    write_snapshot(first_dir / capture_image_name("frontend_braille_launcher.png"), b"braille-launcher-v1")
    write_snapshot(
        first_dir / capture_image_name("frontend_braille_hapticreader.png"),
        b"braille-reading-v1",
    )
    write_snapshot(second_dir / capture_image_name("frontend_3d_objects.png"), b"object-v1")
    write_snapshot(
        second_dir / capture_image_name("frontend_braille_launcher.png"),
        b"braille-launcher-v1",
    )
    write_snapshot(
        second_dir / capture_image_name("frontend_braille_hapticreader.png"),
        b"braille-reading-v2",
    )

    normalize_sparse_history(history_root, TEST_CAPTURES)

    assert (first_dir / "frontend_3d_objects.png").exists()
    assert (first_dir / "frontend_braille_launcher.png").exists()
    assert (first_dir / "frontend_braille_hapticreader.png").exists()
    assert not (second_dir / "frontend_3d_objects.png").exists()
    assert not (second_dir / "frontend_braille_launcher.png").exists()
    assert (second_dir / "frontend_braille_hapticreader.png").exists()

    second_manifest = read_manifest(second_dir)
    object_entry = capture_entry(second_manifest, "object-explorer")
    braille_launcher_entry = capture_entry(second_manifest, "braille-launcher")
    braille_reading_entry = capture_entry(second_manifest, "braille-reading-world")

    assert second_manifest["history_policy"] == "sparse_changed_routes_only"
    assert second_manifest["changed_routes"] == ["/braille-reader"]
    assert object_entry["archived"] is False
    assert object_entry["visual_source_version"] == "2.05.004"
    assert braille_launcher_entry["archived"] is False
    assert braille_launcher_entry["visual_source_version"] == "2.05.004"
    assert braille_reading_entry["archived"] is True
    assert braille_reading_entry["visual_source_version"] == "2.05.005"


def test_write_snapshot_manifest_preserves_existing_timestamp_when_content_is_unchanged(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "current"
    routes = build_current_manifest_entries(TEST_CAPTURES)

    write_snapshot_manifest(
        target_dir,
        base_url="local_smoke_capture",
        captures=TEST_CAPTURES,
        version="2.06.002",
        route_entries=routes,
    )
    manifest_path = target_dir / "snapshot_manifest.json"
    first_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    write_snapshot_manifest(
        target_dir,
        base_url="local_smoke_capture",
        captures=TEST_CAPTURES,
        version="2.06.002",
        route_entries=routes,
    )
    second_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert second_manifest == first_manifest


def test_sync_curated_docs_png_copies_the_curated_braille_pair(tmp_path: Path) -> None:
    current_dir = tmp_path / "current"
    docs_dir = tmp_path / "docs_png"

    write_snapshot(current_dir / "frontend_braille_launcher.png", b"launcher")
    write_snapshot(current_dir / "frontend_braille_hapticreader.png", b"reading")

    sync_curated_docs_png(current_dir, captures=TEST_CAPTURES, docs_dir=docs_dir)

    assert (docs_dir / "frontend_braille_launcher.png").read_bytes() == b"launcher"
    assert (docs_dir / "frontend_braille_hapticreader.png").read_bytes() == b"reading"
