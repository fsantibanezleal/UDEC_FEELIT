"""Canonical version metadata and formatting helpers for FeelIT."""

from __future__ import annotations

import re

APP_NAME = "FeelIT"
APP_VERSION = "2.06.001"
APP_PUBLISHER = "Felipe Santibanez"
VERSION_FORMAT = "X.XX.XXX"
VERSION_PATTERN = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d{2})\.(?P<patch>\d{3})$")


def parse_version(version: str = APP_VERSION) -> tuple[int, int, int]:
    """Parse one workspace version string in the canonical padded format."""
    match = VERSION_PATTERN.fullmatch(version)
    if not match:
        raise ValueError(
            f"Invalid version {version!r}. Expected canonical workspace format {VERSION_FORMAT}.",
        )
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


def format_version(major: int, minor: int, patch: int) -> str:
    """Return one canonical workspace version string with fixed-width padding."""
    return f"{major}.{minor:02d}.{patch:03d}"


def normalized_package_version(version: str = APP_VERSION) -> str:
    """Return a packaging-safe normalized version without display padding."""
    major, minor, patch = parse_version(version)
    return f"{major}.{minor}.{patch}"


def windows_file_version_tuple(version: str = APP_VERSION) -> tuple[int, int, int, int]:
    """Return the numeric Windows file-version tuple."""
    major, minor, patch = parse_version(version)
    return major, minor, patch, 0


def windows_file_version_string(version: str = APP_VERSION) -> str:
    """Return the padded Windows file-version string for display metadata."""
    major, minor, patch, build = windows_file_version_tuple(version)
    return f"{major}.{minor:02d}.{patch:03d}.{build}"


PACKAGE_VERSION = normalized_package_version()
WINDOWS_FILE_VERSION = windows_file_version_string()
WINDOWS_FILE_VERSION_TUPLE = windows_file_version_tuple()

