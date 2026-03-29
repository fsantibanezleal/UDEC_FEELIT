"""Tests for the canonical padded version format used by FeelIT."""

from __future__ import annotations

from app.core.version import (
    APP_VERSION,
    PACKAGE_VERSION,
    VERSION_PATTERN,
    format_version,
    parse_version,
    windows_file_version_string,
    windows_file_version_tuple,
)


def test_canonical_version_uses_workspace_padding() -> None:
    assert VERSION_PATTERN.fullmatch(APP_VERSION)


def test_format_version_applies_fixed_width_padding() -> None:
    assert format_version(2, 5, 2) == "2.05.002"


def test_parse_version_recovers_numeric_segments() -> None:
    assert parse_version("2.05.002") == (2, 5, 2)


def test_package_version_uses_normalized_numeric_segments() -> None:
    major, minor, patch = parse_version(APP_VERSION)
    assert PACKAGE_VERSION == f"{major}.{minor}.{patch}"


def test_windows_file_version_helpers_keep_display_and_numeric_forms() -> None:
    assert windows_file_version_tuple("2.05.002") == (2, 5, 2, 0)
    assert windows_file_version_string("2.05.002") == "2.05.002.0"
