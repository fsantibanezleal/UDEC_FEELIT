"""Run FeelIT repository validation through one repo-managed entrypoint."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ValidationCommand:
    """Describe one validation command executed by this repo-managed wrapper."""

    label: str
    argv: tuple[str, ...]
    allow_failure: bool = False


def build_validation_plan(
    mode: str,
    *,
    install_browser: bool = False,
    sync_docs_png: bool = False,
) -> tuple[ValidationCommand, ...]:
    """Return the ordered validation commands for one requested validation mode."""
    python = sys.executable
    plan: list[ValidationCommand] = []

    if mode in {"unit", "full"}:
        plan.append(
            ValidationCommand(
                label="pytest",
                argv=(python, "-m", "pytest", "tests", "-q"),
            ),
        )

    if mode in {"smoke", "full"}:
        if install_browser:
            plan.append(
                ValidationCommand(
                    label="playwright-install",
                    argv=(python, "-m", "playwright", "install", "chromium"),
                ),
            )
        smoke_args = [python, "scripts/browser_scene_smoke.py"]
        if sync_docs_png:
            smoke_args.append("--sync-docs-png")
        plan.append(
            ValidationCommand(
                label="browser-smoke",
                argv=tuple(smoke_args),
            ),
        )

    if mode == "lint-baseline":
        plan.append(
            ValidationCommand(
                label="ruff-statistics",
                argv=(python, "-m", "ruff", "check", ".", "--statistics"),
                allow_failure=True,
            ),
        )

    if not plan:
        raise ValueError(f"Unsupported validation mode: {mode}")

    return tuple(plan)


def run_validation_plan(plan: tuple[ValidationCommand, ...]) -> None:
    """Execute one planned validation sequence and stop on the first hard failure."""
    for command in plan:
        print(f"[validate] {command.label}: {' '.join(command.argv)}")
        completed = subprocess.run(command.argv, cwd=ROOT, check=False)
        if completed.returncode != 0 and not command.allow_failure:
            raise SystemExit(completed.returncode)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the repo-managed validation entrypoint."""
    parser = argparse.ArgumentParser(description="Run FeelIT validation workflows.")
    parser.add_argument(
        "--mode",
        choices=("unit", "smoke", "full", "lint-baseline"),
        default="unit",
        help="Validation mode to run.",
    )
    parser.add_argument(
        "--install-browser",
        action="store_true",
        help="Install Playwright Chromium before running browser-smoke validation.",
    )
    parser.add_argument(
        "--sync-docs-png",
        action="store_true",
        help="Pass --sync-docs-png through to the browser-smoke workflow.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Run FeelIT validation from a stable repo-managed CLI."""
    args = parse_args(argv)
    plan = build_validation_plan(
        args.mode,
        install_browser=args.install_browser,
        sync_docs_png=args.sync_docs_png,
    )
    run_validation_plan(plan)


if __name__ == "__main__":
    main()
