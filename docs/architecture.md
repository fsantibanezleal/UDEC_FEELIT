# FeelIT Architecture

## Purpose

This document defines the current system architecture for the modern FeelIT rebuild.

## Architectural Priorities

- preserve the verified Braille legacy path
- isolate hardware-specific logic behind a haptic backend abstraction
- expose separate user workspaces for different interaction goals
- render the actual spatial workspace for haptic-facing modes
- keep the application usable when no physical haptic device is attached

## High-Level View

![Architecture](svg/architecture.svg)

## Mode Map

![Mode Map](svg/mode_map.svg)

This mode map should always reflect the current shipped route set, current maturity of each route, and the current blind-first interaction contract.

## Braille Runtime Pipeline

![Braille Pipeline](svg/braille_pipeline.svg)

The Braille pipeline diagram should stay aligned with the real reading workflow, including the current scene-native library launcher, segment loading, preview translation, and reading-world controls.

## Frontend Architecture

The frontend follows the workbench pattern used by the stronger reference repositories.

### Shared Shell

All user workspaces share:

- top application header
- persistent mode navigation
- runtime version badge
- help modal pattern
- dark technical visual language
- a real 3D scene as the primary workspace for spatial modes
- module-based frontend bootstrap through the shared shell helper
- visible boot diagnostics when runtime initialization fails
- workspace-driven scene transitions for Haptic Desktop

Current shared files:

- `app/static/css/style.css`
- `app/static/js/app.js`
- `app/static/js/three_scene_common.js`
- `app/static/vendor/three/three.core.js`
- `app/static/vendor/three/three.module.js`
- `app/static/vendor/three/OrbitControls.js`

### Dedicated Mode Routes

The user-facing interface is separated into dedicated routes:

- `/object-explorer`
- `/braille-reader`
- `/haptic-desktop`
- `/haptic-workspace-manager`

This avoids collapsing incompatible workflows into one long page.

### 3D Workspace Rule In FeelIT

The object explorer, Braille reader, and haptic desktop each render an actual 3D world as the main pane:

- the object explorer stages real OBJ meshes inside a bounded scene
- the Braille reader starts from a scene-native tactile library launcher and then renders the tactile board as raised 3D geometry with scene-native navigation controls
- the desktop mode renders a workspace-driven launcher, galleries, a typed file browser, detail plaques, and opened content scenes
- the shared pointer emulator behaves as a stylus-like proxy when no hardware device is attached

Auxiliary 2D views are secondary and are only used when they help interpretation or debugging.

### Mode-Specific Frontend Modules

- `app/static/object_explorer.html`
- `app/static/braille_reader.html`
- `app/static/haptic_desktop.html`
- `app/static/haptic_workspace_manager.html`
- `app/static/js/object_explorer.js`
- `app/static/js/braille_reader.js`
- `app/static/js/haptic_desktop.js`
- `app/static/js/haptic_workspace_manager.js`
- `app/static/vendor/three/OBJLoader.js`

## API Layer

The API layer provides the public contract between frontend workspaces and domain services.

Current responsibilities:

- health metadata
- public application metadata
- mode catalog
- material profile catalog
- demo model catalog
- bundled document library catalog
- bundled document segment loading
- bundled audio library catalog
- haptic workspace catalog, browsing, text loading, raw file serving, and descriptor management
- haptic backend status
- Braille preview translation

Current file:

- `app/api/routes.py`

## Core Domain Layer

The core domain layer contains logic that should remain independent of any frontend layout or hardware vendor.

Current responsibilities:

- application configuration
- canonical version metadata
- mode catalog
- Braille translation
- Braille preview layout
- haptic material profiles
- bundled demo asset catalog
- bundled public-domain document and audio catalogs
- plain-text, HTML, and EPUB extraction for the internal reading library
- haptic workspace descriptor parsing, registry, and filesystem browsing

Current files:

