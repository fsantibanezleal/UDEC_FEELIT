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
            |-- <changed-route>.png
            |-- <changed-route>.png
            `-- snapshot_manifest.json
```

## Rules

- `current/` must represent the latest shipped or working baseline that the repository claims to document across the frontend routes.
- `current/` remains a full baseline and should keep one curated image per tracked frontend route.
- `history/v<version>/` stores sparse release evidence aligned to shipped versions and should only include route images whose visible UI changed materially relative to the previous archived baseline.
- Unchanged routes still belong in the history manifest, but their provenance should point back to the most recent archived version that still represents that route visually.
- Curated visual artifacts are intentionally tracked in git and must not be blanket-ignored.
- Temporary debugging captures that are not part of the documented project state should not remain here.

## Refresh Workflow

From the repository root:

```powershell
python scripts\browser_scene_smoke.py --archive-version <released-version>
```

This refreshes `current/` as the full active baseline and writes a sparse release record under `history/v<released-version>/`.

If an already tracked route did not change visually, the archived version directory may contain only the routes that did change plus a manifest that documents which older version still supplies the visual baseline for the unchanged pages.
