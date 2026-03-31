"""Runtime manager for selectable haptic backend targets and dependency diagnostics."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.haptics.bridge_probe import (
    HapticBridgeProbeSnapshot,
    default_bridge_output_candidates,
    native_bridge_root,
    probe_native_bridge,
)
from app.core.haptic_feedback_design import (
    build_haptic_contact_design,
    build_haptic_material_rendering_matrix,
)
from app.core.haptic_contact_rollout import build_haptic_contact_rollout
from app.core.haptic_scene_contracts import build_haptic_scene_contract
from app.haptics.base import HapticBackend
from app.haptics.factory import create_haptic_backend
from app.haptics.toolchain import ToolchainComponentStatus, build_native_toolchain_statuses


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
    device_selectors: dict[str, str] = Field(default_factory=dict)


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
    driver_state: str
    device_detection_state: str
    can_activate: bool
    supported_devices: list[str] = Field(default_factory=list)
    supported_capabilities: list[str] = Field(default_factory=list)
    expected_env_vars: list[str] = Field(default_factory=list)
    configured_sdk_root: str | None = None
    detected_sdk_root: str | None = None
    configured_bridge_path: str | None = None
    detected_bridge_path: str | None = None
    detected_driver_root: str | None = None
    configured_device_selector: str | None = None
    bridge_probe_state: str = "not-run"
    bridge_probe_summary: str = ""
    detected_device_count: int | None = None
    detected_devices: list[str] = Field(default_factory=list)
    reported_capabilities: list[str] = Field(default_factory=list)
    probe_notes: list[str] = Field(default_factory=list)
    probe_enumeration_mode: str | None = None
    probe_capability_scope: str | None = None
    evidence: list[str] = Field(default_factory=list)
    install_hint: str = ""


class HapticBridgeWorkspaceStatus(BaseModel):
    """Describe the native bridge build workspace and recommended commands."""

    source_root: str
    build_root_pattern: str
    bootstrap_script_path: str
    diagnostics_script_path: str
    probe_binary_name: str
    preferred_generator: str
    preferred_compiler: str
    toolchain_ready: bool
    configure_command: str
    build_command: str
    run_probe_command: str
    notes: list[str] = Field(default_factory=list)


class HapticRuntimeSnapshot(BaseModel):
    """Full frontend-facing configuration snapshot for the haptic stack."""

    requested_backend: str
    active_backend: str
    active_backend_title: str
    config_file_label: str
    selection_summary: str
    backends: list[HapticBackendCandidate]
    toolchains: list[ToolchainComponentStatus]
    bridge_workspace: HapticBridgeWorkspaceStatus
    contact_design: dict[str, Any]
    material_rendering: list[dict[str, Any]]
    scene_contract: dict[str, Any]
    contact_rollout: dict[str, Any]


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
        "search_terms": ["OpenHaptics", "Touch Device Driver", "Geomagic Touch"],
        "driver_search_terms": ["Touch Device Driver", "Geomagic Touch", "OpenHaptics"],
        "marker_paths": [
            "include/HD/hd.h",
            "include/HDU/hduVector.h",
        ],
        "runtime_markers": [
            "lib/hd.lib",
            "lib/hdu.lib",
            "bin/hd.dll",
            "bin/hdu.dll",
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
        "search_terms": ["Force Dimension", "DHD SDK"],
        "driver_search_terms": ["Force Dimension"],
        "marker_paths": [
            "include/dhdc.h",
            "include/drdc.h",
        ],
        "runtime_markers": [
            "lib/dhd.lib",
            "lib/drd.lib",
            "bin/dhd64.dll",
            "bin/drd64.dll",
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
        "search_terms": ["CHAI3D"],
        "driver_search_terms": ["CHAI3D"],
        "marker_paths": [
            "src/devices/CGenericHapticDevice.h",
            "src/world/CWorld.h",
        ],
        "runtime_markers": [
            "src/devices/CGenericHapticDevice.h",
            "src/world/CWorld.h",
            "CMakeLists.txt",
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


def _iter_registry_install_locations(search_terms: list[str]) -> list[tuple[str, str]]:
    """Return install locations from the Windows uninstall registry matching search terms."""
    if os.name != "nt":
        return []

    try:
        import winreg
    except ImportError:
        return []

    normalized_terms = [term.casefold() for term in search_terms]
    registry_hives = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    hits: list[tuple[str, str]] = []

    for hive, subkey_path in registry_hives:
        try:
            root_key = winreg.OpenKey(hive, subkey_path)
        except OSError:
            continue

        try:
            index = 0
            while True:
                subkey_name = winreg.EnumKey(root_key, index)
                index += 1
                try:
                    subkey = winreg.OpenKey(root_key, subkey_name)
                except OSError:
                    continue

                fields: list[str] = []
                install_location = ""
                for value_name in ("DisplayName", "Publisher", "InstallLocation"):
                    try:
                        value, _ = winreg.QueryValueEx(subkey, value_name)
                    except OSError:
                        value = ""
                    if value_name == "InstallLocation":
                        install_location = str(value or "")
                    fields.append(str(value or ""))

                haystack = " ".join(fields).casefold()
                if not any(term in haystack for term in normalized_terms):
                    continue

                resolved = _resolve_existing_path(install_location)
                if resolved:
                    hits.append((fields[0] or subkey_name, resolved))
        except OSError:
            pass

    unique_hits: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    for display_name, path in hits:
        if path in seen_paths:
            continue
        seen_paths.add(path)
        unique_hits.append((display_name, path))
    return unique_hits


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

    for display_name, install_location in _iter_registry_install_locations(
        definition.get("search_terms", []),
    ):
        markers = definition.get("marker_paths", [])
        if any((Path(install_location) / marker).exists() for marker in markers):
            evidence.append(
                f"Registry installation match '{display_name}' exposes SDK markers at {install_location}",
            )
            return install_location, evidence, configured_raw

    common_roots = [
        Path("C:/OpenHaptics"),
        Path("C:/Program Files/3D Systems/OpenHaptics"),
        Path("C:/Program Files/3D Systems/Touch Device Driver"),
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


def _find_driver_root(definition: dict[str, Any]) -> tuple[str | None, list[str]]:
    """Return the best detected driver-install root plus the evidence trail."""
    evidence: list[str] = []
    for display_name, install_location in _iter_registry_install_locations(
        definition.get("driver_search_terms", []),
    ):
        evidence.append(f"Registry driver match '{display_name}' at {install_location}")
        return install_location, evidence

    evidence.append("No driver installation was detected.")
    return None, evidence


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

    for candidate in default_bridge_output_candidates(str(definition["slug"])):
        detected = _resolve_existing_path(candidate)
        if detected:
            evidence.append(f"Detected native bridge scaffold output: {detected}")
            return detected, evidence, configured_raw

    evidence.append("No bridge executable was detected.")
    return None, evidence, configured_raw


def _build_bridge_workspace_status(
    toolchains: list[ToolchainComponentStatus],
) -> HapticBridgeWorkspaceStatus:
    """Return the current native bridge workspace and bootstrap-command summary."""
    toolchain_map = {tool.slug: tool for tool in toolchains}
    native_root = native_bridge_root().resolve()
    build_root_pattern = native_root / "build" / "<backend-slug>"
    bootstrap_script_path = Path(__file__).resolve().parents[2] / "scripts" / "Bootstrap_HapticBridge.ps1"
    diagnostics_script_path = Path(__file__).resolve().parents[2] / "scripts" / "haptic_bridge_diagnostics.py"

    cmake_tool = toolchain_map.get("cmake")
    ninja_tool = toolchain_map.get("ninja")
    clang_tool = toolchain_map.get("clang++")
    msbuild_tool = toolchain_map.get("msbuild")
    rc_tool = toolchain_map.get("resource-compiler")

    if cmake_tool and cmake_tool.status == "ready" and ninja_tool and ninja_tool.status == "ready":
        generator = "Ninja"
    elif msbuild_tool and msbuild_tool.status == "ready":
        generator = "Visual Studio 17 2022"
    else:
        generator = "Ninja"

    if clang_tool and clang_tool.status == "ready":
        compiler = "clang++"
    elif msbuild_tool and msbuild_tool.status == "ready":
        compiler = "MSVC"
    else:
        compiler = "Not ready"

    toolchain_ready = (
        bool(cmake_tool and cmake_tool.status == "ready")
        and bool(rc_tool and rc_tool.status in {"ready", "detected-without-version"})
        and (
            bool(ninja_tool and ninja_tool.status == "ready" and clang_tool and clang_tool.status == "ready")
            or bool(msbuild_tool and msbuild_tool.status == "ready")
        )
    )
    configure_command = (
        r".\scripts\Bootstrap_HapticBridge.ps1 -Backend <backend-slug> -SdkRoot <sdk-root> -BuildType Release"
    )
    build_command = (
        r".\scripts\Bootstrap_HapticBridge.ps1 -Backend <backend-slug> -SdkRoot <sdk-root> -BuildType Release -Build"
    )
    run_probe_command = (
        r".\native\build\<backend-slug>\out\feelit_bridge_probe.exe --backend <backend-slug> --sdk-root <sdk-root> --emit-json"
    )

    notes = [
        "The bridge scaffold is compiled without vendor SDK linkage so the probe contract can be validated early.",
        "The Force Dimension DHD path can now reach runtime load and device enumeration, OpenHaptics can now reach a conservative default-device probe with reported capability channels, and CHAI3D still remains a scaffold-level bridge target.",
        "CMake plus a Windows resource compiler and either Ninja with clang++ or MSBuild is required to build the scaffold locally.",
    ]
    return HapticBridgeWorkspaceStatus(
        source_root=str(native_root),
        build_root_pattern=str(build_root_pattern),
        bootstrap_script_path=str(bootstrap_script_path),
        diagnostics_script_path=str(diagnostics_script_path),
        probe_binary_name="feelit_bridge_probe.exe",
        preferred_generator=generator,
        preferred_compiler=compiler,
        toolchain_ready=toolchain_ready,
        configure_command=configure_command,
        build_command=build_command,
        run_probe_command=run_probe_command,
        notes=notes,
    )


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
        toolchains = build_native_toolchain_statuses()
        bridge_workspace = _build_bridge_workspace_status(toolchains)
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
                        driver_state="builtin",
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
            driver_root, driver_evidence = _find_driver_root(definition)
            bridge_path, bridge_evidence, configured_bridge_path = _find_bridge_path(
                self._config,
                definition,
            )
            configured_device_selector = (
                self._config.device_selectors.get(str(definition.get("sdk_key") or ""), "").strip()
                or None
            )
            bridge_probe = probe_native_bridge(
                bridge_path,
                backend_slug=slug,
                sdk_root=sdk_root,
                device_selector=configured_device_selector,
            )
            reported_capabilities = [
                str(item).strip()
                for item in bridge_probe.payload.get("reported_capabilities", [])
                if str(item).strip()
            ]
            probe_notes = [
                str(item).strip()
                for item in bridge_probe.payload.get("probe_notes", [])
                if str(item).strip()
            ]
            resolved_symbols = [
                str(item).strip()
                for item in bridge_probe.payload.get("resolved_symbols", [])
                if str(item).strip()
            ]
            open_attempt_labels = [
                str(item).strip()
                for item in bridge_probe.payload.get("open_attempt_labels", [])
                if str(item).strip()
            ]
            enumeration_mode = str(bridge_probe.payload.get("enumeration_mode", "")).strip() or None
            capability_scope = str(bridge_probe.payload.get("capability_scope", "")).strip() or None
            evidence = sdk_evidence + driver_evidence + bridge_evidence
            if bridge_probe.summary:
                evidence.append(f"Bridge probe: {bridge_probe.summary}")
            if configured_device_selector:
                evidence.append(f"Configured device selector: {configured_device_selector}")
            runtime_library = str(bridge_probe.payload.get("runtime_library", "")).strip()
            runtime_load_state = str(bridge_probe.payload.get("runtime_load_state", "")).strip()
            sdk_version = str(bridge_probe.payload.get("sdk_version", "")).strip()
            if runtime_library:
                evidence.append(f"Bridge runtime library: {runtime_library}")
            if runtime_load_state:
                evidence.append(f"Bridge runtime load state: {runtime_load_state}")
            if sdk_version:
                evidence.append(f"Bridge SDK version: {sdk_version}")
            if enumeration_mode:
                evidence.append(f"Bridge enumeration mode: {enumeration_mode}")
            if capability_scope:
                evidence.append(f"Bridge capability scope: {capability_scope}")
            if resolved_symbols:
                evidence.append(f"Bridge symbols: {', '.join(resolved_symbols)}")
            if open_attempt_labels:
                evidence.append(f"Bridge open attempts: {', '.join(open_attempt_labels)}")
            if reported_capabilities:
                evidence.append(
                    f"Bridge reported capabilities: {', '.join(reported_capabilities)}",
                )
            evidence.extend(f"Probe note: {note}" for note in probe_notes)

            if bridge_probe.state == "ready" and (bridge_probe.detected_device_count or 0) > 0:
                availability = "devices-detected"
                dependency_state = "native-bridge-ready"
                driver_state = "installed" if driver_root else "unknown"
                device_detection_state = "devices-detected"
                can_activate = True
            elif bridge_probe.state in {"runtime-loaded-no-devices", "runtime-loaded-capability-ready"}:
                availability = "runtime-loaded-no-devices"
                dependency_state = "native-runtime-loaded"
                driver_state = "installed" if driver_root else "unknown"
                device_detection_state = (
                    "runtime-loaded-no-enumeration"
                    if bridge_probe.state == "runtime-loaded-capability-ready"
                    else "no-devices-detected"
                )
                can_activate = False
            elif bridge_probe.state in {
                "runtime-library-missing",
                "runtime-load-failed",
                "runtime-symbol-missing",
                "device-open-failed",
            }:
                availability = bridge_probe.state
                dependency_state = "native-runtime-probe-failed"
                driver_state = "installed" if driver_root else "unknown"
                device_detection_state = "probe-failed"
                can_activate = False
            elif bridge_probe.state == "scaffold-only":
                availability = "bridge-scaffold-detected"
                dependency_state = "probe-contract-ready"
                driver_state = "installed" if driver_root else "unknown"
                device_detection_state = "bridge-scaffold-only"
                can_activate = False
            elif sdk_root and driver_root and bridge_path:
                availability = "sdk-driver-and-bridge-detected"
                dependency_state = "ready-for-bridge-probe"
                driver_state = "installed"
                device_detection_state = "bridge-pending-probe"
                can_activate = False
            elif sdk_root and bridge_path:
                availability = "sdk-and-bridge-detected"
                dependency_state = "driver-or-probe-missing"
                driver_state = "missing"
                device_detection_state = "bridge-pending-probe"
                can_activate = False
            elif sdk_root:
                availability = "sdk-detected"
                dependency_state = "bridge-missing"
                driver_state = "installed" if driver_root else "missing"
                device_detection_state = "sdk-only"
                can_activate = False
            else:
                availability = "missing-dependency"
                dependency_state = "sdk-missing"
                driver_state = "installed" if driver_root else "missing"
                device_detection_state = "not-available"
                can_activate = False

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
                    driver_state=driver_state,
                    device_detection_state=device_detection_state,
                    can_activate=can_activate,
                    supported_devices=definition["supported_devices"],
                    supported_capabilities=definition["supported_capabilities"],
                    expected_env_vars=definition["expected_env_vars"],
                    configured_sdk_root=configured_sdk_root,
                    detected_sdk_root=sdk_root,
                    configured_bridge_path=configured_bridge_path,
                    detected_bridge_path=bridge_path,
                    detected_driver_root=driver_root,
                    configured_device_selector=configured_device_selector,
                    bridge_probe_state=bridge_probe.state,
                    bridge_probe_summary=bridge_probe.summary,
                    detected_device_count=bridge_probe.detected_device_count,
                    detected_devices=bridge_probe.detected_devices,
                    reported_capabilities=reported_capabilities,
                    probe_notes=probe_notes,
                    probe_enumeration_mode=enumeration_mode,
                    probe_capability_scope=capability_scope,
                    evidence=evidence,
                    install_hint=definition["install_hint"],
                )
            )

        active_status = self._backend.status()
        backend_payloads = [candidate.model_dump() for candidate in candidates]
        return HapticRuntimeSnapshot(
            requested_backend=self._config.requested_backend,
            active_backend=active_status.backend,
            active_backend_title=active_status.backend_title or active_status.backend,
            config_file_label=self._config_path.name,
            selection_summary=self._selection_summary,
            backends=candidates,
            toolchains=toolchains,
            bridge_workspace=bridge_workspace,
            contact_design=build_haptic_contact_design(),
            material_rendering=build_haptic_material_rendering_matrix(),
            scene_contract=build_haptic_scene_contract(),
            contact_rollout=build_haptic_contact_rollout(backend_payloads),
        )

    def update_configuration(
        self,
        *,
        requested_backend: str,
        sdk_roots: dict[str, str],
        bridge_paths: dict[str, str],
        device_selectors: dict[str, str] | None = None,
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
        self._config.device_selectors = {
            key: value.strip() for key, value in (device_selectors or {}).items() if value.strip()
        }
        self._save_config()
        self.refresh_runtime()
        return self.configuration_snapshot()
