# FeelIT Implementation Gap Audit

## Purpose

This document separates what the current FeelIT baseline demonstrably implements today from what remains partial, planned, or hardware-dependent.

It is intentionally conservative. If a behavior is not visible in the runtime, testable through the current repo, or clearly encoded in the shipped code path, it is not treated here as delivered.

## Verification Basis

This audit is based on:

- repository source inspection
- API and unit tests from `tests/`
- local browser smoke validation through `scripts/browser_scene_smoke.py`
- visible runtime behavior in the three shipped 3D workspaces plus the workspace manager and haptic-configuration routes
- preserved legacy evidence in `legacy/Registro Software`

## Delivered And Verifiable

### Shared Runtime

Implemented:

- FastAPI backend with public metadata, health, mode catalog, material catalog, demo-model catalog, and Braille preview endpoints
- internal-library document and audio catalog endpoints for bundled public-domain assets
- canonical padded version source with synchronized README and Windows packaging metadata
- five-route frontend shell served from the backend on port `8101`
- shared Three.js scene runtime with bounded workspace, orbit camera, and stylus-style pointer emulator
- visual fallback execution when no haptic hardware is attached
- browser smoke validation for the three primary 3D scenes with launcher or scene-transition checks plus workspace-manager and haptic-configuration bootstrap checks
- dedicated runtime-manager layer that persists requested-backend intent and tracks vendor dependency readiness without pretending that a physical backend already exists

Notable evidence:

- `app/main.py`
- `app/api/routes.py`
- `app/static/js/app.js`
- `app/static/js/three_scene_common.js`
- `scripts/browser_scene_smoke.py`

### 3D Object Explorer

Implemented:

- bundled multi-format demo catalog exposed through the API
- scene-native paged launcher for curated demo-model sessions
- local `OBJ`, `STL`, self-contained `glTF`, and `GLB` upload and in-browser parsing
- local `glTF` bundle staging when the main model and required sidecar resources are selected together
- server-side validation and staging-profile analysis for local browser-staged uploads before scene parsing
- early blocking for oversized local uploads and incomplete external-resource `glTF` or `GLB` packages
- backend-derived bounds and workspace-scale recommendations when enough geometry metadata is available
- haptic material profile selection grounded in plausible current-device approximations
- visible exploration plinth and adaptive scene bounds
- in-scene Launcher plus material-cycling controls inside the exploration world
- pointer hover and activation feedback in the rendered scene

Still limited:

- no preprocessing pipeline yet for heavy staged assets after validation and staging analysis
- external-resource packages can be resolved only when the required sidecars are selected together locally; there is still no repackaging or repair pipeline
- no native force model tied to real haptic hardware
- no persistent model metadata or saved exploration sessions
- local upload still enters through the surrounding web controls rather than a scene-native intake path

### Braille Reader

Implemented:

- bundled public-domain document library with TXT, HTML, and EPUB extraction
- segmented library loading for bounded Braille sessions
- scene-native tactile library launcher with paged document targets
- text-to-Braille conversion and positioned cell layout
- bounded 3D reading surface with raised dots
- scene-native previous and next tactile controls
- scene-native previous and next document-segment controls plus return to the library launcher
- orientation cues inside the reading world
- optional companion-audio catalog surfaced alongside the reading workflow
- auxiliary 2D board for debugging and teaching

Still limited:

- no compatibility yet for PDF, DOCX, Markdown, or OCR-derived document sources
- no hardware-calibrated workspace adaptation for a specific haptic device
- no formal tactile reading performance validation yet

### Haptic Desktop

Implemented:

- structured `haptic_workspace` descriptor format with bundled demo workspace
- dedicated workspace-manager route for creating and registering workspaces rooted in external folders
- explicit registry diagnostics for missing or invalid registered workspace descriptors
- launcher scene with a neutral launcher hub plus curated entry points for models, texts, audio, and workspace file browsing
- paginated gallery scenes backed by workspace payloads
- bundled demo-workspace galleries synchronized against the full internal model, text, and audio catalogs
- typed file-browser entries with distinct tactile forms for folders, models, text files, audio files, and unsupported files
- server-side file-browser pagination for larger workspace roots
- explicit in-scene Launcher, Gallery or Browser, and Start or Root return controls across gallery, browser, detail, and opened-content scenes
- file-browser scene rooted in the configured workspace path
- direct mode dispatch from the file browser for supported models, text files, and audio files
- detail plaque scene that exposes the content name before opening it
- opened scenes for 3D models, Braille reading, and audio transport
- pointer-driven focus and activation across the current scene's tactile controls
- sanitized workspace-manager payloads and descriptor-label views that avoid exposing absolute local paths by default

Still limited:

