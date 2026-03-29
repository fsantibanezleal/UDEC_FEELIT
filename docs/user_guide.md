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
- move the proxy pointer with keyboard support

Current keyboard cues:

- `W`, `A`, `S`, `D`: move over the workspace plane
- `Q`, `E`: move vertically

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
- inspect per-cell metadata by selecting rendered cells

Current keyboard cues:

- arrow keys move the current cell focus across the tactile board

This is the main legacy-aligned operational mode in the current baseline.

### 3. Haptic Desktop

Route:

```text
/haptic-desktop
```

Current use:

- move focus between desktop objects inside the 3D desktop scene
- activate the focused object
- inspect the current announcement and focus metadata

Current keyboard cues:

- arrow keys move focus between tactile desktop objects
- `Enter` activates the focused object

This workspace currently acts as a focused interaction prototype for future haptic desktop behavior.

## Runtime Information

All pages expose:

- API status
- application version
- public port
- haptic backend mode

If no physical haptic device is configured, the application remains usable in visual fallback mode.

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
