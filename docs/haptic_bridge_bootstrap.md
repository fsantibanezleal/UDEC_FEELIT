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

Together, these provide a first native bridge scaffold that can be configured and built on Windows without already linking against vendor SDKs.

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

The current scaffold returns a JSON payload with:

- backend slug
- status
- summary
- SDK-root presence
- marker hits
- runtime-marker hits
- device count
- device list

Today, that response is allowed to remain `scaffold-only`. The purpose is to prove that FeelIT can:

- find a bridge executable
- invoke it safely
- parse probe JSON
- present the result in the configuration UI and API

## What The Scaffold Does Not Claim

The bridge scaffold does **not** yet claim:

- live device enumeration
- force output
- button input
- workspace calibration
- homing
- servo-loop execution
- real collision or material rendering

Those capabilities still belong to the next backend stage tracked in the native haptic issues.

## Vendor Paths

### OpenHaptics Touch Stack

Current bootstrap scope:

- detect likely SDK markers such as `HD/hd.h` and `HDU/hduVector.h`
- build and run the FeelIT bridge scaffold for the `openhaptics-touch` target
- preserve the path for future Touch-family device enumeration through a real native backend

### Force Dimension DHD Stack

Current bootstrap scope:

- detect DHD headers such as `dhdc.h` and `drdc.h`
- preserve the bridge path and readiness surface for a future device-aware implementation
- align the future bridge contract with the DHD device-count and open-device flow documented by the vendor SDK

### CHAI3D Bridge Stack

Current bootstrap scope:

- detect the CHAI3D source root and key headers
- keep a compatibility-oriented path for future multi-device abstraction
- validate that FeelIT can point to a bridge executable even before that bridge exposes live device data

## Next Technical Step

The next bridge milestone is not "more scaffolding." It is a vendor-aware probe that can report:

- SDK loaded or failed
- runtime library loaded or failed
- device count
- device identity or capability summary
- failure reasons that remain visible in the FeelIT UI and API
