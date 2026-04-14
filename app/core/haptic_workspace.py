"""Workspace descriptors and filesystem services for the Haptic Desktop."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any

from app.core.demo_assets import build_demo_model_catalog
from app.core.library_assets import (
    build_audio_catalog,
    build_document_catalog,
    build_text_payload_from_path,
)

APP_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = APP_DIR / "static"
WORKSPACES_DIR = STATIC_DIR / "assets" / "workspaces"
DEMO_WORKSPACE_FILE = WORKSPACES_DIR / "feelit_demo.haptic_workspace.json"
WORKSPACE_FORMAT = "feelit_haptic_workspace"
WORKSPACE_SUFFIX = ".haptic_workspace.json"
SUPPORTED_MODEL_SUFFIXES = {".obj", ".stl", ".gltf", ".glb"}
SUPPORTED_TEXT_SUFFIXES = {".txt", ".html", ".htm", ".epub", ".md"}
SUPPORTED_AUDIO_SUFFIXES = {".mp3", ".wav", ".ogg", ".m4a"}
DEFAULT_SEGMENT_CHARS = 1200
DEFAULT_FILE_BROWSER_PAGE_SIZE = 6
MAX_FILE_BROWSER_PAGE_SIZE = 24
KIND_LABELS = {
    "directory": "Folder",
    "model": "3D Model",
    "text": "Text",
    "audio": "Audio",
    "unsupported": "Unsupported file",
}
KIND_SHAPE_KEYS = {
    "directory": "folder_tile",
    "model": "polyhedral_model_tile",
    "text": "braille_document_tile",
    "audio": "speaker_wave_tile",
    "unsupported": "blocked_file_tile",
}
KIND_OPEN_MODES = {
    "directory": "file-browser",
    "model": "open-model",
    "text": "open-text",
    "audio": "open-audio",
    "unsupported": "unsupported",
}
KIND_OPEN_LABELS = {
    "directory": "Open folder in the workspace file browser",
    "model": "Open in the 3D model scene",
    "text": "Open in the Braille reading scene",
    "audio": "Open in the audio transport scene",
    "unsupported": "Inspect unsupported file details",
}
MODEL_FORMAT_LABELS = {
    "obj": "OBJ",
    "stl": "STL",
    "gltf": "glTF",
    "glb": "GLB",
}


def _display_label_from_path(path: Path | str) -> str:
    """Return a safe user-facing label derived from one filesystem path."""
    return Path(path).name or str(path)


def _registry_key_for_path(path: Path | str) -> str:
    """Return one opaque stable key for a registered workspace file path."""
    normalized = str(Path(path).expanduser().resolve()).lower()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]


def local_app_state_dir() -> Path:
    """Return the local writable directory used for user-scoped FeelIT state."""
    if os.name == "nt":
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / "FeelIT"
    return Path.home() / ".feelit"


REGISTRY_FILE = local_app_state_dir() / "haptic_workspace_registry.json"


def _slugify(value: str) -> str:
    """Normalize a user-facing name into a filesystem-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "workspace"


def _stable_slug(value: str, *, prefix: str | None = None) -> str:
    """Return a collision-resistant slug derived from one source identity."""
    normalized = _slugify(value)
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    parts = [part for part in (prefix, normalized, digest) if part]
    return "_".join(parts)


