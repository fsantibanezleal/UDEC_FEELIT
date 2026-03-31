"""Bridge-probe contract helpers for future native haptic sidecars."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class HapticBridgeProbeSnapshot(BaseModel):
    """Describe the latest native bridge probe state for one backend."""

    state: str
    summary: str
    executable_path: str | None = None
    backend_slug: str | None = None
    detected_device_count: int | None = None
    detected_devices: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


def native_bridge_root() -> Path:
    """Return the FeelIT native bridge project root."""
    override = os.getenv("FEELIT_NATIVE_BRIDGE_ROOT", "").strip()
    if override:
        return Path(override).expanduser()
    return Path(__file__).resolve().parents[2] / "native"


def default_bridge_output_candidates(backend_slug: str) -> list[Path]:
    """Return the default output locations searched for compiled bridge probes."""
    root = native_bridge_root()
    candidates = [
        root / "build" / backend_slug / "out" / "feelit_bridge_probe.exe",
        root / "build" / backend_slug / "out" / "feelit_bridge_probe",
        root / "build" / backend_slug / "Release" / "feelit_bridge_probe.exe",
        root / "build" / backend_slug / "Debug" / "feelit_bridge_probe.exe",
    ]
    return candidates


def _bridge_command(executable_path: str) -> list[str]:
    """Return the command used to invoke one bridge probe executable."""
    suffix = Path(executable_path).suffix.lower()
    if suffix == ".py":
        return [sys.executable, executable_path]
    if suffix == ".ps1":
        return ["powershell", "-ExecutionPolicy", "Bypass", "-File", executable_path]
    return [executable_path]


def probe_native_bridge(
    executable_path: str | None,
    *,
    backend_slug: str,
    sdk_root: str | None,
    device_selector: str | None = None,
) -> HapticBridgeProbeSnapshot:
    """Run one bridge probe executable and return the parsed probe state."""
    if not executable_path:
        return HapticBridgeProbeSnapshot(
            state="not-configured",
            summary="No native bridge executable is configured or auto-detected yet.",
            backend_slug=backend_slug,
        )

    bridge_path = Path(executable_path).expanduser()
    if not bridge_path.exists():
        return HapticBridgeProbeSnapshot(
            state="missing-executable",
            summary=f"Configured bridge executable is missing: {bridge_path}",
            executable_path=str(bridge_path),
            backend_slug=backend_slug,
        )

    command = _bridge_command(str(bridge_path))
    command.extend(["--backend", backend_slug, "--emit-json"])
    if sdk_root:
        command.extend(["--sdk-root", sdk_root])
    if device_selector:
        command.extend(["--device-selector", device_selector])

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return HapticBridgeProbeSnapshot(
            state="launch-failed",
            summary=f"Bridge probe failed to launch: {error}",
            executable_path=str(bridge_path),
            backend_slug=backend_slug,
        )

    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "No diagnostic output."
        return HapticBridgeProbeSnapshot(
            state="probe-error",
            summary=f"Bridge probe exited with code {completed.returncode}: {stderr}",
            executable_path=str(bridge_path),
            backend_slug=backend_slug,
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return HapticBridgeProbeSnapshot(
            state="invalid-json",
            summary=f"Bridge probe returned invalid JSON: {error}",
            executable_path=str(bridge_path),
            backend_slug=backend_slug,
        )

    summary = str(payload.get("summary", "Bridge probe returned no summary."))
    state = str(payload.get("status", "unknown"))
    devices = [str(item) for item in payload.get("devices", [])]
    device_count = payload.get("device_count")
    if isinstance(device_count, bool) or not isinstance(device_count, int):
        device_count = None

    return HapticBridgeProbeSnapshot(
        state=state,
        summary=summary,
        executable_path=str(bridge_path),
        backend_slug=str(payload.get("backend", backend_slug)),
        detected_device_count=device_count,
        detected_devices=devices,
        payload=payload,
    )
