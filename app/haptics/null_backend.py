"""Null haptic backend used when no physical device is configured."""

from __future__ import annotations

from app.haptics.base import HapticBackend, HapticBackendStatus


class NullHapticBackend(HapticBackend):
    """Fallback backend for visual-only and API-only execution."""

    def __init__(self) -> None:
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def status(self) -> HapticBackendStatus:
        return HapticBackendStatus(
            backend="null",
            connected=False,
            mode="visual-fallback",
            summary=(
                "No physical haptic device is configured. FeelIT is running in visual "
                "fallback mode with API-safe device abstraction."
            ),
            capabilities=[
                "braille-preview",
                "frontend-shell",
                "api-introspection",
            ],
        )

