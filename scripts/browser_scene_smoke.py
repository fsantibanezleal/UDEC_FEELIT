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
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "routes": entries,
    }
    if history_policy:
        manifest["history_policy"] = history_policy
        manifest["changed_routes"] = [
            entry["route"] for entry in entries if entry.get("archived")
        ]
    (target_dir / "snapshot_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


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
            if scene.route == "/braille-reader":
                page.wait_for_function(
                    """
                    () => {
                      const documents = document.querySelectorAll('#library-document-select option').length;
                      const title = document.querySelector('#summary-document-title')?.textContent?.trim() ?? '';
                      return documents > 0 && title !== '' && title !== 'Loading';
                    }
                    """,
                    timeout=15_000,
                )
            if scene.route == "/haptic-desktop":
                persisted_view = {
                    "position": [6.15, 4.05, 2.35],
                    "target": [0.4, 0.52, -0.28],
                    "zoom": 1,
                }
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
                    if not cycle_focus_to(page, "documents"):
                        failures.append("/haptic-desktop could not focus the documents folder from the file browser root")
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
                        if not cycle_focus_to(page, "documents"):
                            failures.append("/haptic-desktop could not refocus the documents folder from the file browser root")
                        else:
                            page.locator("#focus-activate").click()
                            page.wait_for_timeout(1_200)
                            scene_in_documents = (page.locator("#desktop-scene-code").text_content() or "").strip()
                            path_in_documents = (page.locator("#desktop-scene-path").text_content() or "").strip()
                            if scene_in_documents != "file-browser" or "documents" not in path_in_documents:
                                failures.append(
                                    f"/haptic-desktop did not enter the documents folder correctly; scene={scene_in_documents!r} path={path_in_documents!r}",
                                )
                            if focused_label(page) != "Browser":
                                failures.append(
                                    f"/haptic-desktop did not land on the browser hub after entering documents; focus={focused_label(page)!r}",
                                )
                    if not cycle_focus_to(page, "alice_in_wonderland.txt"):
                        failures.append("/haptic-desktop could not focus a supported text file inside documents")
                    else:
                        focus_action = (page.locator("#desktop-focus-action").text_content() or "").strip()
                        if "Braille reading scene" not in focus_action:
                            failures.append(
                                f"/haptic-desktop supported text file did not advertise the Braille reading scene action; action={focus_action!r}",
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
            if scene.route == "/braille-reader":
                document_options = page.locator("#library-document-select option").count()
                audio_options = page.locator("#library-audio-select option").count()
                document_title = (page.locator("#summary-document-title").text_content() or "").strip()
                if document_options == 0:
                    failures.append("/braille-reader did not populate the internal document library selector")
                if audio_options == 0:
                    failures.append("/braille-reader did not populate the internal audio library selector")
                if document_title in {"", "Loading"}:
                    failures.append("/braille-reader did not initialize the active library document summary")
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
