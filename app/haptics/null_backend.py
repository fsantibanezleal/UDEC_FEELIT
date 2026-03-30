"""Null haptic backend used when no physical device is configured."""

from __future__ import annotations

from app.haptics.base import HapticBackend, HapticBackendStatus


class NullHapticBackend(HapticBackend):
    """Fallback backend for visual-only and API-only execution."""

    def __init__(self, *, selection_summary: str | None = None) -> None:
        self._running = False
        self._selection_summary = selection_summary

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def status(self) -> HapticBackendStatus:
        return HapticBackendStatus(
            backend="visual-emulator",
            backend_title="Visual Pointer Emulator",
            connected=False,
            mode="visual-fallback",
            summary=self._selection_summary
            or (
                "No physical haptic device is configured. FeelIT is running in visual "
                "fallback mode with API-safe device abstraction."
            ),
            capabilities=[
                "pointer-emulation",
                "braille-preview",
                "frontend-shell",
                "api-introspection",
            ],
        )
