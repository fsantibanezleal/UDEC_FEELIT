# FeelIT

Modern accessibility-centered haptic application for tactile 3D object exploration, Braille reading, and controlled desktop-style interaction.

## Overview

FeelIT is a modernization of an accessibility project originally developed by Felipe Santibanez during his Electronic Engineering studies in Concepcion, Chile. The project focuses on giving people with visual impairment a richer way to access shape, texture, spatial structure, and text through bounded tactile interaction rather than relying only on visual interfaces or audio narration.

The current repository is not a single long web page. It is a multi-workspace application with four dedicated routes:

- `/object-explorer`
- `/braille-reader`
- `/haptic-desktop`
- `/haptic-workspace-manager`

The shipped baseline already provides real 3D workspace rendering across the spatial modes, a null-safe no-device execution path with pointer emulation, scene-native Braille controls, bundled public-domain reading and audio assets, curated 3D demo assets, and a structured `haptic_workspace` system that prepares the Haptic Desktop for larger external libraries.

## Problem Framing

![FeelIT problem framing](docs/svg/problem_framing.svg)

The core problem is not only that some information is visual. It is that many relevant objects, surfaces, and workflows are physically inaccessible, too large, too distant, too fragile, or too dependent on visual metaphors. FeelIT responds by converting those inaccessible domains into bounded tactile interaction worlds that can later be connected to real haptic hardware.

## Motivation

- Many objects worth understanding cannot be directly touched: landmarks, terrain, animals, cultural artifacts, and scaled structures.
- Audio helps, but audio alone does not preserve tactile agency for users who want to read, inspect shape, or navigate structured content through touch.
- Braille reading should remain possible without monopolizing the audio channel.
- Desktop interaction for blind users should not depend only on flat visual UI metaphors or voice prompts when a tactile scene could provide a more structured access path.
- A modern rebuild also needs methodological honesty: the verified legacy baseline was strongest in Braille, while the richer 3D explorer and haptic desktop are deliberate modernization work.

## Process And Interaction Flow

![FeelIT mode map](docs/svg/mode_map.svg)

The mode map shows the four routed workspaces and how each one owns a different part of the accessibility problem: 3D object staging, Braille reading, haptic desktop interaction, and workspace authoring.

![FeelIT Braille pipeline](docs/svg/braille_pipeline.svg)

The Braille pipeline shows a representative runtime path that is already implemented today: a scene-native library launcher selects content, the API clips a bounded segment, the Braille translator generates positioned cells, and the browser realizes them as a tactile 3D reading world with in-scene controls.

## Architecture

![FeelIT architecture](docs/svg/architecture.svg)

FeelIT uses a shared FastAPI backend, a shared Three.js scene runtime, a null-safe haptic abstraction boundary, and route-specific frontend modules. The architecture is intentionally release-governed: diagrams, README content, help text, and methodological history are all expected to move with the real shipped state rather than drifting behind it.

## KPI Targets

- Blind-first operability: major interaction paths should be available from scene-native tactile targets rather than only from surrounding browser controls.
- Tactile reading continuity: document sessions should support bounded reading, page movement, segment movement, and reliable return paths inside the same 3D world.
- No-device viability: the application should remain runnable, inspectable, and testable without a physical haptic device attached.
- Workspace coherence: galleries, file browser scenes, and opened-content scenes should preserve clear return semantics and stable viewpoint behavior.
- Asset accessibility breadth: the bundled demo content should cover multiple object, text, and audio examples without violating repository-size constraints.
- Modernization traceability: the repository should clearly separate verified legacy behavior from new engineering scope, with current docs and SVGs always matching the runtime.

## Current Measured State

| Indicator | Current State |
|---|---|
| Routed workspaces | `4` |
| Spatial routes with a real 3D primary pane | `3` |
| Bundled OBJ demo models | `10` |
| Bundled public-domain documents | `5` |
| Bundled public-domain audio samples | `4` |
| Bundled reading-source formats | `txt`, `html`, `epub` |
| Public port | `8101` |
| Canonical version | `2.06.001` |
| Verified legacy baseline | Braille loading and conversion with optional Falcon-class haptics |
| Current validation surface | `48` automated tests passing plus browser smoke validation across the `4` routed pages |

## Scope And Current Status

### Current Workspaces

- `3D Object Explorer`: stages bundled or local OBJ geometry, applies tactile material presets, and prepares bounded exploration scenes.
- `Braille Reader`: starts from a scene-native 3D library launcher, loads bounded document segments, and renders a tactile Braille world with in-scene navigation controls.
- `Haptic Desktop`: moves between a launcher, paginated galleries, a typed file browser, detail plaques, and opened scenes for models, text, and audio.
- `Haptic Workspace Manager`: creates and registers structured `haptic_workspace` descriptors rooted in external folders, and now surfaces registry diagnostics when registered descriptors are missing or invalid.

