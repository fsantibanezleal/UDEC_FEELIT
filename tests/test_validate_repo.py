"""Tests for the repo-managed validation entrypoint."""

from __future__ import annotations

import sys

from scripts.validate_repo import build_validation_plan


def test_unit_plan_runs_pytest_only() -> None:
    plan = build_validation_plan("unit")

    assert [command.label for command in plan] == ["pytest"]
    assert plan[0].argv == (sys.executable, "-m", "pytest", "tests", "-q")


def test_lint_plan_runs_ruff_check() -> None:
    plan = build_validation_plan("lint")

    assert [command.label for command in plan] == ["ruff-check"]
    assert plan[0].argv == (sys.executable, "-m", "ruff", "check", ".")


def test_smoke_plan_can_include_browser_install() -> None:
    plan = build_validation_plan("smoke", install_browser=True)

    assert [command.label for command in plan] == ["playwright-install", "browser-smoke"]
    assert plan[0].argv == (sys.executable, "-m", "playwright", "install", "chromium")
    assert plan[1].argv == (sys.executable, "scripts/browser_scene_smoke.py")


def test_full_plan_can_forward_docs_png_sync() -> None:
    plan = build_validation_plan("full", install_browser=True, sync_docs_png=True)

    assert [command.label for command in plan] == [
        "ruff-check",
        "pytest",
        "playwright-install",
        "browser-smoke",
    ]
    assert plan[-1].argv == (
        sys.executable,
        "scripts/browser_scene_smoke.py",
        "--sync-docs-png",
    )


def test_lint_baseline_plan_is_non_blocking() -> None:
    plan = build_validation_plan("lint-baseline")

    assert [command.label for command in plan] == ["ruff-statistics"]
    assert plan[0].allow_failure is True
