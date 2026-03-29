# FeelIT User Guide

## Running The Application

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_app.py
```

Default entry point:

```text
http://127.0.0.1:8101/braille-reader
```

## Available Workspaces

### 1. 3D Object Explorer

Route:

```text
/object-explorer
```

Current use:

- choose a bundled OBJ model or local OBJ file
- stage the current object in the live 3D workspace
- select a tactile material profile
- adjust bounded workspace scale
- move the stylus-style pointer proxy with keyboard support
- emulate a surface contact on the staged object

Current keyboard cues:

- `W`, `A`, `S`, `D`: move over the workspace plane
- `Q`, `E`: move vertically
- `Space` or `Enter`: emulate contact near the current object surface

This workspace currently focuses on visual staging and tactile context preparation ahead of native haptic contact rendering.

### 2. Braille Reader

Route:

```text
/braille-reader
```

Current use:

- load a bundled public-domain document segment or type your own text
- adjust the current document segment length for bounded reading sessions
- choose the number of columns
- generate a Braille preview layout
- inspect the 3D Braille world and the auxiliary board together
- move through the reading surface with the stylus-style pointer proxy
- activate the scene-native previous and next tactile controls
- optionally select companion audio without replacing the tactile-first workflow
- inspect per-cell metadata by selecting rendered cells

Current keyboard cues:

- `W`, `A`, `S`, `D`: move across the tactile reading plane
- `Q`, `E`: adjust pointer height within the bounded workspace
- `Space` or `Enter`: activate the tactile control or current cell under the pointer
- arrow keys: fallback debug navigation across the generated page

This is the main legacy-aligned operational mode in the current baseline.

Internal library endpoints used by this mode:

- `GET /api/library/documents`
- `GET /api/library/documents/{slug}`
- `GET /api/library/audio`

### 3. Haptic Desktop

Route:

```text
/haptic-desktop
```

Current use:

- select the active structured workspace from the left panel
- load the bundled demo workspace or a registered external workspace
- start in a tactile launcher with entry objects for models, texts, audio, and the workspace file browser
- move through paginated gallery scenes and a workspace-root file browser
- open a detail plaque that exposes the content name before opening the real scene
- open 3D model scenes, Braille reading scenes, and audio transport scenes with scene-native return controls

Current keyboard cues:

- `W`, `A`, `S`, `D`: move across the current tactile scene
- `Q`, `E`: move vertically inside the bounded workspace
- `Space`: activate the tactile control or item under the pointer
- arrow keys: fallback debug focus traversal
- `Enter`: fallback activation of the current focused control

The blind-first contract in this mode is that the primary controls live inside the 3D world itself. The surrounding web controls remain a debug and setup layer.

### 4. Haptic Workspace Manager

Route:

```text
/haptic-workspace-manager
```

Current use:

- create a new `haptic_workspace` rooted in an external folder on the local machine
- auto-populate model, text, and audio libraries from supported files already present in that root
- register an existing `.haptic_workspace.json` descriptor file
- review the current workspace catalog before opening a workspace inside Haptic Desktop

## Runtime Information

All pages expose:

- API status
- application version
- public port
- haptic backend mode

If no physical haptic device is configured, the application remains usable in visual fallback mode.

If a workspace cannot initialize correctly, the stage should now expose a visible startup error instead of remaining silently stuck in placeholder states such as `v--`, `Loading`, or `Waiting`.

## Browser Smoke Validation

For scene-regression checks beyond API tests:

```powershell
pip install -e ".[dev]"
python -m playwright install chromium
python scripts\browser_scene_smoke.py
```

This validation opens the three 3D routes, captures the scene canvas in Chromium, and fails if the pages log runtime errors, miss workspace bootstrap data, or if the rendered scene looks under-populated.

## API Endpoints

### Health

```text
GET /api/health
```

### Public Metadata

```text
GET /api/meta
```

### Mode Catalog

```text
GET /api/modes
```

### Material Profiles

```text
GET /api/materials
```

### Demo OBJ Models

```text
GET /api/demo-models
```

### Haptic Backend Status

```text
GET /api/device/status
```

### Braille Preview

```text
POST /api/braille/preview
```

Example payload:

```json
{
  "text": "FeelIT creates tactile access.",
  "columns": 10
}
```

### Document Library Catalog

```text
GET /api/library/documents
```

### Document Segment Loader

```text
GET /api/library/documents/{slug}?offset=0&max_chars=1200
```

### Audio Library Catalog

```text
GET /api/library/audio
```

### Haptic Workspace Catalog

```text
GET /api/haptic-workspaces
```

### Haptic Workspace Detail

```text
GET /api/haptic-workspaces/{slug}
```

### Haptic Workspace Browser

```text
GET /api/haptic-workspaces/{slug}/browse?path=
```

### Haptic Workspace Text Payload

```text
GET /api/haptic-workspaces/{slug}/text-file?path=...&offset=0&max_chars=1200
```

### Haptic Workspace Raw File

```text
GET /api/haptic-workspaces/{slug}/raw-file?path=...
```

### Haptic Workspace Create

```text
POST /api/haptic-workspaces/create
```

### Haptic Workspace Register

```text
POST /api/haptic-workspaces/register
```

## Current Limitations

- no physical device bridge is connected yet
- 3D object staging is currently client-side and focused on `.obj`
- document compatibility is currently limited to bundled `txt`, `html`, and `epub` assets
- bundled Braille library selection still begins from surrounding web controls rather than a scene-native library launcher
- workspace authoring is currently JSON-descriptor based and still needs richer validation and editing affordances
- desktop actions are limited to models, text, audio, and file browsing rather than full desktop automation
- haptic material profiles are plausible approximations, not full physical simulation
