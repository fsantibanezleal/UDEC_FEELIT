# FeelIT Haptic Runtime Design

## Purpose

This document defines the current engineering baseline for FeelIT's haptic runtime path: backend selection, dependency detection, toolchain readiness, bridge probing, contact-model assumptions, and material-response strategy before a physical device bridge is shipped.

![Haptic Runtime Pipeline](svg/haptic_runtime_pipeline.svg)

![Haptic Contact Pipeline](svg/haptic_contact_pipeline.svg)

## Runtime Layers

FeelIT now separates the haptic runtime into three explicit layers:

1. active runtime backend
2. vendor-stack readiness
3. contact and material rendering design

### Active Runtime Backend

Today the active runtime backend is still the visual pointer emulator. It is not a placeholder in the weak sense; it is the stable no-device path used to keep the 3D worlds inspectable, testable, and demoable.

### Vendor-Stack Readiness

The runtime manager now tracks the first three serious physical-stack candidates:

- OpenHaptics Touch-family path
- Force Dimension DHD SDK path
- CHAI3D-oriented bridge path

The current implementation distinguishes:

- requested backend
- active backend
- configured SDK root
- detected SDK root
- detected driver root
- configured bridge path
- detected bridge path
- bridge-probe state
- toolchain readiness

That distinction matters because dependency readiness is not the same thing as a functioning physical runtime.

## Configuration Surface

The new `/haptic-configuration` route exists so the hardware path is visible inside the application itself rather than hidden in ad hoc engineering notes.

The route currently exposes:

- requested backend selection
- vendor SDK-root inputs
- vendor bridge-path inputs
- preferred device-selector inputs
- build-tool diagnostics
- bridge workspace commands
- bridge-probe state per backend
- runtime summary cards
- per-backend diagnostics
- proxy-first collision baseline
- material-rendering baseline
- scene-to-backend contract baseline for the routed haptic worlds

## Native Bridge Bootstrap

FeelIT now includes a first reproducible local bridge-bootstrap path:

- `scripts/Bootstrap_HapticBridge.ps1`
- `scripts/haptic_bridge_diagnostics.py`
- `native/CMakeLists.txt`
- `native/src/feelit_bridge_probe.cpp`

The bootstrap layer is deliberately honest. It proves that the bridge executable can be configured, compiled, discovered, and probed from the FeelIT runtime. It now includes a vendor-aware OpenHaptics path that can dynamically load the HD runtime library set, attempt a conservative default-device open, and report capability channels inferred from exported HDAPI surfaces, plus a vendor-aware Force Dimension path that can dynamically load the DHD runtime library, report the SDK version, and enumerate device identities when that runtime is present.

## Contact Model Baseline

FeelIT should not treat the visual render mesh as the final haptic collision scene.

### Current Design Rule

Use simplified haptic proxies for the servo loop whenever stability matters.

That means:

- object exploration should favor reduced collision meshes or explicit proxy geometry
- Braille dots, page rails, return buttons, and launcher controls should be explicit primitives
- desktop folders, files, and launcher objects should be deliberate tactile tiles rather than arbitrary scene meshes

## Scene-To-Backend Contract

FeelIT now also defines a first scene-to-backend contract layer. This is still not live force output, but it narrows the architectural gap by making each mode declare:

- which tactile primitives exist in the 3D world
- which event transitions a backend should see
- which telemetry fields the runtime should preserve
- which material or constraint channels those primitives should map into

The current contract models Object Explorer, Braille Reader, and Haptic Desktop as different compositions of the same primitive families rather than as unrelated pages with unrelated physics. It now also exposes:

- a reusable primitive-family catalog
- per-mode return-flow expectations
- a backend-readiness matrix that explains which stacks are still diagnostic and which are closer to scene-coupled work

## Loop Assumptions

Current design targets:

- haptic servo loop: about `1000 Hz`
- visual loop: about `60 Hz`

The exact runtime will depend on the vendor SDK and hardware, but FeelIT already uses these targets to structure how collisions and material cues should be reasoned about.

## Material Rendering Strategy

The current material catalog is not only visual metadata. It now also maps to intended haptic rendering channels:

- stiffness
- damping
- friction
- texture waveform
- vibration
- viscosity-like drag

### Practical Interpretation

- rigid smooth materials such as polished metal or ceramic mainly depend on stiffness, low drag, and limited microtexture
- rigid textured materials such as stone or textured polymer depend on stiffness, friction contrast, and periodic texture modulation
- soft materials such as foam or rubber remain partial approximations that rely on lower stiffness and stronger damping, not full deformation simulation
- paper-like interaction is best treated as a thin constrained surface with shallow grain and light drag

## Native Bridge Direction

The current architecture assumes that vendor SDK integration should live behind a native Windows bridge or sidecar process rather than inside the browser.

Reasons:

- vendor SDKs are native, not browser-native
- haptic loops have tighter timing requirements than the visual route
- device telemetry and diagnostics need stronger control over lifecycle and failure handling
- the browser should remain a scene mirror and orchestration surface, not the physical-device driver

### Current Bridge Contract

The bridge executable is now expected to answer a small JSON probe contract before it is allowed to claim anything stronger:

- which backend target it was built for
- whether the SDK root exists
- which expected markers are present
- whether the bridge is scaffold-only, runtime-loaded-without-devices, probe-failed, or device-ready
- how many devices were enumerated
- which device labels were reported
- which probe mode and capability scope were used
- which haptic-capability channels the bridge reports at the current maturity level

That contract is intentionally smaller than the future runtime loop. The goal is to make bridge readiness measurable early. At the moment, Force Dimension can reach device-ready enumeration through the DHD runtime, while OpenHaptics can now move beyond symbol-only validation into a conservative default-device open path with explicit capability reporting.

## Validation Expectations

The runtime path should not be considered shipped until it can prove:

- backend-free startup still works
- SDK readiness is visible and diagnosable
- bridge selection and activation are explicit
- scene-to-backend contact geometry is defined per mode
- material profiles have a documented mapping to force channels
- tests cover the configuration API and route
- diagrams and docs remain aligned with the runtime
