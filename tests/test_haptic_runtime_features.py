"""Tests for the normalized haptic runtime feature schema."""

from __future__ import annotations

from app.core.haptic_runtime_features import normalize_runtime_features


def test_normalize_runtime_features_merges_direct_and_legacy_values() -> None:
    features = normalize_runtime_features(
        ["force-output-path", "button-proxy-input-path"],
        direct_features=["scheduler_or_servo_loop"],
    )
    assert features == ["force_path", "input_path", "pointer_path", "scheduler_or_servo_loop"]


def test_normalize_runtime_features_deduplicates_values() -> None:
    features = normalize_runtime_features(
        ["force-output-path", "force-feedback-path"],
        direct_features=["force_path", "force_path"],
    )
    assert features == ["force_path"]
