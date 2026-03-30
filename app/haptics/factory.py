"""Factory for selecting the active haptic backend."""

from __future__ import annotations

import os

from app.haptics.base import HapticBackend
from app.haptics.null_backend import NullHapticBackend


def create_haptic_backend(
    *,
    requested_backend: str | None = None,
    selection_summary: str | None = None,
) -> HapticBackend:
    """Create the configured haptic backend.

    Current bootstrap behavior always falls back to the null backend. This keeps
    the application runnable while the physical bridge layer is still being built.
    """
    requested = (requested_backend or os.getenv("FEELIT_HAPTIC_BACKEND", "visual-emulator")).strip().lower()
    if requested in {"null", "visual-emulator"}:
        return NullHapticBackend(selection_summary=selection_summary)
    return NullHapticBackend(selection_summary=selection_summary)
