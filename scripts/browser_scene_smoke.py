"""Run a browser smoke test against the current FeelIT frontend routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlparse

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.version import APP_VERSION


@dataclass(frozen=True)
class SceneSpec:
    """Describe one user-facing route to validate and capture."""

    route: str
    canvas_selector: str
    min_unique_colors: int
    wait_until: str = "domcontentloaded"


@dataclass(frozen=True)
class SnapshotReference:
    """Track the most recent archived snapshot that represents one route."""

    version: str
    path: Path


SCENES: tuple[SceneSpec, ...] = (
    SceneSpec(route="/object-explorer", canvas_selector="#object-canvas", min_unique_colors=1200),
    SceneSpec(route="/braille-reader", canvas_selector="#braille-canvas", min_unique_colors=1500),
    SceneSpec(route="/haptic-desktop", canvas_selector="#desktop-canvas", min_unique_colors=1500),
    SceneSpec(
        route="/haptic-workspace-manager",
        canvas_selector=".workspace-grid",
        min_unique_colors=1200,
        wait_until="commit",
    ),
    SceneSpec(
        route="/haptic-configuration",
        canvas_selector=".workspace-grid",
        min_unique_colors=1200,
        wait_until="commit",
    ),
)


def reserve_free_local_port() -> int:
    """Return an available localhost TCP port for temporary test launches."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(base_url: str, timeout_seconds: int) -> None:
    """Wait for the local FeelIT server to expose a healthy HTTP endpoint."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(f"{base_url}/api/health", timeout=2) as response:
                if response.status == 200:
                    return
        except URLError:
            time.sleep(0.2)
        except OSError:
            time.sleep(0.2)
        else:
                return

    raise SystemExit(f"Server did not become ready within {timeout_seconds} seconds at {base_url}.")


def measure_canvas_colors(image_path: Path) -> int:
    """Return the number of unique RGBA colors present in the image."""
    image = Image.open(image_path).convert("RGBA")
    colors = image.getcolors(maxcolors=10_000_000)
    return len(colors) if colors else 10_000_000


def focused_label(page) -> str:
    """Return the current fallback-focus label from the desktop inspector."""
    return (page.locator("#desktop-focus-label").text_content() or "").strip()


def cycle_focus_to(page, label: str, *, max_steps: int = 20) -> bool:
    """Move the fallback focus until the requested label is active."""
    for _ in range(max_steps):
        if focused_label(page) == label:
            return True
        page.locator("#focus-next").click()
        page.wait_for_timeout(80)
    return focused_label(page) == label


def desktop_activate_matching_target(
    page,
    *,
    title: str | None = None,
    type_name: str | None = None,
    title_suffix: str | None = None,
) -> bool:
    """Activate one Haptic Desktop target selected by title or type through the debug API."""
    return bool(
        page.evaluate(
            """
            async (criteria) => {
              const debug = window.__feelitDesktopDebug;
              if (!debug?.targets || !debug?.activateTarget) {
                return false;
              }
              const target = debug.targets().find((item) => {
                if (criteria.title && item.title !== criteria.title) {
                  return false;
                }
                if (criteria.type_name && item.type !== criteria.type_name) {
                  return false;
                }
                if (criteria.title_suffix && !item.title.endsWith(criteria.title_suffix)) {
                  return false;
                }
                return !item.disabled;
              });
              if (!target) {
                return false;
              }
              return debug.activateTarget(target.id);
            }
            """,
            {
                "title": title,
                "type_name": type_name,
                "title_suffix": title_suffix,
            },
        ),
    )


def object_explorer_activate_matching_target(
    page,
    *,
    title: str | None = None,
    type_name: str | None = None,
) -> bool:
    """Activate one Object Explorer target selected by title or type through the debug API."""
    return bool(
        page.evaluate(
            """
            async (criteria) => {
              const debug = window.__feelitObjectExplorerDebug;
              if (!debug?.targets || !debug?.activateTarget) {
                return false;
              }
              const target = debug.targets().find((item) => {
                if (criteria.title && item.title !== criteria.title) {
                  return false;
                }
                if (criteria.type_name && item.type !== criteria.type_name) {
                  return false;
                }
                return !item.disabled;
              });
              if (!target) {
                return false;
              }
              return debug.activateTarget(target.id);
            }
            """,
            {
                "title": title,
                "type_name": type_name,
            },
        ),
    )


def stabilize_scene_for_capture(page, route: str) -> None:
    """Reset one routed frontend surface into a deterministic capture state."""
    if route == "/object-explorer":
        stabilized = page.evaluate(
            """
            async () => {
              const debug = window.__feelitObjectExplorerDebug;
              if (!debug?.stabilizeForCapture) {
                return false;
              }
              await debug.stabilizeForCapture();
              return true;
            }
            """,
        )
        if not stabilized:
            raise SystemExit("Object Explorer capture stabilization failed.")
        page.wait_for_function(
            """
            () => (document.querySelector('#explorer-scene-mode')?.textContent?.trim() ?? '') === 'Scene launcher'
            """,
            timeout=15_000,
        )
        page.wait_for_timeout(150)
        return

    if route == "/braille-reader":
        stabilized = page.evaluate(
            """
            async () => {
              const brailleDebug = window.__feelitBrailleDebug;
              if (brailleDebug?.getSceneMode?.() === "reading") {
                await brailleDebug.activateTarget?.("control-library");
              }
              const debug = window.__feelitSceneDebug?.["braille-reader"];
              if (!debug?.clearPersistedViewState || !debug?.setViewState || !debug?.renderNow) {
                return false;
              }
              debug.clearPersistedViewState();
              debug.setViewState(
                { position: [4.1, 2.9, 4.9], target: [0, 0.2, 0.2], zoom: 1 },
                { persist: false },
              );
              debug.setIdleAnimationEnabled?.(false);
              debug.resetIdleAnimatedObjects?.();
              debug.renderNow();
              return true;
            }
            """,
        )
        if not stabilized:
            raise SystemExit("Braille Reader capture stabilization failed.")
        page.wait_for_function(
            """
            () => (document.querySelector('#reader-scene-mode')?.textContent?.trim() ?? '') === 'Library launcher'
            """,
            timeout=15_000,
        )
        page.wait_for_timeout(150)
        return

    if route == "/haptic-desktop":
        stabilized = page.evaluate(
            """
            async () => {
              const debug = window.__feelitDesktopDebug;
              if (!debug?.stabilizeForCapture) {
                return false;
              }
              await debug.stabilizeForCapture();
              return true;
            }
            """,
        )
        if not stabilized:
            raise SystemExit("Haptic Desktop capture stabilization failed.")
        page.wait_for_function(
            """
            () => (document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '') === 'launcher'
            """,
            timeout=15_000,
        )
        page.wait_for_timeout(150)


def viewport_overflow_metrics(page) -> dict[str, float]:
    """Return document-vs-viewport sizing metrics for overflow checks."""
    return page.evaluate(
        """
        () => ({
          innerHeight: window.innerHeight,
          docScrollHeight: document.documentElement.scrollHeight,
          bodyScrollHeight: document.body.scrollHeight,
          docClientHeight: document.documentElement.clientHeight,
        })
        """,
    )


def read_debug_view_state(page, debug_key: str):
    """Return the exposed per-route camera view state for scene-regression checks."""
    return page.evaluate(
        """
        (routeKey) => window.__feelitSceneDebug?.[routeKey]?.getViewState?.() ?? null
        """,
        debug_key,
    )


def assert_view_state_close(
    failures: list[str],
    route: str,
    label: str,
    actual: dict | None,
    expected: dict,
    *,
    tolerance: float = 0.02,
) -> None:
    """Fail when a camera view state drifted away from the expected persisted view."""
    if actual is None:
        failures.append(f"{route} missing camera debug view state while checking {label}")
        return

    for key in ("position", "target"):
        actual_values = actual.get(key) or []
        expected_values = expected.get(key) or []
        if len(actual_values) != len(expected_values):
            failures.append(f"{route} {label} returned malformed {key} view data")
            return
        if any(abs(float(a) - float(b)) > tolerance for a, b in zip(actual_values, expected_values)):
            failures.append(
                f"{route} camera {label} drifted on {key}: actual={actual_values!r} expected={expected_values!r}",
            )
            return

    actual_zoom = float(actual.get("zoom", 1.0))
    expected_zoom = float(expected.get("zoom", 1.0))
    if abs(actual_zoom - expected_zoom) > tolerance:
        failures.append(
            f"{route} camera {label} drifted on zoom: actual={actual_zoom!r} expected={expected_zoom!r}",
        )


def snapshot_image_name(scene: SceneSpec | str) -> str:
    """Return the canonical image filename for one routed frontend surface."""
    route = scene.route if isinstance(scene, SceneSpec) else scene
    return f"{route.strip('/').replace('-', '_')}.png"


def version_sort_key(version_label: str) -> tuple[int, ...]:
    """Return a sortable numeric key for legacy and padded workspace versions."""
    raw = version_label[1:] if version_label.startswith("v") else version_label
    return tuple(int(part) for part in raw.split("."))


def history_root_dir() -> Path:
    """Return the tracked directory used for archived frontend snapshots."""
    return ROOT / "artifacts" / "frontend_snapshots" / "history"


def iter_history_versions(history_root: Path) -> list[tuple[str, Path]]:
    """Return the archived snapshot directories sorted by semantic version order."""
    if not history_root.exists():
        return []

    versions: list[tuple[str, Path]] = []
    for path in history_root.iterdir():
        if path.is_dir() and path.name.startswith("v"):
            versions.append((path.name[1:], path))
    versions.sort(key=lambda item: version_sort_key(item[0]))
    return versions


def file_digest(path: Path) -> str:
    """Return a stable digest for comparing curated snapshot payloads."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def same_file_content(left: Path, right: Path) -> bool:
    """Return True when two snapshot files carry identical bytes."""
    return file_digest(left) == file_digest(right)


