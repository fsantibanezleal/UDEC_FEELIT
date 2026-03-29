"""Factory for selecting the active haptic backend."""

from __future__ import annotations

import os

from app.haptics.base import HapticBackend
from app.haptics.null_backend import NullHapticBackend


def create_haptic_backend() -> HapticBackend:
    """Create the configured haptic backend.

    Current bootstrap behavior always falls back to the null backend. This keeps
    the application runnable while the physical bridge layer is still being built.
    """
    requested = os.getenv("FEELIT_HAPTIC_BACKEND", "null").strip().lower()
    if requested == "null":
        return NullHapticBackend()
    return NullHapticBackend()