- no native hardware-backed haptic actuation yet
- no richer workspace editor beyond the first descriptor-based manager route
- no desktop-wide automation beyond curated content opening and file browsing
- no support yet for unsupported file types beyond explicit placeholders
- no real blind-user validation round on the new desktop scene flow
- no unregister, rescan, or descriptor-repair lifecycle actions yet in the workspace manager

## Partial Or Prototype-Only Areas

### Haptic Materials

Status:

- delivered as structured profiles and visual approximations
- not yet delivered as hardware-executed force behavior

Interpretation:

The material catalog is real as an API and UI capability, but it remains a preparation layer until a native device backend exists.

### Haptic Runtime Configuration

Status:

- delivered as a configuration and diagnostics surface
- not yet delivered as a live physical-device runtime

Interpretation:

FeelIT now exposes requested backend, active fallback backend, SDK-root intent, bridge-path intent, build-tool readiness, a compiled bridge-probe contract, and a formal contact-model baseline. It also now has a vendor-aware Force Dimension runtime path that can load the DHD runtime and enumerate devices through the probe contract, plus a vendor-aware OpenHaptics path that can load the HD runtime library set, attempt a conservative default-device open, and report stack-level capability channels. This is a real architectural and product step, but it still stops before force rendering or live scene-coupled control.

The runtime now also carries an explicit scene-to-backend contract baseline. That means the repo can already name which tactile primitives and event transitions a future backend must consume for Object Explorer, Braille Reader, and Haptic Desktop, even though the native loop itself is still pending. That contract is no longer just a flat list; it now includes reusable primitive families and a backend-readiness matrix, which makes the remaining gap to scene-coupled force work more auditable.

On top of that, the runtime now computes a first backend-aware contact rollout plan. This is still not live force output, but it materially improves engineering clarity because each stack now names one bounded pilot primitive, one bridge-facing pilot profile, one required runtime-feature set, and one next step instead of stopping at a generic "future work" label.

The current `develop` state now also emits a dry-run pilot command contract for each of those bounded primitives. The runtime can therefore already produce:

- a stable command slug
- transport assumptions
- force-model and safety-envelope summaries
- telemetry expectations
- the missing runtime features that still block real execution

This still stops before bridge acknowledgement, real servo-loop ownership, or force output, but it reduces ambiguity at the next native-integration boundary.

The current bridge path is meaningful because it proves four things end to end:

- FeelIT can discover or configure a bridge executable
- FeelIT can compile that executable locally through a documented bootstrap script
- FeelIT can invoke the bridge and parse JSON results back into the API and frontend
- FeelIT can distinguish scaffold-only bridge readiness from runtime-loaded capability and device-backed capability

The remaining gap is therefore narrower and more concrete: deepen OpenHaptics from conservative default-device probing into richer device characterization and activation, move CHAI3D beyond scaffold-level readiness, then advance from probe states into the actual haptic-control loop.

### Pointer Emulation

Status:

- delivered as a visual and keyboard-driven stylus proxy
- useful for design, inspection, and no-device demonstrations

Interpretation:

This is a valid operational fallback, not a replacement for real haptic execution.

## Not Yet Delivered

The repository does not yet deliver:

- a native haptic backend beside the null backend
- broad runtime device capability detection and activation beyond the current OpenHaptics conservative default-device probe and Force Dimension enumeration baseline
- a native bridge consumer that acknowledges or executes the new dry-run pilot command payloads
- full document-format compatibility beyond the current TXT, HTML, and EPUB baseline
- server-side preprocessing and import pipeline for 3D assets beyond the current validation gate
- real desktop action execution semantics beyond content launching and playback control
- hardware-backed tactile realization of the material profiles
- validated physical collision, force, and material rendering against a real haptic device

## Current Haptic Backend Boundary

The repository now distinguishes three levels of truth:

1. visual fallback execution that is genuinely implemented and testable today
2. vendor-stack dependency readiness that can now be configured and inspected
3. true native hardware actuation that is still pending

That separation is important because it prevents the project from overclaiming hardware readiness while still forcing the backend problem into the visible product and documentation surface.

## Legacy Alignment

Preserved legacy evidence still most strongly supports:

- text-file loading
- Braille conversion
- optional haptic interaction in the Braille reading context

The current repo should not claim that the preserved legacy already delivered:

- the present multi-mode object explorer
- the present haptic desktop concept
- the current browser-based 3D workbench structure

Those belong to the modernization path, not to the verified archived implementation.

## Recommended Near-Term Priorities

1. Build a first native backend activation boundary on top of the current vendor-aware probe coverage so the material and workspace models can move beyond visual approximation.
2. Extend the Braille library with richer compatibility beyond the current TXT, HTML, and EPUB support.
3. Extend the 3D asset pipeline from the current validation gate into preprocessing, repackaging, and safer handling for heavy or external-resource packages.
4. Expand the workspace manager into a richer editor with descriptor validation, asset previews, and safer authoring affordances.