def _ensure_registry_file() -> None:
    """Create the local workspace registry file when it does not exist yet."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_FILE.exists():
        REGISTRY_FILE.write_text(json.dumps({"workspace_files": []}, indent=2), encoding="utf-8")


def _load_registry_payload() -> dict[str, Any]:
    """Return the current local registry payload."""
    _ensure_registry_file()
    payload = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "workspace_files" not in payload:
        payload = {"workspace_files": []}
    return payload


def _save_registry_payload(payload: dict[str, Any]) -> None:
    """Persist the local registry payload."""
    _ensure_registry_file()
    REGISTRY_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _registered_workspace_paths() -> list[Path]:
    """Return the resolved registered workspace descriptor paths from the local registry."""
    payload = _load_registry_payload()
    return [Path(item).expanduser().resolve() for item in payload.get("workspace_files", [])]


def _registry_path_by_key(registry_key: str) -> Path:
    """Resolve one opaque registry key back into the registered workspace path."""
    for path in _registered_workspace_paths():
        if _registry_key_for_path(path) == registry_key:
            return path
    raise KeyError(registry_key)


def _resolve_location(descriptor_path: Path, location: dict[str, Any]) -> Path:
    """Resolve a descriptor location object into an absolute filesystem path."""
    mode = location.get("mode")
    raw_path = location.get("path", "")
    if not raw_path:
        raise ValueError("Workspace location path is required.")

    if mode == "absolute":
        return Path(raw_path).expanduser().resolve()
    if mode == "workspace_relative":
        return (descriptor_path.parent / raw_path).resolve()
    if mode == "app_static_relative":
        return (STATIC_DIR / raw_path).resolve()
    raise ValueError(f"Unsupported workspace location mode: {mode}")


def _normalize_relative_path(relative_path: str) -> str:
    """Normalize a client relative path into a safe POSIX-like representation."""
    if not relative_path:
        return ""
    cleaned = relative_path.replace("\\", "/").strip("/")
    path = PurePosixPath(cleaned)
    if any(part in {"..", "."} for part in path.parts):
        raise ValueError("Relative path traversal is not allowed.")
    return path.as_posix()


def _resolve_child_path(root: Path, relative_path: str) -> Path:
    """Resolve a client-supplied relative path under a validated root."""
    normalized = _normalize_relative_path(relative_path)
    candidate = (root / Path(normalized)).resolve() if normalized else root.resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("Requested path escapes the configured workspace root.")
    return candidate


def _is_hidden_browser_entry(path: Path) -> bool:
    """Return True when one filesystem entry should stay out of the tactile browser."""
    return path.is_file() and path.name.endswith(WORKSPACE_SUFFIX)


def detect_entry_kind(path: Path) -> str:
    """Classify a filesystem entry into a Haptic Desktop content kind."""
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_MODEL_SUFFIXES:
        return "model"
    if suffix in SUPPORTED_TEXT_SUFFIXES:
        return "text"
    if suffix in SUPPORTED_AUDIO_SUFFIXES:
        return "audio"
    return "unsupported"


def build_kind_contract(kind: str) -> dict[str, str]:
    """Return the shared Haptic Desktop contract metadata for one entry kind."""
    normalized_kind = kind if kind in KIND_LABELS else "unsupported"
    return {
        "kind_label": KIND_LABELS[normalized_kind],
        "shape_key": KIND_SHAPE_KEYS[normalized_kind],
        "open_mode": KIND_OPEN_MODES[normalized_kind],
        "open_label": KIND_OPEN_LABELS[normalized_kind],
    }


def _read_workspace_descriptor(path: Path) -> dict[str, Any]:
    """Load and minimally validate a workspace descriptor file."""
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    if descriptor.get("format") != WORKSPACE_FORMAT:
        raise ValueError(f"Unsupported workspace format in {path.name}.")
    if descriptor.get("format_version") != 1:
        raise ValueError(f"Unsupported workspace format_version in {path.name}.")
    if not descriptor.get("slug") or not descriptor.get("title"):
        raise ValueError(f"Workspace descriptor {path.name} is missing required title/slug fields.")
    return descriptor


def _safe_location_object(path: Path, raw_location: Any) -> dict[str, Any]:
    """Return one validated location object or fall back to the descriptor folder."""
    if isinstance(raw_location, dict) and raw_location.get("mode") and raw_location.get("path"):
        return {
            "mode": str(raw_location["mode"]),
            "path": str(raw_location["path"]),
        }
    return {"mode": "absolute", "path": str(path.parent.resolve())}


def _normalized_repair_descriptor(path: Path) -> dict[str, Any]:
    """Return the normalized descriptor that would be written by one repair action."""
    try:
        raw_descriptor = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raw_descriptor = {}

    if not isinstance(raw_descriptor, dict):
        raw_descriptor = {}

    title = str(raw_descriptor.get("title") or "").strip()
    slug = str(raw_descriptor.get("slug") or "").strip()
    if not slug:
        filename_stem = path.name.removesuffix(WORKSPACE_SUFFIX)
        slug = _slugify(title or filename_stem)
    if not title:
        title = slug.replace("_", " ").replace("-", " ").title()

    content_location = _safe_location_object(path, raw_descriptor.get("content_root"))
    file_browser_location = _safe_location_object(path, raw_descriptor.get("file_browser_root"))
    content_root = _resolve_location(path, content_location)
    file_browser_root = _resolve_location(path, file_browser_location)
    if not content_root.exists() or not content_root.is_dir():
        raise ValueError("Workspace content root must exist before the descriptor can be repaired.")
    if not file_browser_root.exists() or not file_browser_root.is_dir():
        raise ValueError("Workspace file-browser root must exist before the descriptor can be repaired.")

    return {
        "format": WORKSPACE_FORMAT,
        "format_version": 1,
        "slug": slug,
        "title": title,
        "description": str(raw_descriptor.get("description") or "").strip(),
        "is_default": bool(raw_descriptor.get("is_default")),
        "content_root": content_location,
        "file_browser_root": file_browser_location,
        "libraries": {
            "models": _auto_collect_workspace_items(content_root, "models"),
            "texts": _auto_collect_workspace_items(content_root, "texts"),
            "audio": _auto_collect_workspace_items(content_root, "audio"),
        },
    }


def _repair_workspace_descriptor(path: Path) -> dict[str, Any]:
    """Rewrite one broken descriptor into the current normalized baseline."""
    descriptor = _normalized_repair_descriptor(path)
    path.write_text(json.dumps(descriptor, indent=2), encoding="utf-8")
    return descriptor


def _bundled_demo_workspace_defaults() -> dict[str, list[dict[str, Any]]]:
    """Return the complete seeded library for the bundled demo workspace."""
    return {
        "models": [
            {
                "slug": f"{model['slug']}_session",
                "title": model["title"],
                "summary": model["description"],
                "source": {"kind": "demo_model", "ref": model["slug"]},
            }
            for model in build_demo_model_catalog()
        ],
        "texts": [
            {
                "slug": f"{document['slug']}_session",
                "title": document["title"],
                "summary": document["summary"],
                "source": {"kind": "library_document", "ref": document["slug"]},
            }
            for document in build_document_catalog()
        ],
        "audio": [
            {
                "slug": f"{audio['slug']}_session",
                "title": audio["title"],
                "summary": audio["summary"],
                "source": {"kind": "library_audio", "ref": audio["slug"]},
            }
            for audio in build_audio_catalog()
        ],
    }


def _normalize_workspace_libraries(
    descriptor: dict[str, Any],
    *,
    registry_source: str,
) -> dict[str, list[dict[str, Any]]]:
    """Return workspace libraries with any bundled-demo defaults merged in."""
    libraries = {
        category: [dict(item) for item in descriptor.get("libraries", {}).get(category, [])]
        for category in ("models", "texts", "audio")
    }

    if not (
        registry_source == "bundled_demo"
        and descriptor.get("auto_include_all_bundled_assets")
    ):
        return libraries

    defaults = _bundled_demo_workspace_defaults()
    for category in ("models", "texts", "audio"):
        existing_refs = {
            item.get("source", {}).get("ref")
            for item in libraries[category]
            if item.get("source", {}).get("kind")
        }
        for item in defaults[category]:
            ref = item["source"]["ref"]
            if ref not in existing_refs:
                libraries[category].append(item)
    return libraries


def _load_workspace_record(path: Path, *, registry_source: str) -> dict[str, Any]:
    """Return a resolved catalog record for one workspace descriptor file."""
    descriptor = _read_workspace_descriptor(path)
    content_root = _resolve_location(path, descriptor["content_root"])
    file_browser_root = _resolve_location(path, descriptor["file_browser_root"])
    if not content_root.exists():
        raise ValueError(f"Workspace content root does not exist for {path.name}.")
    if not file_browser_root.exists():
        raise ValueError(f"Workspace file-browser root does not exist for {path.name}.")

    libraries = _normalize_workspace_libraries(descriptor, registry_source=registry_source)
    return {
        "slug": descriptor["slug"],
        "title": descriptor["title"],
        "description": descriptor.get("description", ""),
        "is_default": bool(descriptor.get("is_default")),
        "registry_source": registry_source,
        "registry_key": _registry_key_for_path(path),
        "workspace_file_path": str(path.resolve()),
        "workspace_file_label": _display_label_from_path(path),
        "content_root": content_root,
        "file_browser_root": file_browser_root,
        "libraries": libraries,
    }


def _workspace_registry_snapshot() -> dict[str, list[dict[str, Any]]]:
    """Return valid and invalid workspace registry entries with diagnostics."""
    records: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()
    demo_path = DEMO_WORKSPACE_FILE.resolve()
    if demo_path.exists():
        records.append(_load_workspace_record(demo_path, registry_source="bundled_demo"))
        seen_paths.add(demo_path)

    registry_payload = _load_registry_payload()
    for raw_path in registry_payload.get("workspace_files", []):
        path = Path(raw_path).expanduser().resolve()
        if path in seen_paths:
            continue
        if not path.exists():
            invalid_records.append(
                {
                    "registry_key": _registry_key_for_path(path),
                    "workspace_file_path": str(path),
                    "workspace_file_label": _display_label_from_path(path),
                    "registry_source": "user_registered",
                    "error_code": "missing_file",
                    "error": "Registered workspace file does not exist.",
                },
            )
            continue
        try:
            records.append(_load_workspace_record(path, registry_source="user_registered"))
            seen_paths.add(path)
        except ValueError as error:
            invalid_records.append(
                {
                    "registry_key": _registry_key_for_path(path),
                    "workspace_file_path": str(path),
                    "workspace_file_label": _display_label_from_path(path),
                    "registry_source": "user_registered",
                    "error_code": "invalid_descriptor",
                    "error": str(error),
                },
            )
            continue
    return {
        "records": records,
        "invalid_records": invalid_records,
    }


def _workspace_records() -> list[dict[str, Any]]:
    """Return all valid known workspaces, including the bundled demo workspace."""
    return _workspace_registry_snapshot()["records"]


def _workspace_record_by_slug(slug: str) -> dict[str, Any]:
    """Return one workspace record by slug."""
    for record in _workspace_records():
        if record["slug"] == slug:
            return record
    raise KeyError(slug)


def _location_preview(location: dict[str, Any]) -> dict[str, str]:
    """Return one user-facing preview payload for a descriptor location object."""
    raw_path = str(location.get("path", "")).strip()
    return {
        "mode": str(location.get("mode", "")),
        "path": raw_path,
        "label": _display_label_from_path(raw_path) if raw_path else "--",
    }


def _library_item_preview(item: dict[str, Any]) -> dict[str, str]:
    """Return one compact preview payload for a descriptor library item."""
    source = item.get("source", {})
    source_kind = str(source.get("kind", ""))
    source_ref = str(source.get("ref") or source.get("relative_path") or "")
    return {
        "slug": str(item.get("slug", "")),
        "title": str(item.get("title", "")),
        "summary": str(item.get("summary", "")),
        "source_kind": source_kind,
        "source_ref": source_ref,
        "relative_path": str(source.get("relative_path", "")),
        "source_label": {
            "demo_model": "Bundled demo model",
            "library_document": "Bundled text library",
            "library_audio": "Bundled audio library",
            "workspace_file": "Workspace file",
        }.get(source_kind, source_kind or "Unknown"),
    }


def _library_item_identity(item: dict[str, Any]) -> str:
    """Return one stable identity string for a descriptor library entry."""
    source = item.get("source", {})
    source_kind = str(source.get("kind", ""))
    source_ref = str(source.get("ref") or source.get("relative_path") or item.get("slug") or "")
    return f"{source_kind}:{source_ref}"


def _library_collection_preview(libraries: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Return one preview summary for the libraries stored in a workspace descriptor."""
    categories: dict[str, Any] = {}
    total_items = 0
    for category in ("models", "texts", "audio"):
        entries = libraries.get(category, [])
        total_items += len(entries)
        categories[category] = {
            "count": len(entries),
            "items": [_library_item_preview(item) for item in entries],
        }
    return {
        "total_items": total_items,
        "categories": categories,
    }


