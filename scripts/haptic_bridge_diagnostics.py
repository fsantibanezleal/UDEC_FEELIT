"""Dump the current FeelIT haptic-runtime and bridge-bootstrap diagnostics as JSON."""

from __future__ import annotations

import json

from app.haptics.runtime_manager import HapticRuntimeManager


def main() -> None:
    """Print one JSON snapshot of the current haptic runtime state."""
    manager = HapticRuntimeManager()
    snapshot = manager.configuration_snapshot()
    print(json.dumps(snapshot.model_dump(), indent=2))


if __name__ == "__main__":
    main()
