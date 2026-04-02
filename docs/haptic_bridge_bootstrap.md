# FeelIT Haptic Bridge Bootstrap

## Purpose

This document defines the reproducible local workflow used to bootstrap the native FeelIT haptic bridge before the full vendor-specific device loop is live.

![Haptic Bridge Bootstrap](svg/haptic_bridge_bootstrap.svg)

## Why This Matters

The haptic path cannot stay at the level of a browser fallback plus a text field for `sdk_root`. A serious bridge path needs:

- explicit toolchain diagnostics
- an executable bridge-probe contract
- a bounded dry-run command acknowledgement path
- a first bounded no-force execution step for the OpenHaptics button-actuation pilot
- a build script that developers can rerun locally
- an honest distinction between scaffold readiness and real device readiness

## Current Deliverables

FeelIT now ships:

- `scripts/Bootstrap_HapticBridge.ps1`
- `scripts/haptic_bridge_diagnostics.py`
- `native/CMakeLists.txt`
- `native/src/feelit_bridge_probe.cpp`

Together, these provide a first native bridge scaffold that can be configured and built on Windows without already linking against vendor SDKs. The executable now covers three bounded bridge responsibilities: a probe path, a dry-run pilot-command acknowledgement path, and one first bounded no-force execution path for the OpenHaptics button-actuation pilot. The probe already contains two vendor-aware paths: an OpenHaptics path that dynamically loads the HD runtime library set, attempts a conservative default-device open, and reports capability channels inferred from exported HDAPI surfaces, and a Force Dimension path that dynamically loads the DHD runtime, reports the SDK version, and enumerates devices when the runtime is available.

The probe payload now also has room for a normalized feature schema. That stable layer is what the Python runtime should eventually rely on for rollout alignment and pilot execution gating, while the raw vendor capability labels remain supporting evidence.

The probe payload now also has room for a normalized feature schema. That stable layer is what the Python runtime should eventually rely on for rollout alignment and pilot execution gating, while the raw vendor capability labels remain supporting evidence.

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

## Dry-Run Pilot Command Acknowledgement

The same executable can now also validate one bounded pilot command contract:

```text
feelit_bridge_probe.exe --backend <backend-slug> --consume-pilot-command-file <command.json> --emit-json
```

This path currently proves only that the bridge boundary can:

- receive a bounded pilot payload
- validate the declared contract shape
- reject backend mismatches or missing required fields
- return a dry-run acknowledgement without claiming scene-wide execution

That is still intentionally smaller than real control. It exists so the first bridge-side milestone after probe coverage is measurable and testable.

## First Bounded Native Execution Slice

The same executable now also supports one bounded native execution step for the OpenHaptics button-actuation pilot:

- receive the same pilot command contract after acknowledgement
- validate that the payload really targets the OpenHaptics button-actuation path
- require a conservative OpenHaptics runtime-ready state first
- execute one bounded bridge-side step in a clamped no-force mode
- return structured execution status and telemetry fields without claiming servo ownership

## What The Bridge Still Does Not Claim

The bridge system does **not** yet claim:

- force output
- button input
- workspace calibration
- homing
- servo-loop execution
- real collision or material rendering
- additional bridge-side execution coverage beyond the first OpenHaptics no-force pilot

The OpenHaptics path can now load the runtime library set, attempt a conservative default-device open, and report stack-level capability channels, and the Force Dimension path can now load and enumerate, but force output, calibration, homing, and live scene-coupled control still belong to the next backend stage tracked in the native haptic issues.

## Vendor Paths

### OpenHaptics Touch Stack

Current bootstrap scope:

- detect likely SDK markers such as `HD/hd.h` and `HDU/hduVector.h`
- build and run the FeelIT bridge scaffold for the `openhaptics-touch` target
- dynamically load `hd.dll` plus optional utility runtime libraries when they are present
- validate minimal HDAPI entry points, attempt a conservative default-device open, and report a vendor-aware capability state
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

The next bridge milestone is to move from the current vendor-aware probe coverage into controlled backend activation. In practice that means:

- OpenHaptics still needs deeper device characterization, calibration-state reporting, and live control beyond the current conservative default-device probe and stack-level capability reporting
- CHAI3D still needs the same kind of runtime-load and device-ready probe states
- the probe contract should carry richer capability data once those stacks are live
- the backend still needs calibration, homing, button-state, and force-output stages after enumeration
