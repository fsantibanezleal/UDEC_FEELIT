"""Integration tests for the native haptic bridge probe scaffold."""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest

from app.haptics.bridge_probe import probe_native_bridge
from app.haptics.runtime_manager import HapticRuntimeManager
from app.haptics.toolchain import ToolchainComponentStatus, build_native_toolchain_statuses

ROOT = Path(__file__).resolve().parent.parent


def _toolchain_map() -> dict[str, ToolchainComponentStatus]:
    """Return the native bridge toolchain statuses keyed by slug."""
    return {status.slug: status for status in build_native_toolchain_statuses()}


def _require_native_build_support() -> dict[str, ToolchainComponentStatus]:
    """Skip when the current host cannot build the native bridge scaffold."""
    if os.name != "nt":
        pytest.skip("The native bridge bootstrap integration is currently validated on Windows only.")

    statuses = _toolchain_map()
    cmake_ready = statuses.get("cmake", ToolchainComponentStatus(slug="", title="", status="missing")).status == "ready"
    rc_ready = statuses.get("resource-compiler", ToolchainComponentStatus(slug="", title="", status="missing")).status in {
        "ready",
        "detected-without-version",
    }
    ninja_ready = statuses.get("ninja", ToolchainComponentStatus(slug="", title="", status="missing")).status == "ready"
    clang_ready = statuses.get("clang++", ToolchainComponentStatus(slug="", title="", status="missing")).status == "ready"
    msbuild_ready = statuses.get("msbuild", ToolchainComponentStatus(slug="", title="", status="missing")).status == "ready"

    if not (cmake_ready and rc_ready and ((ninja_ready and clang_ready) or msbuild_ready)):
        pytest.skip("The native bridge build toolchain is not ready on this host.")
    return statuses


