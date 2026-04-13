"""Targeted tests for browser smoke helpers."""

from __future__ import annotations

from scripts.browser_scene_smoke import (
    is_benign_console_warning,
    is_relevant_console_failure,
    target_within_pointer_bounds,
)


def test_benign_gpu_readpixels_warning_is_ignored() -> None:
    line = (
        "/object-explorer console[warning]: "
        "[.WebGL-0x3d240409a300]GL Driver Message (OpenGL, Performance, GL_CLOSE_PATH_NV, High): "
        "GPU stall due to ReadPixels"
    )
    assert is_benign_console_warning(line)
    assert not is_relevant_console_failure(line)


def test_random_hex_digits_do_not_trigger_false_404_failure() -> None:
    line = "/object-explorer console[warning]: [.WebGL-0x3d240409a300] diagnostic banner"
    assert not is_relevant_console_failure(line)


def test_real_console_error_still_fails() -> None:
    line = "/object-explorer console[error]: Uncaught ReferenceError: foo is not defined"
    assert is_relevant_console_failure(line)


def test_real_404_log_still_fails() -> None:
    line = '/object-explorer console[warning]: GET /static/vendor/example.js 404 Not Found'
    assert is_relevant_console_failure(line)


def test_failed_to_load_log_still_fails() -> None:
    line = "/object-explorer console[warning]: Failed to load resource: net::ERR_FILE_NOT_FOUND"
    assert is_relevant_console_failure(line)


def test_target_within_pointer_bounds_accepts_reachable_target() -> None:
    target = {"position": [0.0, 0.24, 1.18], "radius": 0.32}
    bounds = {"min": [-1.4, 0.14, 0.6], "max": [1.4, 1.45, 1.7]}
    assert target_within_pointer_bounds(target, bounds)


def test_target_within_pointer_bounds_rejects_out_of_bounds_target() -> None:
    target = {"position": [0.0, 0.24, 1.18], "radius": 0.32}
    bounds = {"min": [-1.4, 0.14, 0.9], "max": [1.4, 1.45, 1.1]}
    assert not target_within_pointer_bounds(target, bounds)
