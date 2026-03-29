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

This avoids collapsing incompatible workflows into one long page.

### 3D Workspace Rule In FeelIT

The object explorer, Braille reader, and haptic desktop each render an actual 3D world as the main pane:

- the object explorer stages real OBJ meshes inside a bounded scene
- the Braille reader renders the tactile board as raised 3D geometry with scene-native navigation controls
- the desktop mode renders shape-coded tactile objects inside a spatial desktop layout
- the shared pointer emulator behaves as a stylus-like proxy when no hardware device is attached

Auxiliary 2D views are secondary and are only used when they help interpretation or debugging.

### Mode-Specific Frontend Modules

- `app/static/object_explorer.html`
- `app/static/braille_reader.html`
- `app/static/haptic_desktop.html`
- `app/static/js/object_explorer.js`
- `app/static/js/braille_reader.js`
- `app/static/js/haptic_desktop.js`
- `app/static/vendor/three/OBJLoader.js`

## API Layer

The API layer provides the public contract between frontend workspaces and domain services.

Current responsibilities:

- health metadata
- public application metadata
- mode catalog
- material profile catalog
- demo model catalog
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

Current files:

- `app/core/config.py`
- `app/core/version.py`
- `app/core/modes.py`
- `app/core/braille.py`
- `app/core/haptic_materials.py`
- `app/core/demo_assets.py`

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
6. Each workspace instantiates the shared stylus-like pointer proxy and bounded scene runtime.
7. The object explorer stages an OBJ mesh and tactile material context on a visible exploration plinth.
8. The Braille reader calls `/api/braille/preview` and realizes the response as a 3D tactile board with in-scene controls.
9. The desktop mode instantiates a bounded desktop scene from its local interaction model.
10. Runtime and device status are reflected in the current workspace.

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
- page slicing and 3D Braille board rendering
- scene-native previous and next tactile controls
- orientation rail and origin marker inside the reading world
- selected-cell inspection and auxiliary 2D board

Next additions:

- document ingestion service for richer formats
- richer layout constraints tied to device workspace assumptions

### Haptic Desktop

Current baseline:

- 3D desktop object scene
- focus traversal and activation prototype
- shape-coded tactile object families instead of text-heavy world labels
- announcement and inspector metadata outside the scene itself

Next additions:

- content graph or object catalog
- audio label service
- assistive focus and activation rules
- integration with real desktop or curated content sources

## Packaging Architecture

The repository keeps local execution, standalone distribution, and installer generation inside the same project workflow through:

- `Build_PyInstaller.ps1`
- `build.spec`
- `installer/FeelIT_installer.iss`