- `app/core/config.py`
- `app/core/version.py`
- `app/core/modes.py`
- `app/core/braille.py`
- `app/core/haptic_materials.py`
- `app/core/demo_assets.py`
- `app/core/library_assets.py`
- `app/core/haptic_workspace.py`

## Haptic Runtime Layer

The haptic runtime layer wraps the active device backend.

Current behavior:

- uses a null backend for visual-only fallback execution
- exposes stable device status metadata
- keeps hardware assumptions out of the API and core domain logic

Current files:

- `app/haptics/base.py`
- `app/haptics/null_backend.py`
- `app/haptics/factory.py`

## Page Delivery

FastAPI serves the mode pages directly:

- root redirects to `/braille-reader`
- each mode route returns a dedicated static HTML document
- all static assets are served under `/static`

Current file:

- `app/main.py`

## Current Runtime Flow

1. `run_app.py` launches Uvicorn.
2. `app.main` creates the FastAPI application and starts the selected haptic backend.
3. The user opens one of the dedicated mode routes.
4. The shared frontend shell requests `/api/health` and `/api/meta`.
5. The object explorer additionally calls `/api/materials` and `/api/demo-models`.
6. The Braille reader additionally calls `/api/library/documents` and `/api/library/audio`.
7. Haptic Desktop calls `/api/haptic-workspaces` and resolves the selected `haptic_workspace`.
8. Each spatial workspace instantiates the shared stylus-like pointer proxy and bounded scene runtime.
9. The object explorer stages an OBJ mesh and tactile material context on a visible exploration plinth.
10. The Braille reader loads the bundled library catalog, opens a document from a scene-native launcher, requests `/api/braille/preview`, and realizes the response as a 3D tactile board with in-scene page, segment, and library-return controls.
11. Haptic Desktop moves between launcher, gallery, file-browser, detail, and opened-content scenes using workspace-driven payloads.
12. File-browser entries use kind-specific tactile forms and dispatch supported files directly into the corresponding runtime scene.
13. Opened desktop scenes expose `Gallery` or `Browser` returns to the exact origin context and `Launcher` for return to the workspace start scene.
14. Runtime and device status are reflected in the current workspace.

## Future Extension Points

### 3D Object Explorer

Current baseline:

- real OBJ loading from local bundled assets
- local OBJ upload and client-side parsing
- bounded 3D scene with stylus-like pointer proxy
- visible exploration plinth and adaptive scene bounds
- tactile material preset selection

Next additions:

- asset import endpoints for `.stl` and `.glb`
- persistent model metadata
- server-side validation and preprocessing
- native contact model once a hardware backend is attached

### Braille Reader

Current baseline:

- Braille translation API
- internal public-domain library with TXT, HTML, and EPUB extraction
- segmented document loading for bounded reading sessions
- scene-native 3D library launcher for blind-first document entry
- page slicing and 3D Braille board rendering
- scene-native previous and next tactile controls
- scene-native previous and next segment controls plus library return
- orientation rail and origin marker inside the reading world
- optional companion audio catalog surfaced beside the reading workflow
- selected-cell inspection and auxiliary 2D board

Next additions:

- richer document compatibility beyond the first supported formats
- richer layout constraints tied to device workspace assumptions

### Haptic Desktop

Current baseline:

- structured `haptic_workspace` descriptor format and bundled demo workspace
- dedicated manager route for creating and registering workspaces rooted in external folders
- launcher scene for curated models, texts, audio, and file browsing
- paginated gallery scenes for curated workspace content
- file-browser scene rooted in the configured workspace path
- detail plaque scene with braille naming before content opening
- opened model, text, and audio scenes with scene-native return controls

Next additions:

- richer workspace authoring tools and validation beyond the first JSON descriptor baseline
- audio naming and cue refinement tied to real user workflows
- assistive focus and activation rules tuned against real haptic-device constraints
- integration with native hardware and richer desktop action execution

## Packaging Architecture

The repository keeps local execution, standalone distribution, and installer generation inside the same project workflow through:

- `Build_PyInstaller.ps1`
- `build.spec`
- `installer/FeelIT_installer.iss`
