"""Canonical version metadata for FeelIT."""

from __future__ import annotations

APP_NAME = "FeelIT"
APP_VERSION = "0.2.0"
APP_PUBLISHER = "Felipe Santibanez"


def windows_file_version(version: str = APP_VERSION) -> str:
    """Return a four-part Windows file version string."""
    parts = version.split(".")
    while len(parts) < 4:
        parts.append("0")
    return ".".join(parts[:4])


WINDOWS_FILE_VERSION = windows_file_version()

