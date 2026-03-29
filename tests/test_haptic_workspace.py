"""Tests for Haptic Desktop workspace descriptors and APIs."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.demo_assets import build_demo_model_catalog
from app.core import haptic_workspace
from app.core.library_assets import build_audio_catalog, build_document_catalog, build_text_payload_from_path
from app.main import app


def test_demo_workspace_catalog_exposes_bundled_workspace() -> None:
    catalog = haptic_workspace.build_haptic_workspace_catalog()
    demo = next((workspace for workspace in catalog if workspace["slug"] == "feelit_demo_workspace"), None)
    assert demo is not None
    assert demo["is_default"] is True
    assert demo["category_counts"]["models"] == len(build_demo_model_catalog())
    assert demo["category_counts"]["texts"] == len(build_document_catalog())
    assert demo["category_counts"]["audio"] == len(build_audio_catalog())


def test_demo_workspace_payload_resolves_bundled_libraries() -> None:
    payload = haptic_workspace.build_haptic_workspace_payload("feelit_demo_workspace")
    assert payload["title"] == "FeelIT Demo Workspace"
    assert any(item["kind"] == "model" for item in payload["libraries"]["models"])
    assert any(item["kind"] == "text" for item in payload["libraries"]["texts"])
    assert any(item["kind"] == "audio" for item in payload["libraries"]["audio"])
    assert all(item["open_mode"] == "open-model" for item in payload["libraries"]["models"])
    assert all(item["shape_key"] == "polyhedral_model_tile" for item in payload["libraries"]["models"])
    assert all(item["open_mode"] == "open-text" for item in payload["libraries"]["texts"])
    assert all(item["shape_key"] == "braille_document_tile" for item in payload["libraries"]["texts"])
    assert all(item["open_mode"] == "open-audio" for item in payload["libraries"]["audio"])
    assert all(item["shape_key"] == "speaker_wave_tile" for item in payload["libraries"]["audio"])


def test_demo_workspace_payload_covers_all_bundled_assets() -> None:
    payload = haptic_workspace.build_haptic_workspace_payload("feelit_demo_workspace")

    assert {item["source"]["ref"] for item in payload["libraries"]["models"]} == {
        item["slug"] for item in build_demo_model_catalog()
    }
    assert {item["source"]["ref"] for item in payload["libraries"]["texts"]} == {
        item["slug"] for item in build_document_catalog()
    }
    assert {item["source"]["ref"] for item in payload["libraries"]["audio"]} == {
        item["slug"] for item in build_audio_catalog()
    }


def test_demo_workspace_browser_payload_lists_internal_library_entries() -> None:
    payload = haptic_workspace.build_workspace_browser_payload("feelit_demo_workspace")
    entry_titles = {entry["title"] for entry in payload["entries"]}
    assert payload["current_path"] == ""
    assert "library" in entry_titles
    assert "models" in entry_titles
    library_entry = next(entry for entry in payload["entries"] if entry["title"] == "library")
    assert library_entry["kind"] == "directory"
    assert library_entry["open_mode"] == "file-browser"
    assert library_entry["shape_key"] == "folder_tile"


def test_demo_workspace_browser_payload_maps_text_files_to_braille_scene() -> None:
    payload = haptic_workspace.build_workspace_browser_payload("feelit_demo_workspace", "library/documents")
    text_entry = next(entry for entry in payload["entries"] if entry["title"] == "alice_in_wonderland.txt")
    assert text_entry["kind"] == "text"
    assert text_entry["open_mode"] == "open-text"
    assert text_entry["shape_key"] == "braille_document_tile"
    assert text_entry["open_label"] == "Open in the Braille reading scene"


def test_create_workspace_file_auto_populates_supported_assets(tmp_path, monkeypatch) -> None:
    registry_file = tmp_path / "registry.json"
    monkeypatch.setattr(haptic_workspace, "REGISTRY_FILE", registry_file)

    workspace_root = tmp_path / "workspace_root"
    workspace_root.mkdir()
    (workspace_root / "sample_model.obj").write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n", encoding="utf-8")
    (workspace_root / "sample_text.txt").write_text("Accessible tactile reading sample.", encoding="utf-8")
    (workspace_root / "sample_audio.wav").write_bytes(b"RIFFdemoWAVEfmt ")

    record = haptic_workspace.create_workspace_file(
        title="My Workspace",
        slug="my_workspace",
        description="Temporary workspace for automated tests.",
        root_path=str(workspace_root),
        auto_populate=True,
    )

    descriptor_path = workspace_root / "my_workspace.haptic_workspace.json"
    assert descriptor_path.exists()
    assert record["slug"] == "my_workspace"

    payload = haptic_workspace.build_haptic_workspace_payload("my_workspace")
    assert any(item["kind"] == "model" for item in payload["libraries"]["models"])
    assert any(item["kind"] == "text" for item in payload["libraries"]["texts"])
    assert any(item["kind"] == "audio" for item in payload["libraries"]["audio"])


def test_workspace_auto_populate_generates_collision_safe_library_slugs(tmp_path, monkeypatch) -> None:
    registry_file = tmp_path / "registry.json"
    monkeypatch.setattr(haptic_workspace, "REGISTRY_FILE", registry_file)

    workspace_root = tmp_path / "workspace_root"
    workspace_root.mkdir()
    (workspace_root / "a-b.txt").write_text("one", encoding="utf-8")
    (workspace_root / "a_b.txt").write_text("two", encoding="utf-8")

    haptic_workspace.create_workspace_file(
        title="Collision Safe Workspace",
        slug="collision_safe_workspace",
        description="Temporary workspace for collision testing.",
        root_path=str(workspace_root),
        auto_populate=True,
    )

    workspace_payload = haptic_workspace.build_haptic_workspace_payload("collision_safe_workspace")
    browser_payload = haptic_workspace.build_workspace_browser_payload("collision_safe_workspace")

    library_slugs = [item["slug"] for item in workspace_payload["libraries"]["texts"]]
    browser_slugs = [
        entry["slug"]
        for entry in browser_payload["entries"]
        if entry["title"] in {"a-b.txt", "a_b.txt"}
    ]

    assert len(library_slugs) == len(set(library_slugs))
    assert len(browser_slugs) == len(set(browser_slugs))


def test_workspace_text_payload_uses_collision_safe_slug_seed(tmp_path) -> None:
    document_a = tmp_path / "a" / "sample.txt"
    document_b = tmp_path / "b" / "sample.txt"
    document_a.parent.mkdir()
    document_b.parent.mkdir()
    document_a.write_text("hello", encoding="utf-8")
    document_b.write_text("world", encoding="utf-8")

    payload_a = build_text_payload_from_path(
        document_a,
        title="Sample A",
        source_name="Workspace file",
        source_url="a/sample.txt",
        slug_seed="a/sample.txt",
    )
    payload_b = build_text_payload_from_path(
        document_b,
        title="Sample B",
        source_name="Workspace file",
        source_url="b/sample.txt",
        slug_seed="b/sample.txt",
    )

    assert payload_a["slug"] != payload_b["slug"]


def test_haptic_workspace_create_and_register_endpoints_use_external_registry(tmp_path, monkeypatch) -> None:
    registry_file = tmp_path / "registry.json"
    monkeypatch.setattr(haptic_workspace, "REGISTRY_FILE", registry_file)

    created_root = tmp_path / "created_workspace"
    created_root.mkdir()
    (created_root / "scene.obj").write_text("v 0 0 0\nv 0 1 0\nv 1 0 0\nf 1 2 3\n", encoding="utf-8")
    (created_root / "notes.txt").write_text("Braille library note.", encoding="utf-8")

    existing_root = tmp_path / "existing_workspace"
    existing_root.mkdir()
    descriptor_path = existing_root / "registered_workspace.haptic_workspace.json"
    descriptor_path.write_text(
        json.dumps(
            {
                "format": haptic_workspace.WORKSPACE_FORMAT,
                "format_version": 1,
                "slug": "registered_workspace",
                "title": "Registered Workspace",
                "description": "Existing descriptor file for API registration.",
                "is_default": False,
                "content_root": {"mode": "absolute", "path": str(existing_root)},
                "file_browser_root": {"mode": "absolute", "path": str(existing_root)},
                "libraries": {"models": [], "texts": [], "audio": []},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with TestClient(app) as client:
        create_response = client.post(
            "/api/haptic-workspaces/create",
            json={
                "title": "Created Workspace",
                "slug": "created_workspace",
                "description": "Workspace created from an external root.",
                "root_path": str(created_root),
                "auto_populate": True,
            },
        )
        register_response = client.post(
            "/api/haptic-workspaces/register",
            json={"workspace_file_path": str(descriptor_path)},
        )
        catalog_response = client.get("/api/haptic-workspaces")

    assert create_response.status_code == 200
    assert create_response.json()["workspace"]["slug"] == "created_workspace"
    assert register_response.status_code == 200
    assert register_response.json()["workspace"]["slug"] == "registered_workspace"
    assert catalog_response.status_code == 200
    payload = catalog_response.json()
    assert any(workspace["slug"] == "created_workspace" for workspace in payload["workspaces"])
    assert any(workspace["slug"] == "registered_workspace" for workspace in payload["workspaces"])


def test_workspace_manager_payload_surfaces_invalid_registered_descriptors(tmp_path, monkeypatch) -> None:
    registry_file = tmp_path / "registry.json"
    monkeypatch.setattr(haptic_workspace, "REGISTRY_FILE", registry_file)

    valid_root = tmp_path / "valid_workspace"
    valid_root.mkdir()
    valid_descriptor = valid_root / "valid_workspace.haptic_workspace.json"
    valid_descriptor.write_text(
        json.dumps(
            {
                "format": haptic_workspace.WORKSPACE_FORMAT,
                "format_version": 1,
                "slug": "valid_workspace",
                "title": "Valid Workspace",
                "description": "",
                "is_default": False,
                "content_root": {"mode": "absolute", "path": str(valid_root)},
                "file_browser_root": {"mode": "absolute", "path": str(valid_root)},
                "libraries": {"models": [], "texts": [], "audio": []},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    invalid_root = tmp_path / "invalid_workspace"
    invalid_root.mkdir()
    invalid_descriptor = invalid_root / "invalid_workspace.haptic_workspace.json"
    invalid_descriptor.write_text('{"format":"broken"}', encoding="utf-8")
    missing_descriptor = tmp_path / "missing_workspace.haptic_workspace.json"

    registry_file.write_text(
        json.dumps(
            {
                "workspace_files": [
                    str(valid_descriptor),
                    str(invalid_descriptor),
                    str(missing_descriptor),
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = haptic_workspace.build_workspace_manager_payload()

    assert any(workspace["slug"] == "valid_workspace" for workspace in payload["workspaces"])
    assert len(payload["invalid_workspaces"]) == 2
    assert {entry["error_code"] for entry in payload["invalid_workspaces"]} == {
        "invalid_descriptor",
        "missing_file",
    }


def test_haptic_workspace_api_returns_demo_workspace_payload_browse_and_text() -> None:
    with TestClient(app) as client:
        detail_response = client.get("/api/haptic-workspaces/feelit_demo_workspace")
        browse_response = client.get("/api/haptic-workspaces/feelit_demo_workspace/browse")
        text_response = client.get(
            "/api/haptic-workspaces/feelit_demo_workspace/text-file",
            params={"path": "library/documents/alice_in_wonderland.txt", "offset": 0, "max_chars": 400},
        )

    assert detail_response.status_code == 200
    assert browse_response.status_code == 200
    assert text_response.status_code == 200
    assert detail_response.json()["slug"] == "feelit_demo_workspace"
    assert any(entry["title"] == "library" for entry in browse_response.json()["entries"])
    assert "Alice" in text_response.json()["text"]


def test_detect_entry_kind_maps_supported_file_types_to_modes(tmp_path) -> None:
    model_path = tmp_path / "shape.obj"
    model_path.write_text("v 0 0 0\n", encoding="utf-8")
    text_path = tmp_path / "notes.md"
    text_path.write_text("# sample", encoding="utf-8")
    audio_path = tmp_path / "clip.ogg"
    audio_path.write_bytes(b"OggS")
    unsupported_path = tmp_path / "blob.bin"
    unsupported_path.write_bytes(b"\x00\x01")
    folder_path = tmp_path / "folder"
    folder_path.mkdir()

    assert haptic_workspace.detect_entry_kind(folder_path) == "directory"
    assert haptic_workspace.build_kind_contract("directory")["open_mode"] == "file-browser"
    assert haptic_workspace.detect_entry_kind(model_path) == "model"
    assert haptic_workspace.build_kind_contract("model")["open_mode"] == "open-model"
    assert haptic_workspace.detect_entry_kind(text_path) == "text"
    assert haptic_workspace.build_kind_contract("text")["open_mode"] == "open-text"
    assert haptic_workspace.detect_entry_kind(audio_path) == "audio"
    assert haptic_workspace.build_kind_contract("audio")["open_mode"] == "open-audio"
    assert haptic_workspace.detect_entry_kind(unsupported_path) == "unsupported"
    assert haptic_workspace.build_kind_contract("unsupported")["open_mode"] == "unsupported"