def _build_mock_forcedimension_sdk(sdk_root: Path, clang_path: str) -> None:
    """Create a minimal SDK root with a mock DHD runtime DLL."""
    include_dir = sdk_root / "include"
    lib_dir = sdk_root / "lib"
    bin_dir = sdk_root / "bin"
    include_dir.mkdir(parents=True, exist_ok=True)
    lib_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    (include_dir / "dhdc.h").write_text("// mock DHD header\n", encoding="utf-8")
    (include_dir / "drdc.h").write_text("// mock DRD header\n", encoding="utf-8")
    (lib_dir / "dhd.lib").write_text("", encoding="utf-8")
    (lib_dir / "drd.lib").write_text("", encoding="utf-8")

    runtime_source = sdk_root / "mock_dhd_runtime.cpp"
    runtime_source.write_text(
        textwrap.dedent(
            """
            #if defined(_WIN32)
            #define EXPORT __declspec(dllexport)
            #else
            #define EXPORT
            #endif

            extern "C" {
            EXPORT int dhdGetDeviceCount() { return 2; }
            EXPORT int dhdOpen() { return 0; }
            EXPORT int dhdOpenID(char id) { return static_cast<int>(id); }
            EXPORT int dhdClose(char) { return 0; }
            EXPORT const char* dhdErrorGetLastStr() { return "No error"; }
            EXPORT const char* dhdGetSDKVersionStr() { return "Mock DHD SDK 3.14.0"; }
            EXPORT const char* dhdGetSystemName(char id) {
              return id == 1 ? "Mock OMEGA.7 Left" : "Mock SIGMA.7";
            }
            }
            """,
        ).strip(),
        encoding="utf-8",
    )

    subprocess.run(
        [
            clang_path,
            "-shared",
            "-o",
            str(bin_dir / "dhd64.dll"),
            str(runtime_source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _build_mock_openhaptics_sdk(sdk_root: Path, clang_path: str) -> None:
    """Create a minimal SDK root with mock OpenHaptics runtime DLLs."""
    hd_include_dir = sdk_root / "include" / "HD"
    hdu_include_dir = sdk_root / "include" / "HDU"
    lib_dir = sdk_root / "lib"
    bin_dir = sdk_root / "bin"
    hd_include_dir.mkdir(parents=True, exist_ok=True)
    hdu_include_dir.mkdir(parents=True, exist_ok=True)
    lib_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    (hd_include_dir / "hd.h").write_text("// mock OpenHaptics HD header\n", encoding="utf-8")
    (hdu_include_dir / "hduVector.h").write_text("// mock OpenHaptics HDU header\n", encoding="utf-8")
    (lib_dir / "hd.lib").write_text("", encoding="utf-8")
    (lib_dir / "hdu.lib").write_text("", encoding="utf-8")

    hd_runtime_source = sdk_root / "mock_hd_runtime.cpp"
    hd_runtime_source.write_text(
        textwrap.dedent(
            """
            #if defined(_WIN32)
            #define EXPORT __declspec(dllexport)
            #else
            #define EXPORT
            #endif

            extern "C" {
            EXPORT void* hdInitDevice(const char* selector) {
              if (!selector) {
                return nullptr;
              }
              return reinterpret_cast<void*>(0x1);
            }
            EXPORT void hdDisableDevice(void*) {}
            EXPORT const char* hdGetErrorString(int) { return "No error"; }
            EXPORT const char* hdGetString(int) { return "Mock OpenHaptics Touch X"; }
            EXPORT void* hdGetCurrentDevice() { return reinterpret_cast<void*>(0x1); }
            EXPORT void hdGetIntegerv(int, int* value) {
              if (value) {
                *value = 1;
              }
            }
            EXPORT void hdGetDoublev(int, double* value) {
              if (value) {
                *value = 0.5;
              }
            }
            EXPORT void hdEnable(int) {}
            EXPORT void hdSetDoublev(int, const double*) {}
            EXPORT int hdStartScheduler() { return 0; }
            EXPORT int hdStopScheduler() { return 0; }
            EXPORT void* hdScheduleAsynchronous(void*, void*, int) {
              return reinterpret_cast<void*>(0x2);
            }
            EXPORT int hdUnschedule(void*) { return 0; }
            EXPORT int hdCheckCalibration() { return 1; }
            EXPORT int hdUpdateCalibration(int) { return 0; }
            }
            """,
        ).strip(),
        encoding="utf-8",
    )
    subprocess.run(
        [
            clang_path,
            "-shared",
            "-o",
            str(bin_dir / "hd.dll"),
            str(hd_runtime_source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    hdu_runtime_source = sdk_root / "mock_hdu_runtime.cpp"
    hdu_runtime_source.write_text(
        textwrap.dedent(
            """
            #if defined(_WIN32)
            #define EXPORT __declspec(dllexport)
            #else
            #define EXPORT
            #endif

            extern "C" {
            EXPORT int hduMockUtility() { return 1; }
            }
            """,
        ).strip(),
        encoding="utf-8",
    )
    subprocess.run(
        [
            clang_path,
            "-shared",
            "-o",
            str(bin_dir / "hdu.dll"),
            str(hdu_runtime_source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _build_temp_native_root(native_root: Path) -> Path:
    """Create a temporary native bridge source tree for isolated builds."""
    source_root = ROOT / "native"
    (native_root / "src").mkdir(parents=True, exist_ok=True)
    (native_root / "CMakeLists.txt").write_text(
        (source_root / "CMakeLists.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (native_root / "src" / "feelit_bridge_probe.cpp").write_text(
        (source_root / "src" / "feelit_bridge_probe.cpp").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return native_root


def _build_backend_probe(backend_slug: str, sdk_root: Path, native_root: Path) -> Path:
    """Build the native bridge probe for one backend slug."""
    bootstrap_script = ROOT / "scripts" / "Bootstrap_HapticBridge.ps1"
    probe_path = native_root / "build" / backend_slug / "out" / "feelit_bridge_probe.exe"
    environment = os.environ.copy()
    environment["FEELIT_NATIVE_BRIDGE_ROOT"] = str(native_root)
    subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(bootstrap_script),
            "-Backend",
            backend_slug,
            "-SdkRoot",
            str(sdk_root),
            "-Build",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert probe_path.exists()
    return probe_path


def test_forcedimension_vendor_probe_reports_runtime_and_devices(tmp_path, monkeypatch) -> None:
    """The native probe should load a DHD-like runtime and surface real device data."""
    statuses = _require_native_build_support()
    clang_path = statuses["clang++"].detected_path
    assert clang_path

    sdk_root = tmp_path / "mock_forcedimension_sdk"
    native_root = _build_temp_native_root(tmp_path / "native_bridge_root")
    _build_mock_forcedimension_sdk(sdk_root, clang_path)
    probe_path = _build_backend_probe("forcedimension-dhd", sdk_root, native_root)

    probe = probe_native_bridge(
        str(probe_path),
        backend_slug="forcedimension-dhd",
        sdk_root=str(sdk_root),
    )
    assert probe.state == "ready"
    assert probe.detected_device_count == 2
    assert "Mock DHD SDK 3.14.0" == probe.payload["sdk_version"]
    assert probe.payload["runtime_load_state"] == "loaded"
    assert probe.detected_devices == ["Mock SIGMA.7", "Mock OMEGA.7 Left"]

    config_path = tmp_path / "haptic_runtime_config.json"
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))
    manager = HapticRuntimeManager()
    snapshot = manager.update_configuration(
        requested_backend="forcedimension-dhd",
        sdk_roots={"forcedimension": str(sdk_root)},
        bridge_paths={"forcedimension": str(probe_path)},
    )

    forcedimension = next(
        backend for backend in snapshot.backends if backend.slug == "forcedimension-dhd"
    )
    assert forcedimension.bridge_probe_state == "ready"
    assert forcedimension.detected_device_count == 2
    assert forcedimension.detected_devices == ["Mock SIGMA.7", "Mock OMEGA.7 Left"]
    assert forcedimension.availability == "devices-detected"
    assert any("Bridge runtime load state: loaded" in item for item in forcedimension.evidence)
    assert probe_path == native_root / "build" / "forcedimension-dhd" / "out" / "feelit_bridge_probe.exe"
    assert probe_path != ROOT / "native" / "build" / "forcedimension-dhd" / "out" / "feelit_bridge_probe.exe"


def test_openhaptics_vendor_probe_reports_device_ready_capability(tmp_path, monkeypatch) -> None:
    """The native probe should report a safe default-device open path for OpenHaptics."""
    statuses = _require_native_build_support()
    clang_path = statuses["clang++"].detected_path
    assert clang_path

    sdk_root = tmp_path / "mock_openhaptics_sdk"
    native_root = _build_temp_native_root(tmp_path / "openhaptics_native_bridge_root")
    _build_mock_openhaptics_sdk(sdk_root, clang_path)
    probe_path = _build_backend_probe("openhaptics-touch", sdk_root, native_root)

    probe = probe_native_bridge(
        str(probe_path),
        backend_slug="openhaptics-touch",
        sdk_root=str(sdk_root),
    )
    assert probe.state == "ready"
    assert probe.detected_device_count == 1
    assert probe.payload["runtime_load_state"] == "loaded"
    assert probe.payload["runtime_library"].endswith("hd.dll")
    assert probe.payload["enumeration_mode"] == "default-device-open"
    assert probe.payload["capability_scope"] == "runtime-and-default-device-open"
    assert "force-output-path" in probe.payload["reported_capabilities"]
    assert "hdGetString" in probe.payload["resolved_symbols"]
    assert "scheduler-control" in probe.payload["reported_capabilities"]
    assert "calibration-interface" in probe.payload["reported_capabilities"]
    assert "device-characteristics-query" in probe.payload["reported_capabilities"]
    assert probe.detected_devices == ["OpenHaptics default device (DEFAULT)"]

    config_path = tmp_path / "openhaptics_runtime_config.json"
    monkeypatch.setenv("FEELIT_HAPTIC_CONFIG_PATH", str(config_path))
    manager = HapticRuntimeManager()
    snapshot = manager.update_configuration(
        requested_backend="openhaptics-touch",
        sdk_roots={"openhaptics": str(sdk_root)},
        bridge_paths={"openhaptics": str(probe_path)},
    )

    openhaptics = next(
        backend for backend in snapshot.backends if backend.slug == "openhaptics-touch"
    )
    assert openhaptics.bridge_probe_state == "ready"
    assert openhaptics.availability == "devices-detected"
    assert openhaptics.device_detection_state == "devices-detected"
    assert openhaptics.probe_enumeration_mode == "default-device-open"
    assert openhaptics.probe_capability_scope == "runtime-and-default-device-open"
    assert "force-output-path" in openhaptics.reported_capabilities
    assert "scheduler-control" in openhaptics.reported_capabilities
    assert "calibration-interface" in openhaptics.reported_capabilities
    assert openhaptics.detected_devices == ["OpenHaptics default device (DEFAULT)"]
    assert any("Bridge enumeration mode: default-device-open" in item for item in openhaptics.evidence)
    assert any("Bridge runtime load state: loaded" in item for item in openhaptics.evidence)
    assert probe_path == native_root / "build" / "openhaptics-touch" / "out" / "feelit_bridge_probe.exe"
    assert probe_path != ROOT / "native" / "build" / "openhaptics-touch" / "out" / "feelit_bridge_probe.exe"
