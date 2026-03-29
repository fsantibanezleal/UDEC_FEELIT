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

from app.core.version import APP_VERSION

VERSION_FILE = ROOT / "app" / "core" / "version.py"
README_FILE = ROOT / "README.md"
HISTORY_FILE = ROOT / "docs" / "development_history.md"

VERSION_PATTERN = re.compile(r'APP_VERSION = "(\d+\.\d+\.\d+)"')
README_VERSION_PATTERN = re.compile(r"(## Current Version\s+`)([^`]+)(`)", re.MULTILINE)


def parse_version(value: str) -> tuple[int, int, int]:
    """Parse a semantic version into a tuple."""
    major, minor, patch = value.split(".")
    return int(major), int(minor), int(patch)


def bump(value: str, level: str) -> str:
    """Return a bumped semantic version."""
    major, minor, patch = parse_version(value)
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return level


def bullet_block(lines: list[str], fallback: str) -> str:
    """Format a markdown bullet block."""
    items = lines or [fallback]
    return "\n".join(f"- {item}" for item in items)


def update_version_source(new_version: str) -> None:
    """Update the canonical version file."""
    source = VERSION_FILE.read_text(encoding="utf-8")
    updated = VERSION_PATTERN.sub(f'APP_VERSION = "{new_version}"', source, count=1)
    VERSION_FILE.write_text(updated, encoding="utf-8")


def update_readme_version(new_version: str) -> None:
    """Update the README current-version anchor."""
    source = README_FILE.read_text(encoding="utf-8")
    updated = README_VERSION_PATTERN.sub(rf"\g<1>{new_version}\g<3>", source, count=1)
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
    parser.add_argument("target", help="major, minor, patch, or an explicit semantic version")
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

    if args.target not in {"major", "minor", "patch"} and not re.fullmatch(
        r"\d+\.\d+\.\d+",
        args.target,
    ):
        raise SystemExit("Target must be major, minor, patch, or X.Y.Z")

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
