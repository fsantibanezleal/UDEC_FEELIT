"""Runtime manager for selectable haptic backend targets and dependency diagnostics."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.haptic_feedback_design import (
    build_haptic_contact_design,
    build_haptic_material_rendering_matrix,
)
from app.haptics.base import HapticBackend
from app.haptics.factory import create_haptic_backend


def local_app_state_dir() -> Path:
    """Return the local writable directory used for user-scoped FeelIT state."""
    if os.name == "nt":
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / "FeelIT"
    return Path.home() / ".feelit"


def runtime_config_path() -> Path:
    """Return the runtime configuration file path, honoring a test override when present."""
    override = os.getenv("FEELIT_HAPTIC_CONFIG_PATH", "").strip()
    if override:
        return Path(override).expanduser()
    return local_app_state_dir() / "haptic_runtime_config.json"


class HapticRuntimeConfig(BaseModel):
    """Persisted user-scoped runtime-selection state for haptic backends."""

    requested_backend: str = "visual-emulator"
    sdk_roots: dict[str, str] = Field(default_factory=dict)
    bridge_paths: dict[str, str] = Field(default_factory=dict)


class HapticBackendCandidate(BaseModel):
    """Describe one backend target as seen by the runtime manager."""

    slug: str
    title: str
    vendor: str
    backend_type: str
    summary: str
    requested: bool
    active: bool
    availability: str
    dependency_state: str
    device_detection_state: str
    can_activate: bool
    supported_devices: list[str] = Field(default_factory=list)
    supported_capabilities: list[str] = Field(default_factory=list)
    expected_env_vars: list[str] = Field(default_factory=list)
    configured_sdk_root: str | None = None
    detected_sdk_root: str | None = None
    configured_bridge_path: str | None = None
    detected_bridge_path: str | None = None
    evidence: list[str] = Field(default_factory=list)
    install_hint: str = ""


class HapticRuntimeSnapshot(BaseModel):
    """Full frontend-facing configuration snapshot for the haptic stack."""

    requested_backend: str
    active_backend: str
    active_backend_title: str
    config_file_label: str
    selection_summary: str
    backends: list[HapticBackendCandidate]
    contact_design: dict[str, Any]
    material_rendering: list[dict[str, Any]]


BACKEND_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "slug": "visual-emulator",
        "title": "Visual Pointer Emulator",
        "vendor": "FeelIT",
        "backend_type": "fallback",
        "summary": "Keyboard-driven stylus proxy for safe no-device execution and scene debugging.",
        "supported_devices": ["Built-in visual fallback"],
        "supported_capabilities": [
            "scene-debug",
            "pointer-emulation",
            "no-device-validation",
        ],
        "expected_env_vars": ["FEELIT_HAPTIC_BACKEND"],
        "sdk_key": None,
        "bridge_key": None,
        "env_sdk_vars": [],
        "env_bridge_vars": [],
        "marker_paths": [],
        "install_hint": "Always available. This is the safe default runtime path.",
    },
    {
        "slug": "openhaptics-touch",
        "title": "OpenHaptics Touch Stack",
        "vendor": "3D Systems",
        "backend_type": "vendor-sdk",
        "summary": (
            "Targets Touch-family devices through an OpenHaptics-compatible native bridge."
        ),
        "supported_devices": ["Touch", "Touch X", "Phantom Omni or Geomagic Touch family"],
        "supported_capabilities": [
            "device-detection",
            "workspace-alignment",
            "force-feedback",
            "button-and-proxy-input",
        ],
        "expected_env_vars": [
            "FEELIT_OPENHAPTICS_SDK_ROOT",
            "OPENHAPTICS_SDK_ROOT",
            "OH_SDK_BASE",
            "FEELIT_OPENHAPTICS_BRIDGE",
        ],
        "sdk_key": "openhaptics",
        "bridge_key": "openhaptics",
        "env_sdk_vars": [
            "FEELIT_OPENHAPTICS_SDK_ROOT",
            "OPENHAPTICS_SDK_ROOT",
            "OH_SDK_BASE",
        ],
        "env_bridge_vars": ["FEELIT_OPENHAPTICS_BRIDGE"],
        "marker_paths": [
            "include/HD/hd.h",
            "include/HDU/hduVector.h",
        ],
        "install_hint": (
            "Install the OpenHaptics SDK, then point FeelIT to the SDK root and the "
            "future bridge executable."
        ),
    },
    {
        "slug": "forcedimension-dhd",
        "title": "Force Dimension DHD Stack",
        "vendor": "Force Dimension",
        "backend_type": "vendor-sdk",
        "summary": (
            "Targets Force Dimension devices through the DHD SDK plus a FeelIT native bridge."
        ),
        "supported_devices": ["Force Dimension haptic devices supported by the DHD SDK"],
        "supported_capabilities": [
            "device-detection",
            "workspace-alignment",
            "force-feedback",
            "servo-loop-telemetry",
        ],
        "expected_env_vars": [
            "FEELIT_FORCEDIMENSION_SDK_ROOT",
            "FORCEDIMENSION_SDK_ROOT",
            "FDSDK_ROOT",
            "FEELIT_FORCEDIMENSION_BRIDGE",
        ],
        "sdk_key": "forcedimension",
        "bridge_key": "forcedimension",
        "env_sdk_vars": [
            "FEELIT_FORCEDIMENSION_SDK_ROOT",
            "FORCEDIMENSION_SDK_ROOT",
            "FDSDK_ROOT",
        ],
        "env_bridge_vars": ["FEELIT_FORCEDIMENSION_BRIDGE"],
        "marker_paths": [
            "include/dhdc.h",
            "include/drdc.h",
        ],
        "install_hint": (
            "Install the Force Dimension SDK, then configure the SDK root and the "
            "future FeelIT bridge path for live device enumeration."
        ),
    },
    {
        "slug": "chai3d-bridge",
        "title": "CHAI3D Bridge Stack",
        "vendor": "CHAI3D",
        "backend_type": "bridge",
        "summary": (
            "Compatibility-oriented native bridge that can aggregate multiple supported "
            "device families behind one haptic scene contract."
        ),
        "supported_devices": [
            "CHAI3D-supported devices and simulated-device development paths",
        ],
        "supported_capabilities": [
            "compatibility-abstraction",
            "proxy-based-contact",
            "scene-level-haptics",
        ],
        "expected_env_vars": [
            "FEELIT_CHAI3D_ROOT",
            "CHAI3D_ROOT",
            "FEELIT_CHAI3D_BRIDGE",
        ],
        "sdk_key": "chai3d",
        "bridge_key": "chai3d",
        "env_sdk_vars": [
            "FEELIT_CHAI3D_ROOT",
            "CHAI3D_ROOT",
        ],
        "env_bridge_vars": ["FEELIT_CHAI3D_BRIDGE"],
        "marker_paths": [
            "src/devices/CGenericHapticDevice.h",
            "src/world/CWorld.h",
        ],
        "install_hint": (
            "Configure the CHAI3D root and the native bridge executable when FeelIT is "
            "ready to test a compatibility-oriented stack."
        ),
    },
)


def _resolve_existing_path(raw_path: str | None) -> str | None:
    """Return one normalized existing path when available."""
    if not raw_path:
        return None
    candidate = Path(raw_path).expanduser()
    try:
        resolved = candidate.resolve()
    except OSError:
        return None
    return str(resolved) if resolved.exists() else None


def _find_sdk_root(
    config: HapticRuntimeConfig,
    definition: dict[str, Any],
) -> tuple[str | None, list[str], str | None]:
    """Return the best detected SDK root plus the evidence trail."""
    evidence: list[str] = []
    sdk_key = definition.get("sdk_key")
    if not sdk_key:
        return None, evidence, None

    configured_raw = config.sdk_roots.get(sdk_key, "").strip() or None
    configured = _resolve_existing_path(configured_raw)
    if configured:
        evidence.append(f"Configured SDK root found: {configured}")
        return configured, evidence, configured_raw
    if configured_raw:
        evidence.append(f"Configured SDK root is missing: {configured_raw}")

    for env_name in definition.get("env_sdk_vars", []):
        env_value = _resolve_existing_path(os.getenv(env_name, "").strip())
        if env_value:
            evidence.append(f"Environment {env_name} points to {env_value}")
            return env_value, evidence, configured_raw

    common_roots = [
        Path("C:/OpenHaptics"),
        Path("C:/Program Files/3D Systems/OpenHaptics"),
        Path("C:/Program Files/Force Dimension/sdk"),
        Path("C:/Program Files/CHAI3D"),
        Path("C:/chai3d"),
    ]
    for candidate in common_roots:
        if not candidate.exists():
            continue
        markers = definition.get("marker_paths", [])
        if any((candidate / marker).exists() for marker in markers):
            resolved = str(candidate.resolve())
            evidence.append(f"Detected SDK root by marker scan: {resolved}")
            return resolved, evidence, configured_raw

    evidence.append("No SDK root was detected.")
    return None, evidence, configured_raw


def _find_bridge_path(
    config: HapticRuntimeConfig,
    definition: dict[str, Any],
) -> tuple[str | None, list[str], str | None]:
    """Return the best detected native bridge path plus the evidence trail."""
    evidence: list[str] = []
    bridge_key = definition.get("bridge_key")
    if not bridge_key:
        return None, evidence, None

    configured_raw = config.bridge_paths.get(bridge_key, "").strip() or None
    configured = _resolve_existing_path(configured_raw)
    if configured:
        evidence.append(f"Configured bridge path found: {configured}")
        return configured, evidence, configured_raw
    if configured_raw:
        evidence.append(f"Configured bridge path is missing: {configured_raw}")

    for env_name in definition.get("env_bridge_vars", []):
        env_value = _resolve_existing_path(os.getenv(env_name, "").strip())
        if env_value:
            evidence.append(f"Environment {env_name} points to {env_value}")
            return env_value, evidence, configured_raw

    evidence.append("No bridge executable was detected.")
    return None, evidence, configured_raw


class HapticRuntimeManager:
    """Coordinate user-scoped haptic runtime selection and dependency diagnostics."""

    def __init__(self) -> None:
        self._config_path = runtime_config_path()
        self._config = self._load_config()
        self._selection_summary = ""
        self._backend = self._create_active_backend()

    def _load_config(self) -> HapticRuntimeConfig:
        """Load persisted configuration when available."""
        if not self._config_path.exists():
            return HapticRuntimeConfig()
        payload = json.loads(self._config_path.read_text(encoding="utf-8"))
        return HapticRuntimeConfig.model_validate(payload)

    def _save_config(self) -> None:
        """Persist the current runtime configuration."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps(self._config.model_dump(), indent=2),
            encoding="utf-8",
        )

    def _create_active_backend(self) -> HapticBackend:
        """Create the currently active backend implementation."""
        requested = self._config.requested_backend
        if requested != "visual-emulator":
            self._selection_summary = (
                f"Requested backend '{requested}' is tracked for diagnostics, but the "
                "native bridge is not implemented yet. FeelIT is running in the visual "
                "pointer-emulator fallback."
            )
            return create_haptic_backend(
                requested_backend="visual-emulator",
                selection_summary=self._selection_summary,
            )

        self._selection_summary = (
            "FeelIT is running with the built-in visual pointer emulator. This remains "
            "the safe default until a native physical-device bridge is attached."
        )
        return create_haptic_backend(
            requested_backend="visual-emulator",
            selection_summary=self._selection_summary,
        )

    def start(self) -> None:
        """Start the currently active backend."""
        self._backend.start()

    def stop(self) -> None:
        """Stop the currently active backend."""
        self._backend.stop()

    @property
    def backend(self) -> HapticBackend:
        """Return the current active backend implementation."""
        return self._backend

    def refresh_runtime(self) -> None:
        """Refresh configuration state and recreate the active backend."""
        self._backend.stop()
        self._backend = self._create_active_backend()
        self._backend.start()

    def configuration_snapshot(self) -> HapticRuntimeSnapshot:
        """Return the full runtime configuration snapshot."""
        candidates: list[HapticBackendCandidate] = []
        for definition in BACKEND_DEFINITIONS:
            slug = definition["slug"]
            requested = self._config.requested_backend == slug
            active = slug == "visual-emulator"

            if slug == "visual-emulator":
                candidates.append(
                    HapticBackendCandidate(
                        slug=slug,
                        title=definition["title"],
                        vendor=definition["vendor"],
                        backend_type=definition["backend_type"],
                        summary=definition["summary"],
                        requested=requested,
                        active=active,
                        availability="ready",
                        dependency_state="builtin",
                        device_detection_state="emulated",
                        can_activate=True,
                        supported_devices=definition["supported_devices"],
                        supported_capabilities=definition["supported_capabilities"],
                        expected_env_vars=definition["expected_env_vars"],
                        install_hint=definition["install_hint"],
                        evidence=["Built into FeelIT and always available."],
                    )
                )
                continue

            sdk_root, sdk_evidence, configured_sdk_root = _find_sdk_root(self._config, definition)
            bridge_path, bridge_evidence, configured_bridge_path = _find_bridge_path(
                self._config,
                definition,
            )
            evidence = sdk_evidence + bridge_evidence

            if sdk_root and bridge_path:
                availability = "sdk-and-bridge-detected"
                dependency_state = "ready-for-native-bridge"
                device_detection_state = "bridge-pending-runtime"
            elif sdk_root:
                availability = "sdk-detected"
                dependency_state = "bridge-missing"
                device_detection_state = "sdk-only"
            else:
                availability = "missing-dependency"
                dependency_state = "sdk-missing"
                device_detection_state = "not-available"

            candidates.append(
                HapticBackendCandidate(
                    slug=slug,
                    title=definition["title"],
                    vendor=definition["vendor"],
                    backend_type=definition["backend_type"],
                    summary=definition["summary"],
                    requested=requested,
                    active=False,
                    availability=availability,
                    dependency_state=dependency_state,
                    device_detection_state=device_detection_state,
                    can_activate=False,
                    supported_devices=definition["supported_devices"],
                    supported_capabilities=definition["supported_capabilities"],
                    expected_env_vars=definition["expected_env_vars"],
                    configured_sdk_root=configured_sdk_root,
                    detected_sdk_root=sdk_root,
                    configured_bridge_path=configured_bridge_path,
                    detected_bridge_path=bridge_path,
                    evidence=evidence,
                    install_hint=definition["install_hint"],
                )
            )

        active_status = self._backend.status()
        return HapticRuntimeSnapshot(
            requested_backend=self._config.requested_backend,
            active_backend=active_status.backend,
            active_backend_title=active_status.backend_title or active_status.backend,
            config_file_label=self._config_path.name,
            selection_summary=self._selection_summary,
            backends=candidates,
            contact_design=build_haptic_contact_design(),
            material_rendering=build_haptic_material_rendering_matrix(),
        )

    def update_configuration(
        self,
        *,
        requested_backend: str,
        sdk_roots: dict[str, str],
        bridge_paths: dict[str, str],
    ) -> HapticRuntimeSnapshot:
        """Persist new runtime-selection preferences and return the refreshed snapshot."""
        valid_slugs = {definition["slug"] for definition in BACKEND_DEFINITIONS}
        if requested_backend not in valid_slugs:
            raise ValueError(f"Unsupported haptic backend selection: {requested_backend}")

        self._config.requested_backend = requested_backend
        self._config.sdk_roots = {key: value.strip() for key, value in sdk_roots.items() if value.strip()}
        self._config.bridge_paths = {
            key: value.strip() for key, value in bridge_paths.items() if value.strip()
        }
        self._save_config()
        self.refresh_runtime()
        return self.configuration_snapshot()
