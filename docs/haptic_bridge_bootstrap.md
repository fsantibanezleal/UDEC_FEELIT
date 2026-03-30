# FeelIT Haptic Bridge Bootstrap

## Purpose

This document defines the reproducible local workflow used to bootstrap the native FeelIT haptic bridge before the full vendor-specific device loop is live.

![Haptic Bridge Bootstrap](svg/haptic_bridge_bootstrap.svg)

## Why This Matters

The haptic path cannot stay at the level of a browser fallback plus a text field for `sdk_root`. A serious bridge path needs:

- explicit toolchain diagnostics
- an executable bridge-probe contract
- a build script that developers can rerun locally
- an honest distinction between scaffold readiness and real device readiness

## Current Deliverables

FeelIT now ships:

- `scripts/Bootstrap_HapticBridge.ps1`
- `scripts/haptic_bridge_diagnostics.py`
- `native/CMakeLists.txt`
- `native/src/feelit_bridge_probe.cpp`

Together, these provide a first native bridge scaffold that can be configured and built on Windows without already linking against vendor SDKs. The probe now also contains a first vendor-aware Force Dimension path that dynamically loads the DHD runtime, reports the SDK version, and enumerates devices when the runtime is available.

## Bootstrap Workflow

### 1. Diagnose the current stack

```powershell
python scripts\haptic_bridge_diagnostics.py
```

This command dumps the same runtime and bootstrap state that the `/haptic-configuration` route exposes through the API:

- backend candidates
- SDK-root evidence
- bridge-path evidence
- toolchain readiness
- bridge workspace commands
- contact and material-design baseline

### 2. Configure the bridge scaffold

```powershell
.\scripts\Bootstrap_HapticBridge.ps1 -Backend openhaptics-touch -SdkRoot C:\Path\To\VendorSDK
```

### 3. Configure and build

```powershell
.\scripts\Bootstrap_HapticBridge.ps1 -Backend openhaptics-touch -SdkRoot C:\Path\To\VendorSDK -Build
```

The script currently supports the FeelIT backend slugs tracked by the runtime manager:

- `openhaptics-touch`
- `forcedimension-dhd`
- `chai3d-bridge`

## Toolchain Expectations

The current scaffold expects a Windows-native build surface with:

- `CMake`
- a Windows resource compiler
- either `Ninja` plus `clang++` or `MSBuild`

FeelIT now detects and reports these tools independently because a missing resource compiler can still break the build even when `cmake` and `clang++` exist.

## Probe Contract

The bridge scaffold is intentionally narrow and explicit. The executable is expected to answer:

```text
feelit_bridge_probe.exe --backend <backend-slug> --sdk-root <sdk-root> --emit-json
```

The current probe returns a JSON payload with:

- backend slug
- status
- summary
- SDK-root presence
- marker hits
- runtime-marker hits
- runtime-library path
- runtime-load state
- SDK version string when the vendor runtime exposes one
- device count
- device list

Depending on the backend and installed runtime, that response may remain `scaffold-only` or may advance to vendor-aware runtime states such as `runtime-loaded-no-devices` or `ready`. The purpose is to prove that FeelIT can:

- find a bridge executable
- invoke it safely
- parse probe JSON
- present the result in the configuration UI and API

## What The Bridge Still Does Not Claim

The bridge system does **not** yet claim:

- force output
- button input
- workspace calibration
- homing
- servo-loop execution
- real collision or material rendering

The Force Dimension path can now load and enumerate, but those richer runtime capabilities still belong to the next backend stage tracked in the native haptic issues.

## Vendor Paths

### OpenHaptics Touch Stack

Current bootstrap scope:

- detect likely SDK markers such as `HD/hd.h` and `HDU/hduVector.h`
- build and run the FeelIT bridge scaffold for the `openhaptics-touch` target
- preserve the path for future Touch-family device enumeration through a real native backend

### Force Dimension DHD Stack

Current bootstrap scope:

- detect DHD headers such as `dhdc.h` and `drdc.h`
- dynamically load the DHD runtime library from the configured SDK root when it is present
- report SDK version, device count, and device identity through the bridge JSON contract
- preserve the path for future force, calibration, and scene-coupled backend behavior after enumeration succeeds

### CHAI3D Bridge Stack

Current bootstrap scope:

- detect the CHAI3D source root and key headers
- keep a compatibility-oriented path for future multi-device abstraction
- validate that FeelIT can point to a bridge executable even before that bridge exposes live device data

## Next Technical Step

The next bridge milestone is to extend vendor-aware probing beyond the first Force Dimension path and move from enumeration into controlled backend activation. In practice that means:

- OpenHaptics and CHAI3D need the same kind of runtime-load and device-ready probe states
- the probe contract should carry richer capability data once those stacks are live
- the backend still needs calibration, homing, button-state, and force-output stages after enumeration
