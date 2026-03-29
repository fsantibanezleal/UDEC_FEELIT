"""Bump the canonical FeelIT version and synchronize release metadata."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.version import APP_VERSION, VERSION_FORMAT, format_version, parse_version

VERSION_FILE = ROOT / "app" / "core" / "version.py"
README_FILE = ROOT / "README.md"
HISTORY_FILE = ROOT / "docs" / "development_history.md"

VERSION_SOURCE_PATTERN = re.compile(r'APP_VERSION = "(\d+\.\d{2}\.\d{3})"')
README_HEADING_VERSION_PATTERN = re.compile(r"(## Current Version\s+`)([^`]+)(`)", re.MULTILINE)
README_TABLE_VERSION_PATTERN = re.compile(r"(\| Canonical version \| `)([^`]+)(` \|)", re.MULTILINE)


def replace_once_or_fail(
    pattern: re.Pattern[str],
    source: str,
    replacement: str,
    *,
    file_label: str,
    anchor_label: str,
) -> str:
    """Replace one required anchor and fail fast when it is missing or duplicated."""
    updated, replacement_count = pattern.subn(replacement, source, count=1)
    if replacement_count != 1:
        raise SystemExit(
            f"Unable to update {anchor_label} in {file_label}. "
            "Expected exactly one matching anchor.",
        )
    return updated


def bump(value: str, level: str) -> str:
    """Return a bumped workspace version using the padded canonical format."""
    major, minor, patch = parse_version(value)
    if level == "major":
        return format_version(major + 1, 0, 0)
    if level == "minor":
        return format_version(major, minor + 1, 0)
    if level == "patch":
        return format_version(major, minor, patch + 1)
    return level


def bullet_block(lines: list[str], fallback: str) -> str:
    """Format a markdown bullet block."""
    items = lines or [fallback]
    return "\n".join(f"- {item}" for item in items)


def update_version_source(new_version: str) -> None:
    """Update the canonical version file."""
    source = VERSION_FILE.read_text(encoding="utf-8")
    updated = replace_once_or_fail(
        VERSION_SOURCE_PATTERN,
        source,
        f'APP_VERSION = "{new_version}"',
        file_label=str(VERSION_FILE),
        anchor_label="APP_VERSION",
    )
    VERSION_FILE.write_text(updated, encoding="utf-8")


def update_readme_version(new_version: str) -> None:
    """Update the README current-version anchor."""
    source = README_FILE.read_text(encoding="utf-8")
    patterns = (
        (README_HEADING_VERSION_PATTERN, "README current version heading"),
        (README_TABLE_VERSION_PATTERN, "README canonical version row"),
    )
    updated = None
    for pattern, anchor_label in patterns:
        if pattern.search(source):
            updated = replace_once_or_fail(
                pattern,
                source,
                rf"\g<1>{new_version}\g<3>",
                file_label=str(README_FILE),
                anchor_label=anchor_label,
            )
            break
    if updated is None:
        raise SystemExit(
            f"Unable to update the README version anchor in {README_FILE}. "
            "Expected either the current-version heading or the canonical-version table row.",
        )
    README_FILE.write_text(updated, encoding="utf-8")


def update_history_document(
    new_version: str,
    release_date: str,
    summary: str,
    delivered: list[str],
    rationale: list[str],
) -> None:
    """Insert a new release entry at the top of the modern rebuild timeline."""
    source = HISTORY_FILE.read_text(encoding="utf-8")
    heading = f"### v{new_version} ({release_date})"
    if heading in source:
        return

    marker = "## Modern Rebuild Timeline\n\n"
    if marker not in source:
        raise SystemExit("Unable to find the modern rebuild timeline marker.")

    entry = (
        f"{heading}\n\n"
        f"{summary}\n\n"
        f"Delivered:\n\n"
        f"{bullet_block(delivered, 'Release details pending completion.')}\n\n"
        f"Rationale:\n\n"
        f"{bullet_block(rationale, 'Release rationale pending completion.')}\n\n"
    )
    updated = source.replace(marker, marker + entry, 1)
    HISTORY_FILE.write_text(updated, encoding="utf-8")


def main() -> None:
    """Bump FeelIT to the next requested version."""
    parser = argparse.ArgumentParser(description="Bump FeelIT version")
    parser.add_argument(
        "target",
        help=f"major, minor, patch, or an explicit workspace version in {VERSION_FORMAT}",
    )
    parser.add_argument("--date", default=date.today().isoformat(), dest="release_date")
    parser.add_argument(
        "--summary",
        default="Release entry pending summary.",
        help="Short summary paragraph for the development history entry.",
    )
    parser.add_argument(
        "--delivered",
        action="append",
        default=[],
        help="Delivered bullet to append to the history entry. Repeat as needed.",
    )
    parser.add_argument(
        "--rationale",
        action="append",
        default=[],
        help="Rationale bullet to append to the history entry. Repeat as needed.",
    )
    args = parser.parse_args()

    if args.target not in {"major", "minor", "patch"}:
        try:
            parse_version(args.target)
        except ValueError as error:
            raise SystemExit(
                f"Target must be major, minor, patch, or {VERSION_FORMAT}",
            ) from error

    new_version = bump(APP_VERSION, args.target)
    update_version_source(new_version)
    update_readme_version(new_version)
    update_history_document(
        new_version,
        args.release_date,
        args.summary,
        args.delivered,
        args.rationale,
    )
    subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_version.py")], check=True)
    print(new_version)


if __name__ == "__main__":
    main()