def _rescan_delta_preview(
    current_libraries: dict[str, list[dict[str, Any]]],
    rescanned_libraries: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Return one preview of what one rescan would add or remove per category."""
    categories: dict[str, Any] = {}
    for category in ("models", "texts", "audio"):
        current_items = current_libraries.get(category, [])
        rescanned_items = rescanned_libraries.get(category, [])
        current_ids = {_library_item_identity(item): item for item in current_items}
        rescanned_ids = {_library_item_identity(item): item for item in rescanned_items}
        added_ids = [identity for identity in rescanned_ids if identity not in current_ids]
        removed_ids = [identity for identity in current_ids if identity not in rescanned_ids]
        categories[category] = {
            "current_count": len(current_items),
            "rescanned_count": len(rescanned_items),
            "delta": len(rescanned_items) - len(current_items),
            "added_count": len(added_ids),
            "removed_count": len(removed_ids),
            "added_preview": [_library_item_preview(rescanned_ids[item_id]) for item_id in added_ids[:4]],
            "removed_preview": [_library_item_preview(current_ids[item_id]) for item_id in removed_ids[:4]],
        }
    return {"categories": categories}


def _candidate_library_preview(
    current_libraries: dict[str, list[dict[str, Any]]],
    rescanned_libraries: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Return one preview of discoverable workspace-file candidates not yet in the descriptor."""
    categories: dict[str, Any] = {}
    total_items = 0
    for category in ("models", "texts", "audio"):
        current_ids = {
            _library_item_identity(item)
            for item in current_libraries.get(category, [])
        }
        candidates = [
            item
            for item in rescanned_libraries.get(category, [])
            if _library_item_identity(item) not in current_ids
        ]
        total_items += len(candidates)
        categories[category] = {
            "count": len(candidates),
            "items": [_library_item_preview(item) for item in candidates],
        }
    return {
        "total_items": total_items,
        "categories": categories,
    }


def _editable_workspace_descriptor(slug: str) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    """Return one editable user-registered workspace record plus its descriptor payload."""
    record = _workspace_record_by_slug(slug)
    if record["registry_source"] != "user_registered":
        raise ValueError("Only user-registered workspaces can be edited from the manager.")
    descriptor_path = Path(record["workspace_file_path"]).resolve()
    descriptor = _read_workspace_descriptor(descriptor_path)
    return record, descriptor_path, descriptor


def _validate_workspace_library_category(category: str) -> str:
    """Return one validated descriptor library category."""
    normalized = str(category).strip().lower()
    if normalized not in {"models", "texts", "audio"}:
        raise ValueError(f"Unsupported workspace library category: {category}")
    return normalized


def _workspace_item_from_relative_path(relative_path: str, *, root_path: Path) -> tuple[str, dict[str, Any]]:
    """Return one descriptor library item derived from a workspace-root file path."""
    normalized_relative_path = _normalize_relative_path(relative_path)
    file_path = _resolve_child_path(root_path, normalized_relative_path)
    if not file_path.exists() or not file_path.is_file():
        raise ValueError("Workspace library item path must point to one existing file inside the content root.")
    if file_path.name.endswith(WORKSPACE_SUFFIX):
        raise ValueError("Workspace descriptor files cannot be added to the authored library.")

    kind = detect_entry_kind(file_path)
    category_map = {
        "model": "models",
        "text": "texts",
        "audio": "audio",
    }
    category = category_map.get(kind)
    if category is None:
        raise ValueError("Only supported model, text, or audio files can be added to the authored library.")

    item = {
        "slug": _stable_slug(normalized_relative_path, prefix=category[:-1]),
        "title": file_path.stem.replace("_", " ").replace("-", " ").title(),
        "summary": f"Curated {category[:-1]} from the workspace root.",
        "source": {"kind": "workspace_file", "relative_path": normalized_relative_path},
    }
    return category, item


def _descriptor_library_entry_by_slug(
    descriptor: dict[str, Any],
    category: str,
    item_slug: str,
) -> tuple[int, dict[str, Any]]:
    """Return one descriptor library item and its index by slug."""
    normalized_category = _validate_workspace_library_category(category)
    entries = descriptor.get("libraries", {}).get(normalized_category, [])
    for index, entry in enumerate(entries):
        if str(entry.get("slug", "")) == item_slug:
            return index, entry
    raise KeyError(item_slug)


def _workspace_descriptor_preview(path: Path, *, registry_source: str) -> dict[str, Any]:
    """Return one descriptor preview payload, including the current rescan delta."""
    descriptor = _read_workspace_descriptor(path)
    record = _load_workspace_record(path, registry_source=registry_source)
    content_root = _resolve_location(path, descriptor["content_root"])
    rescanned_libraries = {
        "models": _auto_collect_workspace_items(content_root, "models"),
        "texts": _auto_collect_workspace_items(content_root, "texts"),
        "audio": _auto_collect_workspace_items(content_root, "audio"),
    }
    return {
        "registry_key": record["registry_key"],
        "slug": record["slug"],
        "title": descriptor["title"],
        "description": descriptor.get("description", ""),
        "registry_source": registry_source,
        "workspace_file_label": record["workspace_file_label"],
        "workspace_file_path": record["workspace_file_path"],
        "can_edit": registry_source == "user_registered",
        "content_root": _location_preview(descriptor["content_root"]),
        "file_browser_root": _location_preview(descriptor["file_browser_root"]),
        "libraries": _library_collection_preview(descriptor.get("libraries", {})),
        "candidate_assets": _candidate_library_preview(descriptor.get("libraries", {}), rescanned_libraries),
        "rescan_preview": _rescan_delta_preview(descriptor.get("libraries", {}), rescanned_libraries),
    }


def _catalog_lookup(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    """Return one catalog item by a selected key value."""
    return next((item for item in items if item.get(key) == value), None)


def _resolve_workspace_item(workspace_slug: str, record: dict[str, Any], category: str, item: dict[str, Any]) -> dict[str, Any]:
    """Resolve one workspace item into a frontend-ready payload."""
    source = item.get("source", {})
    source_kind = source.get("kind")
    ref = source.get("ref")
    payload = {
        "slug": item["slug"],
        "title": item["title"],
        "summary": item.get("summary", ""),
        "category": category,
        "source": {"kind": source_kind},
    }

    if source_kind == "demo_model":
        model = _catalog_lookup(build_demo_model_catalog(), "slug", ref)
        if model is None:
            raise ValueError(f"Unknown demo model reference: {ref}")
        payload["kind"] = "model"
        payload.update(build_kind_contract("model"))
        payload["source"].update(
            {
                "ref": ref,
                "demo_model_slug": model["slug"],
                "file_url": model["file_url"],
                "title": model["title"],
                "format": model["file_format"],
                "format_label": model["format_label"],
                "extension": f".{model['file_format']}",
            },
        )
        return payload

    if source_kind == "library_document":
        document = _catalog_lookup(build_document_catalog(), "slug", ref)
        if document is None:
            raise ValueError(f"Unknown library document reference: {ref}")
        payload["kind"] = "text"
        payload.update(build_kind_contract("text"))
        payload["source"].update(
            {
                "ref": ref,
                "document_slug": document["slug"],
                "text_endpoint": f"/api/library/documents/{document['slug']}",
                "format": document["format"],
                "extension": f".{document['format']}",
            },
        )
        return payload

    if source_kind == "library_audio":
        audio = _catalog_lookup(build_audio_catalog(), "slug", ref)
        if audio is None:
            raise ValueError(f"Unknown library audio reference: {ref}")
        payload["kind"] = "audio"
        payload.update(build_kind_contract("audio"))
        payload["source"].update(
            {
                "ref": ref,
                "audio_slug": audio["slug"],
                "file_url": audio["file_url"],
                "format": audio["format"],
                "extension": f".{audio['format']}",
            },
        )
        return payload

    if source_kind == "workspace_file":
        relative_path = _normalize_relative_path(source.get("relative_path", ""))
        file_path = _resolve_child_path(record["content_root"], relative_path)
        payload["kind"] = detect_entry_kind(file_path)
        payload.update(build_kind_contract(payload["kind"]))
        payload["source"].update(
            {
                "relative_path": relative_path,
                "raw_file_endpoint": f"/api/haptic-workspaces/{workspace_slug}/raw-file?path={relative_path}",
                "extension": file_path.suffix.lower(),
            },
        )
        if payload["kind"] == "model":
            file_format = file_path.suffix.lower().lstrip(".")
            payload["source"]["format"] = file_format
            payload["source"]["format_label"] = MODEL_FORMAT_LABELS.get(
                file_format, file_format.upper()
            )
        if payload["kind"] == "text":
            payload["source"]["text_endpoint"] = (
                f"/api/haptic-workspaces/{workspace_slug}/text-file?path={relative_path}"
            )
        return payload

    raise ValueError(f"Unsupported workspace source kind: {source_kind}")


def build_haptic_workspace_catalog() -> list[dict[str, Any]]:
    """Return the public catalog of available Haptic Desktop workspaces."""
    catalog: list[dict[str, Any]] = []
    for record in _workspace_records():
        catalog.append(
            {
                "slug": record["slug"],
                "title": record["title"],
                "description": record["description"],
                "is_default": record["is_default"],
                "registry_source": record["registry_source"],
                "registry_key": record["registry_key"],
                "can_unregister": record["registry_source"] == "user_registered",
                "can_rescan": record["registry_source"] == "user_registered",
                "workspace_file_label": record["workspace_file_label"],
                "category_counts": {
                    "models": len(record["libraries"].get("models", [])),
                    "texts": len(record["libraries"].get("texts", [])),
                    "audio": len(record["libraries"].get("audio", [])),
                },
            },
        )
    return catalog


def build_haptic_workspace_payload(slug: str) -> dict[str, Any]:
    """Return one resolved workspace payload for frontend scene generation."""
    record = _workspace_record_by_slug(slug)
    libraries = {}
    for category in ("models", "texts", "audio"):
        libraries[category] = [
            _resolve_workspace_item(slug, record, category, item)
            for item in record["libraries"].get(category, [])
        ]

    return {
        "slug": record["slug"],
        "title": record["title"],
        "description": record["description"],
        "is_default": record["is_default"],
        "registry_source": record["registry_source"],
        "workspace_file_label": record["workspace_file_label"],
        "libraries": libraries,
        "file_browser": {
            "root_label": record["file_browser_root"].name,
        },
    }


def _paginate_browser_entries(entries: list[dict[str, Any]], *, page: int, page_size: int) -> tuple[list[dict[str, Any]], int, int]:
    """Return one browser page plus normalized page metadata."""
    if page_size < 1 or page_size > MAX_FILE_BROWSER_PAGE_SIZE:
        raise ValueError(
            f"Workspace browser page_size must be between 1 and {MAX_FILE_BROWSER_PAGE_SIZE}.",
        )
    total_entries = len(entries)
    page_count = max(1, (total_entries + page_size - 1) // page_size)
    normalized_page = min(max(page, 0), page_count - 1)
    start_index = normalized_page * page_size
    end_index = start_index + page_size
    return entries[start_index:end_index], normalized_page, page_count


def build_workspace_browser_payload(
    slug: str,
    relative_path: str = "",
    *,
    page: int = 0,
    page_size: int = DEFAULT_FILE_BROWSER_PAGE_SIZE,
    include_directory_child_counts: bool = False,
) -> dict[str, Any]:
    """Return a safe paginated file-system browser payload under the configured root."""
    record = _workspace_record_by_slug(slug)
    current_directory = _resolve_child_path(record["file_browser_root"], relative_path)
    if not current_directory.is_dir():
        raise ValueError("Requested workspace browser path is not a directory.")

    normalized_path = _normalize_relative_path(relative_path)
    entries: list[dict[str, Any]] = []
    for child in sorted(current_directory.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
        if _is_hidden_browser_entry(child):
            continue
        child_relative = child.relative_to(record["file_browser_root"]).as_posix()
        kind = detect_entry_kind(child)
        entry = {
            "slug": _stable_slug(child_relative, prefix="entry"),
            "title": child.name,
            "summary": f"{kind.title()} entry in the configured workspace root.",
            "kind": kind,
            "relative_path": child_relative,
            "size_bytes": child.stat().st_size if child.is_file() else 0,
            "extension": child.suffix.lower() if child.is_file() else "",
        }
        entry.update(build_kind_contract(kind))
        if kind == "directory":
            if include_directory_child_counts:
                entry["child_count"] = sum(1 for _ in child.iterdir())
        else:
            entry["source"] = {
                "kind": "workspace_file",
                "relative_path": child_relative,
                "raw_file_endpoint": f"/api/haptic-workspaces/{slug}/raw-file?path={child_relative}",
                "extension": child.suffix.lower(),
            }
            if kind == "model":
                file_format = child.suffix.lower().lstrip(".")
                entry["source"]["format"] = file_format
                entry["source"]["format_label"] = MODEL_FORMAT_LABELS.get(
                    file_format, file_format.upper()
                )
            if kind == "text":
                entry["source"]["text_endpoint"] = (
                    f"/api/haptic-workspaces/{slug}/text-file?path={child_relative}"
                )
        entries.append(entry)

    parent_path = ""
    if normalized_path:
        parent_path = PurePosixPath(normalized_path).parent.as_posix()
        if parent_path == ".":
            parent_path = ""

    paginated_entries, normalized_page, page_count = _paginate_browser_entries(
        entries,
        page=page,
        page_size=page_size,
    )

    return {
        "workspace_slug": slug,
        "current_path": normalized_path,
        "current_label": current_directory.name,
        "parent_path": parent_path or None,
        "page": normalized_page,
        "page_size": page_size,
        "page_count": page_count,
        "total_entries": len(entries),
        "entries": paginated_entries,
    }


def raw_workspace_file_path(slug: str, relative_path: str) -> Path:
    """Return a safe raw file path rooted in the workspace browser root."""
    record = _workspace_record_by_slug(slug)
    candidate = _resolve_child_path(record["file_browser_root"], relative_path)
    if not candidate.is_file():
        raise ValueError("Requested workspace file does not exist.")
    return candidate


def build_workspace_text_payload(slug: str, relative_path: str, *, offset: int = 0, max_chars: int = DEFAULT_SEGMENT_CHARS) -> dict[str, Any]:
    """Return a segmented text payload for one raw workspace file."""
    file_path = raw_workspace_file_path(slug, relative_path)
    if detect_entry_kind(file_path) != "text":
        raise ValueError("Requested workspace file is not a supported text file.")
    return build_text_payload_from_path(
        file_path,
        title=file_path.name,
        source_name="Workspace file",
        source_url=file_path.as_posix(),
        slug_seed=relative_path,
        offset=offset,
        max_chars=max_chars,
    )


def register_workspace_file(workspace_file_path: str) -> dict[str, Any]:
    """Register an existing workspace descriptor file in the local registry."""
    path = Path(workspace_file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise ValueError("Workspace file path does not exist.")
    if path.suffixes[-2:] != [".haptic_workspace", ".json"] and not path.name.endswith(WORKSPACE_SUFFIX):
        raise ValueError(f"Workspace files must end with {WORKSPACE_SUFFIX}.")

    descriptor = _read_workspace_descriptor(path)
    existing_slugs = {record["slug"] for record in _workspace_records()}
    if descriptor["slug"] in existing_slugs and path.resolve() != DEMO_WORKSPACE_FILE.resolve():
        for record in _workspace_records():
            if record["slug"] == descriptor["slug"] and Path(record["workspace_file_path"]).resolve() != path:
                raise ValueError(f"A workspace with slug '{descriptor['slug']}' is already registered.")

    payload = _load_registry_payload()
    paths = {Path(item).expanduser().resolve() for item in payload.get("workspace_files", [])}
    paths.add(path)
    payload["workspace_files"] = [str(item) for item in sorted(paths)]
    _save_registry_payload(payload)
    return _load_workspace_record(path, registry_source="user_registered")


def unregister_workspace_file(registry_key: str) -> dict[str, str]:
    """Remove one registered workspace descriptor reference from the local registry."""
    path = _registry_path_by_key(registry_key)
    payload = _load_registry_payload()
    remaining_paths = [
        str(Path(item).expanduser().resolve())
        for item in payload.get("workspace_files", [])
        if Path(item).expanduser().resolve() != path
    ]
    if len(remaining_paths) == len(payload.get("workspace_files", [])):
        raise KeyError(registry_key)
    payload["workspace_files"] = sorted(remaining_paths)
    _save_registry_payload(payload)
    return {
        "registry_key": registry_key,
        "workspace_file_label": _display_label_from_path(path),
    }


def rescan_workspace_file(slug: str) -> dict[str, Any]:
    """Rebuild one registered workspace library catalog from its current content root."""
    record = _workspace_record_by_slug(slug)
    if record["registry_source"] != "user_registered":
        raise ValueError("Only user-registered workspaces can be rescanned.")

    path = Path(record["workspace_file_path"]).resolve()
    descriptor = _read_workspace_descriptor(path)
    content_root = _resolve_location(path, descriptor["content_root"])
    descriptor["libraries"] = {
        "models": _auto_collect_workspace_items(content_root, "models"),
        "texts": _auto_collect_workspace_items(content_root, "texts"),
        "audio": _auto_collect_workspace_items(content_root, "audio"),
    }
    path.write_text(json.dumps(descriptor, indent=2), encoding="utf-8")
    return _load_workspace_record(path, registry_source="user_registered")


def repair_workspace_file(registry_key: str) -> dict[str, Any]:
    """Repair one invalid registered descriptor when it still exists on disk."""
    path = _registry_path_by_key(registry_key)
    if not path.exists() or not path.is_file():
        raise ValueError("Missing workspace files cannot be repaired in place.")
    _repair_workspace_descriptor(path)
    return _load_workspace_record(path, registry_source="user_registered")


def build_workspace_descriptor_preview(slug: str) -> dict[str, Any]:
    """Return one preview payload for a valid registered workspace descriptor."""
    record = _workspace_record_by_slug(slug)
    return _workspace_descriptor_preview(
        Path(record["workspace_file_path"]).resolve(),
        registry_source=record["registry_source"],
    )


def build_invalid_workspace_repair_preview(registry_key: str) -> dict[str, Any]:
    """Return one preview payload for repairing a broken registered descriptor."""
    path = _registry_path_by_key(registry_key)
    if not path.exists() or not path.is_file():
        raise ValueError("Missing workspace files cannot be repaired in place.")
    descriptor = _normalized_repair_descriptor(path)
    return {
        "registry_key": registry_key,
        "workspace_file_label": _display_label_from_path(path),
        "workspace_file_path": str(path.resolve()),
        "slug": descriptor["slug"],
        "title": descriptor["title"],
        "description": descriptor.get("description", ""),
        "content_root": _location_preview(descriptor["content_root"]),
        "file_browser_root": _location_preview(descriptor["file_browser_root"]),
        "libraries": _library_collection_preview(descriptor["libraries"]),
    }


def update_workspace_file(
    slug: str,
    *,
    title: str,
    description: str,
    content_root_path: str,
    file_browser_root_path: str,
    refresh_libraries: bool,
) -> dict[str, Any]:
    """Apply one safe structured descriptor update for a registered workspace."""
    record = _workspace_record_by_slug(slug)
    if record["registry_source"] != "user_registered":
        raise ValueError("Only user-registered workspaces can be edited.")

    normalized_title = title.strip()
    if not normalized_title:
        raise ValueError("Workspace title cannot be empty.")

    descriptor_path = Path(record["workspace_file_path"]).resolve()
    descriptor = _read_workspace_descriptor(descriptor_path)
    current_content_root = _resolve_location(descriptor_path, descriptor["content_root"])
    current_file_browser_root = _resolve_location(descriptor_path, descriptor["file_browser_root"])
    new_content_root = Path(content_root_path).expanduser().resolve()
    new_file_browser_root = Path(file_browser_root_path).expanduser().resolve()
    if not new_content_root.exists() or not new_content_root.is_dir():
        raise ValueError("Workspace content root must be an existing directory.")
    if not new_file_browser_root.exists() or not new_file_browser_root.is_dir():
        raise ValueError("Workspace file-browser root must be an existing directory.")

    descriptor["title"] = normalized_title
    descriptor["description"] = description.strip()
    descriptor["content_root"] = {"mode": "absolute", "path": str(new_content_root)}
    descriptor["file_browser_root"] = {"mode": "absolute", "path": str(new_file_browser_root)}

    roots_changed = (
        new_content_root != current_content_root
        or new_file_browser_root != current_file_browser_root
    )
    if refresh_libraries or roots_changed:
        descriptor["libraries"] = {
            "models": _auto_collect_workspace_items(new_content_root, "models"),
            "texts": _auto_collect_workspace_items(new_content_root, "texts"),
            "audio": _auto_collect_workspace_items(new_content_root, "audio"),
        }

    descriptor_path.write_text(json.dumps(descriptor, indent=2), encoding="utf-8")
    return _load_workspace_record(descriptor_path, registry_source="user_registered")


def add_workspace_library_item(
    slug: str,
    *,
    relative_path: str,
    title: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    """Add one discoverable workspace-file asset into the authored descriptor library."""
    record, descriptor_path, descriptor = _editable_workspace_descriptor(slug)
    category, item = _workspace_item_from_relative_path(relative_path, root_path=record["content_root"])

    entries = descriptor.setdefault("libraries", {}).setdefault(category, [])
    candidate_identity = _library_item_identity(item)
    if any(_library_item_identity(entry) == candidate_identity for entry in entries):
        raise ValueError("The selected workspace file is already present in the descriptor library.")

    if title and title.strip():
        item["title"] = title.strip()
    if summary is not None:
        item["summary"] = summary.strip()

    entries.append(item)
    descriptor_path.write_text(json.dumps(descriptor, indent=2), encoding="utf-8")
    return _load_workspace_record(descriptor_path, registry_source="user_registered")


def update_workspace_library_item(
    slug: str,
    *,
    category: str,
    item_slug: str,
    title: str,
    summary: str,
) -> dict[str, Any]:
    """Update one authored library item label and summary without changing its source."""
    _, descriptor_path, descriptor = _editable_workspace_descriptor(slug)
    normalized_category = _validate_workspace_library_category(category)
    _, entry = _descriptor_library_entry_by_slug(descriptor, normalized_category, item_slug)
    normalized_title = title.strip()
    if not normalized_title:
        raise ValueError("Workspace library items require a non-empty title.")

    entry["title"] = normalized_title
    entry["summary"] = summary.strip()
    descriptor_path.write_text(json.dumps(descriptor, indent=2), encoding="utf-8")
    return _load_workspace_record(descriptor_path, registry_source="user_registered")


def move_workspace_library_item(
    slug: str,
    *,
    category: str,
    item_slug: str,
    direction: str,
) -> dict[str, Any]:
    """Move one authored library item up or down inside its category ordering."""
    _, descriptor_path, descriptor = _editable_workspace_descriptor(slug)
    normalized_category = _validate_workspace_library_category(category)
    normalized_direction = str(direction).strip().lower()
    if normalized_direction not in {"up", "down"}:
        raise ValueError("Workspace library move direction must be 'up' or 'down'.")

    entries = descriptor.setdefault("libraries", {}).setdefault(normalized_category, [])
    index, entry = _descriptor_library_entry_by_slug(descriptor, normalized_category, item_slug)
    target_index = index - 1 if normalized_direction == "up" else index + 1
    if target_index < 0 or target_index >= len(entries):
        raise ValueError("Workspace library item is already at the requested boundary.")

    entries.pop(index)
    entries.insert(target_index, entry)
    descriptor_path.write_text(json.dumps(descriptor, indent=2), encoding="utf-8")
    return _load_workspace_record(descriptor_path, registry_source="user_registered")


def remove_workspace_library_item(
    slug: str,
    *,
    category: str,
    item_slug: str,
) -> dict[str, Any]:
    """Remove one authored library item from its category."""
    _, descriptor_path, descriptor = _editable_workspace_descriptor(slug)
    normalized_category = _validate_workspace_library_category(category)
    entries = descriptor.setdefault("libraries", {}).setdefault(normalized_category, [])
    index, _ = _descriptor_library_entry_by_slug(descriptor, normalized_category, item_slug)
    entries.pop(index)
    descriptor_path.write_text(json.dumps(descriptor, indent=2), encoding="utf-8")
    return _load_workspace_record(descriptor_path, registry_source="user_registered")


def _auto_collect_workspace_items(root_path: Path, kind: str) -> list[dict[str, Any]]:
    """Discover workspace files of a given kind under a user root."""
    suffixes = {
        "models": SUPPORTED_MODEL_SUFFIXES,
        "texts": SUPPORTED_TEXT_SUFFIXES,
        "audio": SUPPORTED_AUDIO_SUFFIXES,
    }[kind]

    items: list[dict[str, Any]] = []
    for path in sorted(root_path.rglob("*"), key=lambda entry: entry.as_posix().lower()):
        if not path.is_file() or path.name.endswith(WORKSPACE_SUFFIX):
            continue
        if path.suffix.lower() not in suffixes:
            continue
        relative_path = path.relative_to(root_path).as_posix()
        items.append(
            {
                "slug": _stable_slug(relative_path, prefix=kind[:-1]),
                "title": path.stem.replace("_", " ").replace("-", " ").title(),
                "summary": f"Auto-discovered {kind[:-1]} from the workspace root.",
                "source": {"kind": "workspace_file", "relative_path": relative_path},
            },
        )
    return items


def create_workspace_file(
    *,
    title: str,
    slug: str | None,
    description: str,
    root_path: str,
    auto_populate: bool = True,
) -> dict[str, Any]:
    """Create, register, and return a new workspace descriptor rooted in a user folder."""
    workspace_root = Path(root_path).expanduser().resolve()
    if not workspace_root.exists() or not workspace_root.is_dir():
        raise ValueError("Workspace root path must be an existing directory.")

    workspace_slug = _slugify(slug or title)
    workspace_file_path = workspace_root / f"{workspace_slug}{WORKSPACE_SUFFIX}"
    if workspace_file_path.exists():
        raise ValueError(f"The workspace file already exists: {workspace_file_path.name}")

    descriptor = {
        "format": WORKSPACE_FORMAT,
        "format_version": 1,
        "slug": workspace_slug,
        "title": title,
        "description": description,
        "is_default": False,
        "content_root": {"mode": "absolute", "path": str(workspace_root)},
        "file_browser_root": {"mode": "absolute", "path": str(workspace_root)},
        "libraries": {
            "models": _auto_collect_workspace_items(workspace_root, "models") if auto_populate else [],
            "texts": _auto_collect_workspace_items(workspace_root, "texts") if auto_populate else [],
            "audio": _auto_collect_workspace_items(workspace_root, "audio") if auto_populate else [],
        },
    }
    workspace_file_path.write_text(json.dumps(descriptor, indent=2), encoding="utf-8")
    return register_workspace_file(str(workspace_file_path))


def build_workspace_manager_payload() -> dict[str, Any]:
    """Return workspace-manager metadata for the frontend page."""
    snapshot = _workspace_registry_snapshot()

    invalid_workspaces: list[dict[str, Any]] = []
    for record in snapshot["invalid_records"]:
        preview = None
        if record["error_code"] == "invalid_descriptor":
            try:
                preview = build_invalid_workspace_repair_preview(record["registry_key"])
            except ValueError:
                preview = None

        invalid_workspaces.append(
            {
                "registry_key": record["registry_key"],
                "workspace_file_label": record["workspace_file_label"],
                "registry_source": record["registry_source"],
                "error_code": record["error_code"],
                "error": record["error"],
                "can_unregister": True,
                "can_repair": record["error_code"] == "invalid_descriptor",
                "repair_preview": preview,
            }
        )

    return {
        "workspace_suffix": WORKSPACE_SUFFIX,
        "registry_file_label": REGISTRY_FILE.name,
        "registry_storage_scope": "User-local FeelIT application state",
        "workspaces": build_haptic_workspace_catalog(),
        "invalid_workspaces": invalid_workspaces,
    }
