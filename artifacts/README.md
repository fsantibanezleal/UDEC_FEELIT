# FeelIT Visual Artifacts

This directory stores tracked visual evidence of the shipped frontend state.

## Purpose

- preserve the current visual state of the user-facing workspaces
- preserve versioned snapshots that show how the interface evolved over time
- support README documentation, methodological history, issue review, and release audits

## Structure

```text
artifacts/
|-- README.md
`-- frontend_snapshots/
    |-- current/
    |   |-- braille_reader.png
    |   |-- haptic_desktop.png
    |   |-- haptic_workspace_manager.png
    |   |-- object_explorer.png
    |   `-- snapshot_manifest.json
    `-- history/
        `-- v<version>/
            |-- braille_reader.png
            |-- haptic_desktop.png
            |-- haptic_workspace_manager.png
            |-- object_explorer.png
            `-- snapshot_manifest.json
```

## Rules

- `current/` must represent the latest shipped or working baseline that the repository claims to document across the frontend routes.
- `history/v<version>/` stores frozen snapshot sets aligned to released versions.
- Curated visual artifacts are intentionally tracked in git and must not be blanket-ignored.
- Temporary debugging captures that are not part of the documented project state should not remain here.

## Refresh Workflow

From the repository root:

```powershell
python scripts\browser_scene_smoke.py --archive-version <released-version>
```

This updates `current/` and also writes a frozen copy under `history/v<released-version>/`.