def build_current_manifest_entries(routes: tuple[SceneSpec, ...]) -> list[dict[str, object]]:
    """Describe the fully populated `current/` snapshot baseline."""
    return [
        {
            "route": scene.route,
            "image": snapshot_image_name(scene),
            "archived": True,
            "visual_source_version": None,
        }
        for scene in routes
    ]


def build_history_manifest_entries(
    version: str,
    version_dir: Path,
    routes: tuple[SceneSpec, ...],
    latest_refs: dict[str, SnapshotReference],
) -> list[dict[str, object]]:
    """Describe a sparse archived version directory with per-route provenance."""
    entries: list[dict[str, object]] = []
    for scene in routes:
        image_name = snapshot_image_name(scene)
        image_path = version_dir / image_name
        active_ref = latest_refs.get(image_name)
        entries.append(
            {
                "route": scene.route,
                "image": image_name,
                "archived": image_path.exists(),
                "visual_source_version": version if image_path.exists() else active_ref.version if active_ref else None,
            },
        )
    return entries


def write_snapshot_manifest(
    target_dir: Path,
    *,
    base_url: str,
    routes: tuple[SceneSpec, ...],
    version: str,
    route_entries: list[dict[str, object]] | None = None,
    history_policy: str | None = None,
) -> None:
    """Write a small manifest describing one captured visual snapshot set."""
    target_dir.mkdir(parents=True, exist_ok=True)
    entries = route_entries or build_current_manifest_entries(routes)
    manifest = {
        "app": "FeelIT",
        "version": version,
        "base_url": base_url,
        "routes": entries,
    }
    if history_policy:
        manifest["history_policy"] = history_policy
        manifest["changed_routes"] = [
            entry["route"] for entry in entries if entry.get("archived")
        ]
    manifest_path = target_dir / "snapshot_manifest.json"
    existing_manifest: dict[str, object] | None = None
    if manifest_path.exists():
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    comparable_manifest = dict(manifest)
    existing_comparable_manifest = None
    if existing_manifest is not None:
        existing_comparable_manifest = dict(existing_manifest)
        existing_comparable_manifest.pop("generated_at_utc", None)
        if existing_comparable_manifest == comparable_manifest:
            manifest["generated_at_utc"] = existing_manifest.get("generated_at_utc")
            return

    manifest["generated_at_utc"] = datetime.now(UTC).replace(microsecond=0).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def prepare_snapshot_dir(target_dir: Path) -> None:
    """Remove curated snapshot payloads before writing a fresh set."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.png", "*.json"):
        for file_path in target_dir.glob(pattern):
            file_path.unlink()


def run_browser_smoke(base_url: str, screenshot_dir: Path) -> None:
    """Validate that each workspace loads and produces a non-trivial canvas image."""
    prepare_snapshot_dir(screenshot_dir)
    failures: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        for scene in SCENES:
            console_messages: list[str] = []
            page_errors: list[str] = []
            object_launcher_loaded = False
            object_launcher_paginated = False
            object_model_loaded = False
            object_non_obj_model_loaded = False
            object_launcher_returned = False
            desktop_gallery_loaded = False
            desktop_gallery_paginated = False
            page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
            page.on(
                "console",
                lambda message, store=console_messages, route=scene.route: store.append(
                    f"{route} console[{message.type}]: {message.text}",
                ),
            )
            page.on(
                "pageerror",
                lambda error, store=page_errors, route=scene.route: store.append(
                    f"{route} pageerror: {error}",
                ),
            )

            page.goto(f"{base_url}{scene.route}", wait_until=scene.wait_until, timeout=30_000)
            page.wait_for_selector(scene.canvas_selector, state="visible", timeout=15_000)
            if scene.route == "/object-explorer":
                page.wait_for_function(
                    """
                    () => {
                      const sceneMode = document.querySelector('#explorer-scene-mode')?.textContent?.trim() ?? '';
                      const launcherPage = document.querySelector('#explorer-launcher-page')?.textContent?.trim() ?? '';
                      const modelName = document.querySelector('#inspector-model-name')?.textContent?.trim() ?? '';
                      return sceneMode !== '' && sceneMode !== 'Loading' && launcherPage !== '' && launcherPage !== '--' && modelName !== '' && modelName !== '--';
                    }
                    """,
                    timeout=15_000,
                )
                scene_mode = (page.locator("#explorer-scene-mode").text_content() or "").strip()
                if scene_mode != "Scene launcher":
                    failures.append(
                        f"/object-explorer did not boot into the scene launcher; scene_mode={scene_mode!r}",
                    )
                else:
                    object_launcher_loaded = True
                page_two_loaded = page.evaluate(
                    """
                    async () => {
                      const debug = window.__feelitObjectExplorerDebug;
                      if (!debug?.activateTarget || !debug?.targetIds) {
                        return false;
                      }
                      if (!debug.targetIds().includes('launcher-next-page')) {
                        return false;
                      }
                      await debug.activateTarget('launcher-next-page');
                      return true;
                    }
                    """,
                )
                if not page_two_loaded:
                    failures.append("/object-explorer could not activate the launcher next-page control")
                else:
                    page.wait_for_function(
                        """
                        () => (document.querySelector('#explorer-launcher-page')?.textContent?.trim() ?? '').startsWith('2 /')
                        """,
                        timeout=15_000,
                    )
                    object_launcher_paginated = True
                if not object_explorer_activate_matching_target(page, title="Female Figure"):
                    failures.append("/object-explorer could not activate a page-2 launcher model target")
                else:
                    page.wait_for_function(
                        """
                        () => (document.querySelector('#explorer-scene-mode')?.textContent?.trim() ?? '') === 'Exploration scene'
                        """,
                        timeout=15_000,
                    )
                    object_model_loaded = True
                    if not page.evaluate(
                        """
                        async () => {
                          const debug = window.__feelitObjectExplorerDebug;
                          if (!debug?.activateTarget) {
                            return false;
                          }
                          return debug.activateTarget('exploration-launcher');
                        }
                        """,
                    ):
                        failures.append("/object-explorer could not activate the exploration Launcher control")
                    else:
                        page.wait_for_function(
                            """
                            () => {
                              const sceneMode = document.querySelector('#explorer-scene-mode')?.textContent?.trim() ?? '';
                              const launcherPage = document.querySelector('#explorer-launcher-page')?.textContent?.trim() ?? '';
                              return sceneMode === 'Scene launcher' && launcherPage.startsWith('2 /');
                            }
                            """,
                            timeout=15_000,
                        )
                        object_launcher_returned = True
                navigation_puck_page_loaded = page.evaluate(
                    """
                    async () => {
                      const debug = window.__feelitObjectExplorerDebug;
                      if (!debug?.navigateToLauncher) {
                        return false;
                      }
                      await debug.navigateToLauncher(4);
                      return true;
                    }
                    """,
                )
                if not navigation_puck_page_loaded:
                    failures.append("/object-explorer could not jump to the non-OBJ launcher page")
                else:
                    page.wait_for_function(
                        """
                        () => (document.querySelector('#explorer-launcher-page')?.textContent?.trim() ?? '').startsWith('5 /')
                        """,
                        timeout=15_000,
                    )
                    if not object_explorer_activate_matching_target(page, title="Navigation Puck"):
                        failures.append("/object-explorer could not activate the GLB launcher model target")
                    else:
                        page.wait_for_function(
                            """
                            () => (document.querySelector('#explorer-scene-mode')?.textContent?.trim() ?? '') === 'Exploration scene'
                            """,
                            timeout=15_000,
                        )
                        object_non_obj_model_loaded = True
                        if not page.evaluate(
                            """
                            async () => {
                              const debug = window.__feelitObjectExplorerDebug;
                              if (!debug?.activateTarget) {
                                return false;
                              }
                              return debug.activateTarget('exploration-launcher');
                            }
                            """,
                        ):
                            failures.append("/object-explorer could not return from the GLB scene to the launcher")
                        else:
                            page.wait_for_function(
                                """
                                () => {
                                  const sceneMode = document.querySelector('#explorer-scene-mode')?.textContent?.trim() ?? '';
                                  const launcherPage = document.querySelector('#explorer-launcher-page')?.textContent?.trim() ?? '';
                                  return sceneMode === 'Scene launcher' && launcherPage.startsWith('5 /');
                                }
                                """,
                                timeout=15_000,
                            )
            if scene.route == "/braille-reader":
                page.wait_for_function(
                    """
                    () => {
                      const documents = document.querySelectorAll('#library-document-select option').length;
                      const title = document.querySelector('#summary-document-title')?.textContent?.trim() ?? '';
                      const sceneMode = document.querySelector('#reader-scene-mode')?.textContent?.trim() ?? '';
                      return documents > 0 && title !== '' && title !== 'Loading' && sceneMode !== '' && sceneMode !== 'Loading';
                    }
                    """,
                    timeout=15_000,
                )
                scene_mode = (page.locator("#reader-scene-mode").text_content() or "").strip()
                if scene_mode != "Library launcher":
                    failures.append(
                        f"/braille-reader did not boot into the library launcher; scene_mode={scene_mode!r}",
                    )
                launcher_target_activated = page.evaluate(
                    """
                    async () => {
                      const debug = window.__feelitBrailleDebug;
                      if (!debug?.targetIds || !debug?.activateTarget) {
                        return false;
                      }
                      const targetId = debug.targetIds().find((id) => id.startsWith('library-document-'));
                      if (!targetId) {
                        return false;
                      }
                      return debug.activateTarget(targetId);
                    }
                    """,
                )
                if not launcher_target_activated:
                    failures.append("/braille-reader could not activate a scene-native library document target")
                else:
                    page.wait_for_function(
                        """
                        () => (document.querySelector('#reader-scene-mode')?.textContent?.trim() ?? '') === 'Reading scene'
                        """,
                        timeout=15_000,
                    )
                    library_return_activated = page.evaluate(
                        """
                        async () => {
                          const debug = window.__feelitBrailleDebug;
                          if (!debug?.activateTarget) {
                            return false;
                          }
                          return debug.activateTarget('control-library');
                        }
                        """,
                    )
                    if not library_return_activated:
                        failures.append("/braille-reader could not activate the library return control")
                    else:
                        page.wait_for_function(
                            """
                            () => (document.querySelector('#reader-scene-mode')?.textContent?.trim() ?? '') === 'Library launcher'
                            """,
                            timeout=15_000,
                        )
            if scene.route == "/haptic-desktop":
                persisted_view = {
                    "position": [6.15, 4.05, 2.35],
                    "target": [0.4, 0.52, -0.28],
                    "zoom": 1,
                }
                desktop_browser_text_loaded = False
                desktop_browser_audio_loaded = False
                desktop_browser_model_loaded = False
                page.wait_for_function(
                    """
                    () => {
                      const workspaces = document.querySelectorAll('#desktop-workspace-select option').length;
                      const title = document.querySelector('#desktop-workspace-title')?.textContent?.trim() ?? '';
                      const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                      return workspaces > 0 && title !== '' && title !== 'Loading' && title !== 'No workspace' && sceneCode !== '' && sceneCode !== '--' && sceneCode !== 'Loading';
                    }
                    """,
                    timeout=15_000,
                )
                if not page.evaluate(
                    """
                    (viewState) => {
                      const debug = window.__feelitSceneDebug?.["haptic-desktop"];
                      if (!debug?.setViewState || !debug?.hasPersistedViewState) {
                        return false;
                      }
                      debug.setViewState(viewState, { persist: true });
                      return debug.hasPersistedViewState();
                    }
                    """,
                    persisted_view,
                ):
                    failures.append("/haptic-desktop could not seed a persisted camera view state")
                if not cycle_focus_to(page, "Models Gallery"):
                    failures.append("/haptic-desktop could not focus Models Gallery from the launcher")
                else:
                    page.locator("#focus-activate").click()
                page.wait_for_function(
                    """
                    () => {
                      const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                      const pagination = document.querySelector('#desktop-pagination')?.textContent?.trim() ?? '';
                      return sceneCode === 'models-gallery' && pagination !== '' && pagination !== '--';
                    }
                    """,
                    timeout=15_000,
                )
                assert_view_state_close(
                    failures,
                    scene.route,
                    "after entering the gallery",
                    read_debug_view_state(page, "haptic-desktop"),
                    persisted_view,
                )
                desktop_gallery_loaded = True
                if focused_label(page) != "Gallery":
                    failures.append(
                        f"/haptic-desktop entered the models gallery with focus on {focused_label(page)!r} instead of 'Gallery'",
                    )
                if not cycle_focus_to(page, "Next"):
                    failures.append("/haptic-desktop could not focus the gallery Next control")
                else:
                    page.locator("#focus-activate").click()
                    page.wait_for_function(
                        """
                        () => {
                          const pagination = document.querySelector('#desktop-pagination')?.textContent?.trim() ?? '';
                          return pagination.startsWith('2 /');
                        }
                        """,
                        timeout=15_000,
                    )
                    desktop_gallery_paginated = True
                    if focused_label(page) != "Gallery":
                        failures.append(
                            f"/haptic-desktop page turn did not land on the gallery hub; focus={focused_label(page)!r}",
                        )
                if not cycle_focus_to(page, "Female Figure"):
                    failures.append("/haptic-desktop could not focus a page-2 model gallery item")
                else:
                    page.locator("#focus-activate").click()
                    page.wait_for_function(
                        """
                        () => {
                          const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                          return sceneCode === 'detail-model';
                        }
                        """,
                        timeout=15_000,
                    )
                    if not cycle_focus_to(page, "Open"):
                        failures.append("/haptic-desktop could not focus the detail Open control")
                    else:
                        page.locator("#focus-activate").click()
                        page.wait_for_function(
                            """
                            () => {
                              const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                              return sceneCode === 'open-model';
                            }
                            """,
                            timeout=15_000,
                        )
                        assert_view_state_close(
                            failures,
                            scene.route,
                            "after opening the model scene",
                            read_debug_view_state(page, "haptic-desktop"),
                            persisted_view,
                        )
                    if not cycle_focus_to(page, "Gallery"):
                        failures.append("/haptic-desktop could not focus the model Gallery return control")
                    else:
                        page.locator("#focus-activate").click()
                        page.wait_for_function(
                            """
                            () => {
                              const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                              const pagination = document.querySelector('#desktop-pagination')?.textContent?.trim() ?? '';
                              return sceneCode === 'models-gallery' && pagination.startsWith('2 /');
                            }
                            """,
                            timeout=15_000,
                        )
                        assert_view_state_close(
                            failures,
                            scene.route,
                            "after returning to the gallery",
                            read_debug_view_state(page, "haptic-desktop"),
                            persisted_view,
                        )
                        if focused_label(page) != "Gallery":
                            failures.append(
                                f"/haptic-desktop gallery return landed on {focused_label(page)!r} instead of 'Gallery'",
                            )
                if not cycle_focus_to(page, "Start"):
                    failures.append("/haptic-desktop could not focus the gallery Start control")
                else:
                    page.locator("#focus-activate").click()
                    page.wait_for_function(
                        """
                        () => {
                          const pagination = document.querySelector('#desktop-pagination')?.textContent?.trim() ?? '';
                          return pagination.startsWith('1 /');
                        }
                        """,
                        timeout=15_000,
                    )
                    if focused_label(page) != "Gallery":
                        failures.append(
                            f"/haptic-desktop gallery Start did not land on the gallery hub; focus={focused_label(page)!r}",
                        )
                if not cycle_focus_to(page, "Launcher"):
                    failures.append("/haptic-desktop could not focus the gallery Launcher control")
                else:
                    page.locator("#focus-activate").click()
                    page.wait_for_function(
                        """
                        () => {
                          const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                          return sceneCode === 'launcher';
                        }
                        """,
                        timeout=15_000,
                    )
                    launcher_focus = focused_label(page)
                    if launcher_focus != "Launcher":
                        failures.append(
                            f"/haptic-desktop returned to launcher but left focus on {launcher_focus!r} instead of 'Launcher'",
                        )
                    if not cycle_focus_to(page, "File Browser"):
                        failures.append("/haptic-desktop could not focus File Browser from the launcher")
                    else:
                        page.locator("#focus-activate").click()
                        page.wait_for_function(
                            """
                            () => {
                              const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                              return sceneCode === 'file-browser';
                            }
                            """,
                        timeout=15_000,
                    )
                    if focused_label(page) != "Browser":
                        failures.append(
                            f"/haptic-desktop entered the file browser with focus on {focused_label(page)!r} instead of 'Browser'",
                        )
                    if not cycle_focus_to(page, "library"):
                        failures.append("/haptic-desktop could not focus the library folder from the file browser root")
                    else:
                        if not cycle_focus_to(page, "Launcher"):
                            failures.append("/haptic-desktop could not focus the file-browser Launcher control")
                        else:
                            page.keyboard.down("Space")
                            page.wait_for_timeout(900)
                            page.keyboard.up("Space")
                            page.wait_for_timeout(700)
                            scene_after_hold = (page.locator("#desktop-scene-code").text_content() or "").strip()
                            focus_after_hold = focused_label(page)
                            if scene_after_hold != "launcher":
                                failures.append(
                                    f"/haptic-desktop held-space return from file browser ended on {scene_after_hold!r} instead of 'launcher'",
                                )
                            if focus_after_hold != "Launcher":
                                failures.append(
                                    f"/haptic-desktop held-space return from file browser left focus on {focus_after_hold!r} instead of 'Launcher'",
                                )
                        if not cycle_focus_to(page, "File Browser"):
                            failures.append("/haptic-desktop could not refocus File Browser from the launcher after the held-space test")
                        else:
                            page.locator("#focus-activate").click()
                            page.wait_for_timeout(1_000)
                        if not cycle_focus_to(page, "library"):
                            failures.append("/haptic-desktop could not refocus the library folder from the file browser root")
                        else:
                            page.locator("#focus-activate").click()
                            page.wait_for_timeout(1_200)
                            scene_in_library = (page.locator("#desktop-scene-code").text_content() or "").strip()
                            path_in_library = (page.locator("#desktop-scene-path").text_content() or "").strip()
                            if scene_in_library != "file-browser" or "library" not in path_in_library:
                                failures.append(
                                    f"/haptic-desktop did not enter the library folder correctly; scene={scene_in_library!r} path={path_in_library!r}",
                                )
                            if focused_label(page) != "Browser":
                                failures.append(
                                    f"/haptic-desktop did not land on the browser hub after entering library; focus={focused_label(page)!r}",
                                )
                    if not cycle_focus_to(page, "documents"):
                        failures.append("/haptic-desktop could not focus the documents folder from the library root")
                    else:
                        page.locator("#focus-activate").click()
                        page.wait_for_function(
                            """
                            () => {
                              const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                              const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                              return sceneCode === 'file-browser' && scenePath.includes('library/documents');
                            }
                            """,
                            timeout=15_000,
                        )
                    if not cycle_focus_to(page, "alice_in_wonderland.txt"):
                        failures.append("/haptic-desktop could not focus a supported text file inside documents")
                    else:
                        focus_action = (page.locator("#desktop-focus-action").text_content() or "").strip()
                        if "Braille reading scene" not in focus_action:
                            failures.append(
                                f"/haptic-desktop supported text file did not advertise the Braille reading scene action; action={focus_action!r}",
                            )
                        else:
                            page.locator("#focus-activate").click()
                            page.wait_for_function(
                                """
                                () => {
                                  const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                                  const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                                  return sceneCode === 'open-text' && scenePath.includes('alice_in_wonderland.txt');
                                }
                                """,
                                timeout=15_000,
                            )
                            desktop_browser_text_loaded = True
                            if not cycle_focus_to(page, "Browser"):
                                failures.append("/haptic-desktop could not focus the file-browser return control from the text scene")
                            else:
                                page.locator("#focus-activate").click()
                                page.wait_for_function(
                                    """
                                    () => {
                                      const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                                      const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                                      return sceneCode === 'file-browser' && scenePath.includes('library/documents');
                                    }
                                    """,
                                    timeout=15_000,
                                )
                    if not cycle_focus_to(page, "Root"):
                        failures.append("/haptic-desktop could not focus the file-browser Root control from the documents folder")
                    else:
                        page.locator("#focus-activate").click()
                        page.wait_for_function(
                            """
                            () => {
                              const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                              const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                              return sceneCode === 'file-browser' && scenePath === 'assets';
                            }
                            """,
                            timeout=15_000,
                        )
                    if not cycle_focus_to(page, "library"):
                        failures.append("/haptic-desktop could not refocus the library folder from the file browser root")
                    else:
                        page.locator("#focus-activate").click()
                        page.wait_for_function(
                            """
                            () => {
                              const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                              const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                              return sceneCode === 'file-browser' && scenePath.includes('library');
                            }
                            """,
                            timeout=15_000,
                        )
                        if not cycle_focus_to(page, "audio"):
                            failures.append("/haptic-desktop could not focus the audio folder from the library root")
                        else:
                            page.locator("#focus-activate").click()
                            page.wait_for_function(
                                """
                                () => {
                                  const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                                  const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                                  return sceneCode === 'file-browser' && scenePath.includes('library/audio');
                                }
                                """,
                                timeout=15_000,
                            )
                            if not desktop_activate_matching_target(page, type_name="Audio"):
                                failures.append("/haptic-desktop could not activate a supported audio file from the file browser")
                            else:
                                page.wait_for_function(
                                    """
                                    () => (document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '') === 'open-audio'
                                    """,
                                    timeout=15_000,
                                )
                                desktop_browser_audio_loaded = True
                                if not cycle_focus_to(page, "Browser"):
                                    failures.append("/haptic-desktop could not focus the file-browser return control from the audio scene")
                                else:
                                    page.locator("#focus-activate").click()
                                    page.wait_for_function(
                                        """
                                        () => {
                                          const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                                          const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                                          return sceneCode === 'file-browser' && scenePath.includes('library/audio');
                                        }
                                        """,
                                        timeout=15_000,
                                    )
                    if not cycle_focus_to(page, "Root"):
                        failures.append("/haptic-desktop could not refocus the file-browser Root control from the audio folder")
                    else:
                        page.locator("#focus-activate").click()
                        page.wait_for_function(
                            """
                            () => {
                              const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                              const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                              return sceneCode === 'file-browser' && scenePath === 'assets';
                            }
                            """,
                            timeout=15_000,
                        )
                    if not cycle_focus_to(page, "models"):
                        failures.append("/haptic-desktop could not focus the models folder from the file browser root")
                    else:
                        page.locator("#focus-activate").click()
                        page.wait_for_function(
                            """
                            () => {
                              const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                              const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                              return sceneCode === 'file-browser' && scenePath.includes('models');
                            }
                            """,
                            timeout=15_000,
                        )
                        if not cycle_focus_to(page, "demo"):
                            failures.append("/haptic-desktop could not focus the demo folder from the models root")
                        else:
                            page.locator("#focus-activate").click()
                            page.wait_for_function(
                                """
                                () => {
                                  const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                                  const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                                  return sceneCode === 'file-browser' && scenePath.includes('models/demo');
                                }
                                """,
                                timeout=15_000,
                            )
                            if not desktop_activate_matching_target(page, title="locator_token.stl"):
                                failures.append("/haptic-desktop could not activate the STL model file from the file browser")
                            else:
                                page.wait_for_function(
                                    """
                                    () => (document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '') === 'open-model'
                                    """,
                                    timeout=15_000,
                                )
                                desktop_browser_model_loaded = True
                                if not cycle_focus_to(page, "Browser"):
                                    failures.append("/haptic-desktop could not focus the file-browser return control from the model scene")
                                else:
                                    page.locator("#focus-activate").click()
                                    page.wait_for_function(
                                        """
                                        () => {
                                          const sceneCode = document.querySelector('#desktop-scene-code')?.textContent?.trim() ?? '';
                                          const scenePath = document.querySelector('#desktop-scene-path')?.textContent?.trim() ?? '';
                                          return sceneCode === 'file-browser' && scenePath.includes('models/demo');
                                        }
                                        """,
                                        timeout=15_000,
                                    )
            if scene.route == "/haptic-workspace-manager":
                page.wait_for_function(
                    """
                    () => {
                      const workspaces = document.querySelectorAll('#workspace-list .workspace-card').length;
                      const runtime = document.querySelector('#manager-runtime-pill')?.textContent?.trim() ?? '';
                      const pageStatus = document.querySelector('#manager-page-status')?.textContent?.trim() ?? '';
                      return workspaces > 0 && runtime !== '' && runtime !== 'Loading' && pageStatus !== '' && pageStatus !== 'Waiting';
                    }
                    """,
                    timeout=15_000,
                )
            if scene.route == "/haptic-configuration":
                page.wait_for_function(
                    """
                    () => {
                      const backends = document.querySelectorAll('#backend-list .backend-card').length;
                      const runtime = document.querySelector('#config-runtime-pill')?.textContent?.trim() ?? '';
                      const pageStatus = document.querySelector('#config-page-status')?.textContent?.trim() ?? '';
                      return backends > 0 && runtime !== '' && runtime !== 'Loading' && pageStatus !== '' && pageStatus !== 'Waiting';
                    }
                    """,
                    timeout=15_000,
                )
            if scene.route != "/haptic-workspace-manager":
                stabilize_scene_for_capture(page, scene.route)
            page.wait_for_timeout(1_200)
            overflow_metrics = viewport_overflow_metrics(page)

            screenshot_path = screenshot_dir / f"{scene.route.strip('/').replace('-', '_')}.png"
            page.locator(scene.canvas_selector).screenshot(path=str(screenshot_path))
            unique_colors = measure_canvas_colors(screenshot_path)
            version_text = (page.locator('[data-runtime="version"]').first.text_content() or "").strip()
            api_status_text = (page.locator('[data-runtime="api-status"]').first.text_content() or "").strip()
            error_overlay_count = page.locator(".stage-error-overlay").count()

            error_logs = [
                line for line in console_messages
                if "console[error]" in line or "404" in line or "Failed to load" in line
            ]
            if page_errors:
                failures.extend(page_errors)
            if error_logs:
                failures.extend(error_logs)
            if unique_colors < scene.min_unique_colors:
                failures.append(
                    f"{scene.route} capture looks under-rendered: "
                    f"{unique_colors} unique colors < {scene.min_unique_colors}",
                )
            if version_text in {"", "v--", "Loading", "Error"}:
                failures.append(f"{scene.route} runtime version slot did not initialize: {version_text!r}")
            if api_status_text in {"", "Loading", "error"}:
                failures.append(f"{scene.route} API status slot did not initialize: {api_status_text!r}")
            if error_overlay_count:
                failures.append(f"{scene.route} rendered a visible stage boot error overlay")
            if overflow_metrics["docScrollHeight"] > overflow_metrics["innerHeight"] + 2:
                failures.append(
                    f"{scene.route} overflowed vertically: "
                    f"scrollHeight={overflow_metrics['docScrollHeight']} "
                    f"innerHeight={overflow_metrics['innerHeight']}",
                )
            if overflow_metrics["bodyScrollHeight"] > overflow_metrics["innerHeight"] + 2:
                failures.append(
                    f"{scene.route} body overflowed vertically: "
                    f"bodyScrollHeight={overflow_metrics['bodyScrollHeight']} "
                    f"innerHeight={overflow_metrics['innerHeight']}",
                )
            if scene.route == "/object-explorer":
                scene_mode = (page.locator("#explorer-scene-mode").text_content() or "").strip()
                launcher_page = (page.locator("#explorer-launcher-page").text_content() or "").strip()
                model_name = (page.locator("#inspector-model-name").text_content() or "").strip()
                if scene_mode != "Scene launcher":
                    failures.append(f"/object-explorer did not settle back on the scene launcher: {scene_mode!r}")
                if launcher_page in {"", "--"}:
                    failures.append("/object-explorer did not initialize the launcher page indicator")
                if model_name in {"", "--"}:
                    failures.append("/object-explorer did not initialize the selected model summary")
                if not object_launcher_loaded:
                    failures.append("/object-explorer did not boot into the scene launcher")
                if not object_launcher_paginated:
                    failures.append("/object-explorer did not expose real launcher pagination")
                if not object_model_loaded:
                    failures.append("/object-explorer did not open a scene-native model session from the launcher")
                if not object_non_obj_model_loaded:
                    failures.append("/object-explorer did not open a non-OBJ launcher model session")
                if not object_launcher_returned:
                    failures.append("/object-explorer did not return from the exploration scene back to the launcher page")
            if scene.route == "/braille-reader":
                document_options = page.locator("#library-document-select option").count()
                audio_options = page.locator("#library-audio-select option").count()
                document_title = (page.locator("#summary-document-title").text_content() or "").strip()
                scene_mode = (page.locator("#reader-scene-mode").text_content() or "").strip()
                if document_options == 0:
                    failures.append("/braille-reader did not populate the internal document library selector")
                if audio_options == 0:
                    failures.append("/braille-reader did not populate the internal audio library selector")
                if document_title in {"", "Loading"}:
                    failures.append("/braille-reader did not initialize the active library document summary")
                if scene_mode not in {"Library launcher", "Reading scene"}:
                    failures.append(f"/braille-reader reported an invalid scene mode: {scene_mode!r}")
            if scene.route == "/haptic-desktop":
                workspace_options = page.locator("#desktop-workspace-select option").count()
                workspace_title = (page.locator("#desktop-workspace-title").text_content() or "").strip()
                scene_code = (page.locator("#desktop-scene-code").text_content() or "").strip()
                if workspace_options == 0:
                    failures.append("/haptic-desktop did not populate the workspace selector")
                if workspace_title in {"", "Loading", "No workspace"}:
                    failures.append("/haptic-desktop did not initialize the active workspace summary")
                if not desktop_gallery_loaded:
                    failures.append("/haptic-desktop did not navigate from launcher into the models gallery")
                if not desktop_gallery_paginated:
                    failures.append("/haptic-desktop models gallery did not expose real pagination")
                if not desktop_browser_text_loaded:
                    failures.append("/haptic-desktop did not open a text file from the file browser into the reading scene")
                if not desktop_browser_audio_loaded:
                    failures.append("/haptic-desktop did not open an audio file from the file browser into the audio scene")
                if not desktop_browser_model_loaded:
                    failures.append("/haptic-desktop did not open a model file from the file browser into the model scene")
                if scene_code in {"", "--", "Loading"}:
                    failures.append("/haptic-desktop did not initialize the scene code")
            if scene.route == "/haptic-workspace-manager":
                workspace_cards = page.locator("#workspace-list .workspace-card").count()
                manager_runtime = (page.locator("#manager-runtime-pill").text_content() or "").strip()
                manager_status = (page.locator("#manager-page-status").text_content() or "").strip()
                selected_title = (page.locator("#selected-workspace-title").text_content() or "").strip()
                if workspace_cards == 0:
                    failures.append("/haptic-workspace-manager did not render any registered workspace cards")
                if manager_runtime in {"", "Loading", "Runtime error"}:
                    failures.append("/haptic-workspace-manager did not initialize the runtime pill")
                if manager_status in {"", "Waiting", "Boot failed"}:
                    failures.append("/haptic-workspace-manager did not initialize the page status")
                if selected_title in {"", "--"}:
                    failures.append("/haptic-workspace-manager did not initialize the selected workspace summary")
            if scene.route == "/haptic-configuration":
                backend_cards = page.locator("#backend-list .backend-card").count()
                runtime_pill = (page.locator("#config-runtime-pill").text_content() or "").strip()
                page_status = (page.locator("#config-page-status").text_content() or "").strip()
                requested_backend = (page.locator("#config-requested-backend").text_content() or "").strip()
                active_backend = (page.locator("#config-active-backend").text_content() or "").strip()
                selected_backend_title = (page.locator("#selected-backend-title").text_content() or "").strip()
                if backend_cards == 0:
                    failures.append("/haptic-configuration did not render any backend diagnostics cards")
                if runtime_pill in {"", "Loading", "Runtime error"}:
                    failures.append("/haptic-configuration did not initialize the runtime pill")
                if page_status in {"", "Waiting", "Boot failed"}:
                    failures.append("/haptic-configuration did not initialize the page status")
                if requested_backend in {"", "Loading"}:
                    failures.append("/haptic-configuration did not initialize the requested backend summary")
                if active_backend in {"", "Loading"}:
                    failures.append("/haptic-configuration did not initialize the active backend summary")
                if selected_backend_title in {"", "--"}:
                    failures.append("/haptic-configuration did not initialize the selected backend inspector")

            print(
                f"{scene.route}: unique_colors={unique_colors} "
                f"version={version_text} api_status={api_status_text} "
                f"screenshot={screenshot_path}",
            )
            page.close()

        browser.close()

    if failures:
        raise SystemExit("Browser smoke test failed:\n- " + "\n- ".join(failures))

    write_snapshot_manifest(
        screenshot_dir,
        base_url="local_smoke_capture",
        routes=SCENES,
        version=APP_VERSION,
        route_entries=build_current_manifest_entries(SCENES),
    )


def normalize_sparse_history(
    history_root: Path,
    routes: tuple[SceneSpec, ...] = SCENES,
) -> None:
    """Retrofit sparse history manifests and remove redundant archived route images."""
    latest_refs: dict[str, SnapshotReference] = {}

    for version, version_dir in iter_history_versions(history_root):
        for scene in routes:
            image_name = snapshot_image_name(scene)
            image_path = version_dir / image_name
            previous_ref = latest_refs.get(image_name)
            if not image_path.exists():
                continue
            if previous_ref and same_file_content(image_path, previous_ref.path):
                image_path.unlink()
                continue
            latest_refs[image_name] = SnapshotReference(version=version, path=image_path)

        write_snapshot_manifest(
            version_dir,
            base_url="archived_release_snapshot",
            routes=routes,
            version=version,
            route_entries=build_history_manifest_entries(version, version_dir, routes, latest_refs),
            history_policy="sparse_changed_routes_only",
        )


def archive_snapshot_set(
    current_dir: Path,
    archive_version: str,
    *,
    routes: tuple[SceneSpec, ...] = SCENES,
    history_root: Path | None = None,
) -> Path:
    """Freeze only the route snapshots that changed relative to prior archived baselines."""
    resolved_history_root = history_root or history_root_dir()
    archive_dir = resolved_history_root / f"v{archive_version}"
    prepare_snapshot_dir(archive_dir)

    latest_refs: dict[str, SnapshotReference] = {}
    for version, version_dir in iter_history_versions(resolved_history_root):
        if version == archive_version:
            continue
        for scene in routes:
            image_name = snapshot_image_name(scene)
            image_path = version_dir / image_name
            if image_path.exists():
                latest_refs[image_name] = SnapshotReference(version=version, path=image_path)

    for scene in routes:
        image_name = snapshot_image_name(scene)
        current_image = current_dir / image_name
        if not current_image.exists():
            continue
        previous_ref = latest_refs.get(image_name)
        if previous_ref and same_file_content(current_image, previous_ref.path):
            continue
        shutil.copy2(current_image, archive_dir / image_name)

    normalize_sparse_history(resolved_history_root, routes)
    refreshed_refs = {
        image_name: ref
        for image_name, ref in latest_refs.items()
    }
    for scene in routes:
        image_name = snapshot_image_name(scene)
        image_path = archive_dir / image_name
        if image_path.exists():
            refreshed_refs[image_name] = SnapshotReference(version=archive_version, path=image_path)

    write_snapshot_manifest(
        archive_dir,
        base_url="archived_release_snapshot",
        routes=routes,
        version=archive_version,
        route_entries=build_history_manifest_entries(
            archive_version,
            archive_dir,
            routes,
            refreshed_refs,
        ),
        history_policy="sparse_changed_routes_only",
    )
    return archive_dir


def main() -> None:
    """Run the browser smoke test with or without launching a local server."""
    parser = argparse.ArgumentParser(description="Smoke-test FeelIT 3D workspaces in Chromium.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8101")
    parser.add_argument(
        "--screenshot-dir",
        default=str(ROOT / "artifacts" / "frontend_snapshots" / "current"),
        help="Directory where canvas screenshots will be written.",
    )
    parser.add_argument(
        "--archive-version",
        default="",
        help="Optional canonical workspace version used to also archive the captured screenshots under artifacts/frontend_snapshots/history/v<version>.",
    )
    parser.add_argument(
        "--normalize-history",
        action="store_true",
        help="Normalize the tracked frontend history into sparse changed-route archives after capturing the current baseline.",
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="Do not launch a local server; assume --base-url is already running.",
    )
    args = parser.parse_args()

    server_process: subprocess.Popen[str] | None = None
    base_url = args.base_url
    try:
        if not args.no_launch:
            parsed = urlparse(args.base_url)
            host = parsed.hostname or "127.0.0.1"
            port = reserve_free_local_port()
            base_url = f"http://{host}:{port}"
            server_process = subprocess.Popen(
                [sys.executable, "run_app.py", "--no-browser", "--host", host, "--port", str(port)],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            wait_for_server(base_url, timeout_seconds=30)

        run_browser_smoke(base_url, Path(args.screenshot_dir))
        if args.archive_version:
            archive_dir = archive_snapshot_set(Path(args.screenshot_dir), args.archive_version)
            print(f"Archived snapshot set at {archive_dir}")
        elif args.normalize_history:
            normalize_sparse_history(history_root_dir(), SCENES)
            print(f"Normalized sparse snapshot history at {history_root_dir()}")
        print("Browser smoke test passed.")
    finally:
        if server_process is not None:
            server_process.terminate()
            try:
                server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_process.kill()


if __name__ == "__main__":
    main()
