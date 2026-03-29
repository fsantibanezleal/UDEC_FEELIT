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

- type or paste text
- choose the number of columns
- generate a Braille preview layout
- inspect the 3D Braille world and the auxiliary board together
- move through the reading surface with the stylus-style pointer proxy
- activate the scene-native previous and next tactile controls
- inspect per-cell metadata by selecting rendered cells

Current keyboard cues:

- `W`, `A`, `S`, `D`: move across the tactile reading plane
- `Q`, `E`: adjust pointer height within the bounded workspace
- `Space` or `Enter`: activate the tactile control or current cell under the pointer
- arrow keys: fallback debug navigation across the generated page

This is the main legacy-aligned operational mode in the current baseline.

### 3. Haptic Desktop

Route:

```text
/haptic-desktop
```

Current use:

- move the stylus-style pointer proxy through a shape-coded desktop world
- let the pointer focus desktop objects by spatial proximity
- activate the focused object
- inspect the current announcement and focus metadata

Current keyboard cues:

- `W`, `A`, `S`, `D`: move across the desktop world
- `Q`, `E`: move vertically
- `Space` or `Enter`: activate the focused desktop object
- arrow keys: fallback debug focus traversal

This workspace currently acts as a focused interaction prototype for future haptic desktop behavior.

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

This validation opens all three routes, captures the 3D canvas in Chromium, and fails if the pages log runtime errors or if the rendered scene looks under-populated.

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

## Current Limitations

- no physical device bridge is connected yet
- 3D object staging is currently client-side and focused on `.obj`
- no document parser beyond direct text input is active yet
- desktop actions are still frontend-level prototypes
- haptic material profiles are plausible approximations, not full physical simulation
