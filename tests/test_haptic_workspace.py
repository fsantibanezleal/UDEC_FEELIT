"""Tests for Haptic Desktop workspace descriptors and APIs."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core import haptic_workspace
from app.main import app


def test_demo_workspace_catalog_exposes_bundled_workspace() -> None:
    catalog = haptic_workspace.build_haptic_workspace_catalog()
    demo = next((workspace for workspace in catalog if workspace["slug"] == "feelit_demo_workspace"), None)
    assert demo is not None
    assert demo["is_default"] is True
    assert demo["category_counts"]["models"] >= 3
    assert demo["category_counts"]["texts"] >= 3
    assert demo["category_counts"]["audio"] >= 2


def test_demo_workspace_payload_resolves_bundled_libraries() -> None:
    payload = haptic_workspace.build_haptic_workspace_payload("feelit_demo_workspace")
    assert payload["title"] == "FeelIT Demo Workspace"
    assert any(item["kind"] == "model" for item in payload["libraries"]["models"])
    assert any(item["kind"] == "text" for item in payload["libraries"]["texts"])
    assert any(item["kind"] == "audio" for item in payload["libraries"]["audio"])


def test_demo_workspace_browser_payload_lists_internal_library_entries() -> None:
    payload = haptic_workspace.build_workspace_browser_payload("feelit_demo_workspace")
    entry_titles = {entry["title"] for entry in payload["entries"]}
    assert payload["current_path"] == ""
    assert "audio" in entry_titles
    assert "documents" in entry_titles


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


def test_haptic_workspace_api_returns_demo_workspace_payload_browse_and_text() -> None:
    with TestClient(app) as client:
        detail_response = client.get("/api/haptic-workspaces/feelit_demo_workspace")
        browse_response = client.get("/api/haptic-workspaces/feelit_demo_workspace/browse")
        text_response = client.get(
            "/api/haptic-workspaces/feelit_demo_workspace/text-file",
            params={"path": "documents/alice_in_wonderland.txt", "offset": 0, "max_chars": 400},
        )

    assert detail_response.status_code == 200
    assert browse_response.status_code == 200
    assert text_response.status_code == 200
    assert detail_response.json()["slug"] == "feelit_demo_workspace"
    assert any(entry["title"] == "documents" for entry in browse_response.json()["entries"])
    assert "Alice" in text_response.json()["text"]
