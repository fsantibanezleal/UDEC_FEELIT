# FeelIT Haptic Runtime Design

## Purpose

This document defines the current engineering baseline for FeelIT's haptic runtime path: backend selection, dependency detection, contact-model assumptions, and material-response strategy before a physical device bridge is shipped.

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
- configured bridge path
- detected bridge path

That distinction matters because dependency readiness is not the same thing as a functioning physical runtime.

## Configuration Surface

The new `/haptic-configuration` route exists so the hardware path is visible inside the application itself rather than hidden in ad hoc engineering notes.

The route currently exposes:

- requested backend selection
- vendor SDK-root inputs
- vendor bridge-path inputs
- runtime summary cards
- per-backend diagnostics
- proxy-first collision baseline
- material-rendering baseline

## Contact Model Baseline

FeelIT should not treat the visual render mesh as the final haptic collision scene.

### Current Design Rule

Use simplified haptic proxies for the servo loop whenever stability matters.

That means:

- object exploration should favor reduced collision meshes or explicit proxy geometry
- Braille dots, page rails, return buttons, and launcher controls should be explicit primitives
- desktop folders, files, and launcher objects should be deliberate tactile tiles rather than arbitrary scene meshes

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

## Validation Expectations

The runtime path should not be considered shipped until it can prove:

- backend-free startup still works
- SDK readiness is visible and diagnosable
- bridge selection and activation are explicit
- scene-to-backend contact geometry is defined per mode
- material profiles have a documented mapping to force channels
- tests cover the configuration API and route
- diagrams and docs remain aligned with the runtime
