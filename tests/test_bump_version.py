"""Tests for the release bump helper safeguards."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import bump_version


def test_update_version_source_fails_when_app_version_anchor_is_missing(tmp_path: Path, monkeypatch) -> None:
    version_file = tmp_path / "version.py"
    version_file.write_text('NO_VERSION = "x"\n', encoding="utf-8")
    monkeypatch.setattr(bump_version, "VERSION_FILE", version_file)

    with pytest.raises(SystemExit, match="APP_VERSION"):
        bump_version.update_version_source("2.06.001")


def test_update_readme_version_fails_when_current_version_anchor_is_missing(tmp_path: Path, monkeypatch) -> None:
    readme_file = tmp_path / "README.md"
    readme_file.write_text("# FeelIT\n", encoding="utf-8")
    monkeypatch.setattr(bump_version, "README_FILE", readme_file)

    with pytest.raises(SystemExit, match="README version anchor"):
        bump_version.update_readme_version("2.06.001")


def test_update_readme_version_rewrites_the_expected_anchor(tmp_path: Path, monkeypatch) -> None:
    readme_file = tmp_path / "README.md"
    readme_file.write_text("## Current Version\n`2.06.000`\n", encoding="utf-8")
    monkeypatch.setattr(bump_version, "README_FILE", readme_file)

    bump_version.update_readme_version("2.06.001")

    assert "`2.06.001`" in readme_file.read_text(encoding="utf-8")


def test_update_readme_version_rewrites_the_canonical_version_table_row(tmp_path: Path, monkeypatch) -> None:
    readme_file = tmp_path / "README.md"
    readme_file.write_text("| Canonical version | `2.06.000` |\n", encoding="utf-8")
    monkeypatch.setattr(bump_version, "README_FILE", readme_file)

    bump_version.update_readme_version("2.06.001")

    assert "`2.06.001`" in readme_file.read_text(encoding="utf-8")
