"""Run a browser smoke test against the three FeelIT 3D workspaces."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class SceneSpec:
    """Describe one user-facing 3D workspace to validate."""

    route: str
    canvas_selector: str
    min_unique_colors: int


SCENES: tuple[SceneSpec, ...] = (
    SceneSpec(route="/object-explorer", canvas_selector="#object-canvas", min_unique_colors=1200),
    SceneSpec(route="/braille-reader", canvas_selector="#braille-canvas", min_unique_colors=1500),
    SceneSpec(route="/haptic-desktop", canvas_selector="#desktop-canvas", min_unique_colors=1500),
)


def wait_for_server(process: subprocess.Popen[str], timeout_seconds: int) -> None:
    """Wait for the local FeelIT server to report readiness."""
    deadline = time.time() + timeout_seconds
    log_lines: list[str] = []
    while time.time() < deadline:
        line = process.stdout.readline()
        if line:
            log_lines.append(line.rstrip())
            if "Uvicorn running on" in line or "Application startup complete" in line:
                return
        else:
            time.sleep(0.2)

    recent = "\n".join(log_lines[-20:])
    raise SystemExit(f"Server did not become ready within {timeout_seconds} seconds.\n{recent}")


def measure_canvas_colors(image_path: Path) -> int:
    """Return the number of unique RGBA colors present in the image."""
    image = Image.open(image_path).convert("RGBA")
    colors = image.getcolors(maxcolors=10_000_000)
    return len(colors) if colors else 10_000_000


def run_browser_smoke(base_url: str, screenshot_dir: Path) -> None:
    """Validate that each workspace loads and produces a non-trivial canvas image."""
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        for scene in SCENES:
            console_messages: list[str] = []
            page_errors: list[str] = []
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

            page.goto(f"{base_url}{scene.route}", wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(2_200)

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
                    f"{scene.route} canvas looks under-rendered: "
                    f"{unique_colors} unique colors < {scene.min_unique_colors}",
                )
            if version_text in {"", "v--", "Loading", "Error"}:
                failures.append(f"{scene.route} runtime version slot did not initialize: {version_text!r}")
            if api_status_text in {"", "Loading", "error"}:
                failures.append(f"{scene.route} API status slot did not initialize: {api_status_text!r}")
            if error_overlay_count:
                failures.append(f"{scene.route} rendered a visible stage boot error overlay")
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

            print(
                f"{scene.route}: unique_colors={unique_colors} "
                f"version={version_text} api_status={api_status_text} "
                f"screenshot={screenshot_path}",
            )
            page.close()

        browser.close()

    if failures:
        raise SystemExit("Browser smoke test failed:\n- " + "\n- ".join(failures))


def main() -> None:
    """Run the browser smoke test with or without launching a local server."""
    parser = argparse.ArgumentParser(description="Smoke-test FeelIT 3D workspaces in Chromium.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8101")
    parser.add_argument(
        "--screenshot-dir",
        default=str(ROOT / "artifacts" / "browser_smoke"),
        help="Directory where canvas screenshots will be written.",
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="Do not launch a local server; assume --base-url is already running.",
    )
    args = parser.parse_args()

    server_process: subprocess.Popen[str] | None = None
    try:
        if not args.no_launch:
            server_process = subprocess.Popen(
                [sys.executable, "run_app.py"],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            wait_for_server(server_process, timeout_seconds=30)

        run_browser_smoke(args.base_url, Path(args.screenshot_dir))
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