### Legacy Boundary

The preserved legacy archive in `legacy/Registro Software` most strongly verifies the Braille reading lineage: text-file loading, character-level Braille conversion, OpenGL-based visualization, and optional Falcon-class haptic interaction. The current object explorer, haptic desktop, and multi-route browser workbench are modernization work, not claims about a fully preserved legacy implementation.

![FeelIT legacy to modern mapping](docs/svg/legacy_to_modern.svg)

### Current Boundaries

- no native physical haptic backend is attached yet
- 3D asset import is still centered on OBJ and local staging
- document compatibility is currently limited to bundled `txt`, `html`, and `epub`
- the workspace manager is still a first structured-descriptor baseline rather than a rich authoring suite
- the desktop flow already opens models, text, and audio, but it is not yet a full desktop automation environment
- the current metrics are mostly engineering and delivery metrics, not yet a formal user-study outcome set

## Technical Quick Start

### 1. Create the environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run FeelIT

```powershell
python run_app.py
```

Open one of the routed workspaces:

- `http://127.0.0.1:8101/object-explorer`
- `http://127.0.0.1:8101/braille-reader`
- `http://127.0.0.1:8101/haptic-desktop`
- `http://127.0.0.1:8101/haptic-workspace-manager`

## Validation

### Automated tests

```powershell
python -m pytest tests -v
```

### Browser smoke validation

```powershell
pip install -e ".[dev]"
python -m playwright install chromium
python scripts\browser_scene_smoke.py
```

To refresh the tracked visual baseline and freeze a release snapshot set:

```powershell
python scripts\browser_scene_smoke.py --archive-version <released-version>
```

## Runtime Surface

### Public metadata and health

- `GET /api/health`
- `GET /api/meta`
- `GET /api/modes`
- `GET /api/device/status`

### Object and material staging

- `GET /api/materials`
- `GET /api/demo-models`

### Braille and library services

- `POST /api/braille/preview`
- `GET /api/library/documents`
- `GET /api/library/documents/{slug}`
- `GET /api/library/audio`

### Haptic workspace services

- `GET /api/haptic-workspaces`
- `GET /api/haptic-workspaces/{slug}`
- `GET /api/haptic-workspaces/{slug}/browse`
- `GET /api/haptic-workspaces/{slug}/text-file`
- `GET /api/haptic-workspaces/{slug}/raw-file`
- `POST /api/haptic-workspaces/create`
- `POST /api/haptic-workspaces/register`

## Bundled Demo Content

### 3D models

FeelIT ships `10` lightweight OBJ demos, including `WaltHead.obj`, `Cerberus.obj`, `tree.obj`, `terrain_peak.obj`, and low-poly book and vase samples. The full catalog and provenance are documented in [Asset Sources](docs/asset_sources.md).

### Reading library

The internal public-domain library ships `5` bundled documents:

- `Alice's Adventures in Wonderland`
- `Pride and Prejudice`
- `Pride and Prejudice (EPUB)`
- `The Raven`
- `Feeding the Mind`

It also ships `4` companion audio samples from public-domain sources. See [Library Catalog](docs/library_catalog.md) and [Asset Sources](docs/asset_sources.md).

### Workspace system

The bundled demo workspace lives at `app/static/assets/workspaces/feelit_demo.haptic_workspace.json` and mirrors the full internal demo catalog so Haptic Desktop galleries do not hide bundled content behind a partial subset.

## Build And Distribution

### PyInstaller executable

```powershell
.\Build_PyInstaller.ps1
```

### Inno Setup installer

After building the executable:

```powershell
.\installer\Build_InnoSetup.ps1
```

## Documentation Index

- [Scope And Motivation](docs/scope_and_motivation.md)
- [Architecture](docs/architecture.md)
- [Implementation Gap Audit](docs/implementation_gap_audit.md)
- [Material Profiles](docs/material_profiles.md)
- [Library Catalog](docs/library_catalog.md)
- [Asset Sources](docs/asset_sources.md)
- [Theory](docs/theory.md)
- [Development History](docs/development_history.md)
- [User Guide](docs/user_guide.md)
- [References](docs/references.md)
- [Legacy Mapping](docs/legacy_mapping.md)
- [Artifacts Archive](artifacts/README.md)

## License

MIT for the modern code in this repository. Legacy materials remain preserved for historical and research context.
