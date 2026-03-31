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

- start from a scene-native 3D launcher with paged demo-model session targets
- open a bundled demo object directly from the 3D world or stage a local `OBJ`, `STL`, `glTF`, or `GLB` file from the outer controls
- if multiple supported local model files are selected together, choose which one is the main model before loading the bundle
- select a local `glTF` main file together with its sidecar buffers or textures when the asset is not self-contained
- select a tactile material profile or cycle materials from the in-scene controls once a session is open
- adjust bounded workspace scale
- move the stylus-style pointer proxy with keyboard support
- use the in-scene `Launcher` control to return to the object-session launcher on the current page
- emulate a surface contact on the staged object

Current keyboard cues:

- `W`, `A`, `S`, `D`: move over the workspace plane
- `Q`, `E`: move vertically
- `Space` or `Enter`: emulate contact near the current object surface

This workspace now has a blind-first entry path for curated demo models, while local uploads support `OBJ`, `STL`, `GLB`, self-contained `glTF`, and multi-file local `glTF` bundles as a secondary outer-panel intake path.

### 2. Braille Reader

Route:

```text
/braille-reader
```

Current use:

- start from a scene-native 3D library launcher with paged tactile document targets
- open a bundled public-domain document segment directly from the tactile scene or type your own text
- adjust the current document segment length for bounded reading sessions
- choose the number of columns
- generate a Braille preview layout
- inspect the 3D Braille world and the auxiliary board together
- move through the reading surface with the stylus-style pointer proxy
- activate the scene-native previous and next tactile controls
- activate scene-native previous and next document-segment controls
- return from the reading scene to the tactile library launcher without depending on the browser panel
- optionally select companion audio without replacing the tactile-first workflow
- inspect per-cell metadata by selecting rendered cells

Current keyboard cues:

- `W`, `A`, `S`, `D`: move across the tactile reading plane
- `Q`, `E`: adjust pointer height within the bounded workspace
- `Space` or `Enter`: activate the tactile control or current cell under the pointer
- arrow keys: fallback debug navigation across the generated page

This remains the main legacy-aligned operational mode, but it now has a blind-first scene-native entry path instead of relying exclusively on the surrounding web controls.

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
- use the bundled demo workspace as a full internal-library baseline covering every bundled model, document, and audio sample
- expect the bundled demo file browser to start at the bundled assets root, exposing `library`, `models`, and `workspaces` branches for controlled exploration
- start in a tactile launcher with a neutral launcher hub plus entry objects for models, texts, audio, and the workspace file browser
- enter gallery and file-browser scenes through a neutral `Gallery` or `Browser` hub before moving to individual items
- move through smaller paginated gallery scenes and a workspace-root file browser where folders, models, texts, audio files, and unsupported files use different tactile 3D shapes
- expect file-browser paging to be resolved server-side so larger external folders can still be navigated through bounded scene pages
- use explicit in-scene `Launcher` controls plus `Gallery` or `Browser` return controls and `Start` or `Root` controls to jump back to the main menu, the current origin page, or the beginning of the active gallery or browser flow
- expect `Launcher` to return to the neutral launcher hub, while `Gallery` or `Browser` return to the exact gallery page or file-browser location that launched the current scene and `Start` or `Root` return to the beginning of the active gallery or browser flow
- keep the current orbit, pan, and zoom viewpoint while moving through desktop scenes on the same page; the view should only reset when explicitly requested or when leaving the page
- open a detail plaque that exposes the content name before opening the real scene
- open 3D model scenes, Braille reading scenes, and audio transport scenes with scene-native return controls
- from the file browser, open supported files directly in their corresponding runtime mode: models in the 3D model scene, texts in the Braille reading scene, and audio files in the audio transport scene

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
- inspect registry diagnostics when a previously registered workspace file is missing or its descriptor is invalid
- expect the manager to show descriptor labels and registry file labels by default rather than full absolute local paths

### 5. Haptic Configuration

Route:

```text
/haptic-configuration
```

Current use:

- inspect the requested runtime backend separately from the currently active fallback backend
- configure SDK roots and bridge paths for the first tracked vendor stacks
- persist preferred device selectors so a backend can probe a specific runtime label before falling back to its default selector path
- inspect build-tool readiness for the native bridge workflow
- review the native bridge source root, build-root pattern, and recommended bootstrap commands
- inspect per-backend bridge-probe state before claiming that a physical runtime exists
- review vendor-aware probe summaries, including OpenHaptics conservative default-device probe states plus reported capability channels and Force Dimension detected-device identities when a supported runtime is present
- review dependency readiness for the OpenHaptics, Force Dimension, and CHAI3D-oriented paths
- inspect the current design baseline for collision, contact, material rendering, reusable scene primitives, and backend readiness
- inspect the backend-aware contact rollout plan that names one bounded pilot primitive, one pilot profile, and one next engineering step for each stack
- keep the built-in visual emulator as the safe default runtime until a native bridge is ready

This route is not a substitute for the future native backend. Its role is to make the hardware path explicit, testable, and documentable before real devices are attached.

Bridge-bootstrap commands:

```powershell
python scripts\haptic_bridge_diagnostics.py
.\scripts\Bootstrap_HapticBridge.ps1 -Backend openhaptics-touch -Build
.\scripts\Bootstrap_HapticBridge.ps1 -Backend forcedimension-dhd -Build
```

## Runtime Information

All pages expose:

- API status
- application version
- public port
- haptic backend mode

If no physical haptic device is configured, the application remains usable in visual fallback mode.

If a workspace cannot initialize correctly, the stage should now expose a visible startup error instead of remaining silently stuck in placeholder states such as `v--`, `Loading`, or `Waiting`.

On 3D routes, orbit, pan, and zoom changes should persist across scene rebuilds while the user remains on the same page.

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

### Demo 3D Models

```text
GET /api/demo-models
```

### Haptic Backend Status

```text
GET /api/device/status
```

### Haptic Runtime Configuration

```text
GET /api/haptics/configuration
POST /api/haptics/configuration
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
GET /api/haptic-workspaces/{slug}/browse?path=&page=0&page_size=6
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

- no physical device loop is connected to the scene runtime yet, even though the haptic-configuration route now tracks backend selection intent, vendor dependency readiness, bridge-probe state, and toolchain availability
- the Force Dimension DHD path can now load the runtime library and enumerate devices through the native probe, OpenHaptics can now load the HD runtime library set, attempt a conservative default-device open, and report capability channels, and CHAI3D remains a scaffold-level probe path
- no current probe drives force output, calibration, homing, or scene-coupled haptic interaction
- 3D object staging is currently client-side and focused on `obj`, `stl`, `glb`, self-contained `gltf`, and local `gltf` bundles selected together with their sidecar resources
- document compatibility is currently limited to bundled `txt`, `html`, and `epub` assets
- workspace authoring is currently JSON-descriptor based and still needs richer validation and editing affordances
- desktop actions are limited to models, text, audio, and file browsing rather than full desktop automation
- haptic material profiles are plausible approximations, not full physical simulation
