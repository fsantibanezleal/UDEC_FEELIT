# Development History

## Legacy Background

### v1.7.5 and earlier

The preserved FeelIT archive documents a Windows-based application oriented to tactile access for people with visual impairment. The recoverable evidence confirms:

- text-file loading
- character-by-character Braille conversion
- optional haptic interaction with a Novint Falcon-style device
- OpenGL-based visual rendering

The archived user manual describes the software as a digital-to-relief presentation system with haptic feedback. The preserved implementation that can be verified today is the Braille reading mode.

## Modern Rebuild Timeline

### v2.05.002 (2026-03-29)

Regularize the active FeelIT line onto a legacy-aware release 2 and adopt the fixed-width canonical version format X.XX.XXX.

Delivered:

- Promoted the active FeelIT line from the previous 0.5.x path to the canonical padded version 2.05.002.
- Updated version tooling so runtime, documentation, PyInstaller metadata, and Inno Setup metadata all consume the padded canonical format.
- Introduced a packaging-safe normalized version derivation for Python package metadata while preserving the padded workspace version as the canonical project string.

Rationale:

- FeelIT is a modernization of a prior initiative and should not present its active line as an early 0.x prototype.
- The fixed-width version format improves scanability, consistency, and long-range release tracking across the workspace.

### v0.5.5 (2026-03-29)

Promote tracked frontend snapshot archives into the FeelIT release workflow and preserve the current UI baseline in git.

Delivered:

- Stopped blanket-ignoring curated artifacts and documented the tracked frontend snapshot archive structure.
- Expanded the browser smoke workflow to capture all current frontend routes, including the Haptic Workspace Manager.
- Archived the visual baseline under artifacts/frontend_snapshots/history/v0.5.4 before preparing the new release baseline.

Rationale:

- The repository should preserve visual evidence of the shipped interface, not only textual documentation and SVG diagrams.
- Frontend evolution needs a stable release-by-release audit trail for UI reviews, regression checks, and methodological history.

### v0.5.4 (2026-03-29)

Patch release focused on typed Haptic Desktop file-browser interaction, contextual Home or Launcher return semantics, and stronger workspace item contracts.

Delivered:

- Added explicit file-kind contracts for Haptic Desktop entries, including tactile shape keys, mode-routing metadata, and mode-specific action labels.
- Routed supported file-browser files into their corresponding runtime scenes while keeping Home tied to the exact origin and Launcher tied to the workspace start scene.
- Fixed fallback activation priority for focused desktop targets and extended automated coverage for file-kind mode mapping plus Haptic Desktop scene flow.

Rationale:

- Keep Haptic Desktop navigation consistent for blind-first workflows by making file type, tactile representation, mode dispatch, and return semantics follow one explicit contract.
- Prevent focus-driven fallback interaction from silently activating the wrong target when the pointer and fallback focus diverge.

### v0.5.3 (2026-03-29)

Patch release focused on deterministic launcher return semantics in Haptic Desktop and regression coverage for held activation across scene transitions.

Delivered:

- Made Launcher returns land on a neutral launcher hub instead of inheriting focus on a specific gallery tile.
- Suppressed repeated held-key activations during scene transitions in the shared pointer emulator.
- Extended the browser smoke validator to reproduce and guard the file-browser-to-launcher return path.

Rationale:

- Keep Haptic Desktop navigation semantically stable so blind-first return controls always land in the expected scene and focus anchor.
- Prevent held activation from leaking across scene rebuilds and causing accidental follow-up navigation.

### v0.5.2 (2026-03-29)

Patch release focused on explicit launcher and start or root return controls across Haptic Desktop scenes.

Delivered:

- Replaced ambiguous Home controls with explicit Launcher controls across galleries, file-browser scenes, detail scenes, and opened content scenes.
- Added direct Start and Root controls so users can jump back to the beginning of the active gallery or browser flow without stepping through intermediate pages.
- Extended the browser smoke validator to exercise gallery Next, Start, and Launcher controls through the fallback focus path.

Rationale:

- Keep blind-first scene navigation explicit and predictable by separating return-to-launcher from return-to-gallery-start semantics.
- Make the no-device runtime emulate the same controlled navigation paths that a future haptic-only workflow will require.

### v0.5.1 (2026-03-29)

Patch release focused on full bundled gallery coverage in the demo workspace, clearer Haptic Desktop pagination, and isolated browser smoke validation.

Delivered:

- Merged the bundled demo workspace with the full internal model, text, and audio catalogs so every bundled asset appears in Haptic Desktop galleries.
- Reduced gallery density per page and reworked gallery framing so multiple tactile items are clearly staged in the 3D scene at once.
- Hardened the browser smoke test to launch FeelIT on an isolated temporary port and verify real gallery pagination.

Rationale:

- Keep the default demo workspace aligned with the actual internal library instead of drifting into a partial subset.
- Make the gallery scene visually and operationally communicate that users are moving through a real paginated collection, not a single-item showcase.
- Prevent false regression results caused by stale local servers already occupying the default application port.

### v0.5.0 (2026-03-29)

Release focused on workspace-driven Haptic Desktop scenes, structured haptic_workspace descriptors, and the first external-workspace management flow.

Delivered:

- Added the haptic_workspace descriptor format, bundled demo workspace, external-root registry flow, and a dedicated Workspace Manager page.
- Rebuilt Haptic Desktop around a scene graph with launcher, curated galleries, file-browser navigation, detail plaques, and opened scenes for models, text, and audio.
- Expanded automated coverage with workspace-domain tests, API tests, and a stronger browser smoke validator for desktop workspace bootstrap.

Rationale:

- Shift Haptic Desktop from a static prototype into a real workspace-driven interaction model aligned with the project vision.
- Treat structured workspace authoring, external asset roots, and blind-first scene transitions as product-level capabilities rather than future notes.

### v0.4.0 (2026-03-29)

Release focused on the internal public-domain reading library, expanded demo assets, and stronger asset-validation coverage.

Delivered:

- Added a bundled public-domain document and audio library with TXT, HTML, and EPUB support plus segmented loading for the Braille Reader.
- Expanded the bundled OBJ catalog with additional lightweight demo models and extended the material profile set with paper and ceramic approximations.
- Hardened local execution and validation through a launcher regression fix, per-file asset-size tests, and richer browser smoke checks for the Braille workspace.

Rationale:

- Make the Braille Reader immediately demonstrable with curated internal content instead of ad hoc sample text.
- Increase tactile exploration variety without inflating the repository or exceeding the 60 MB per-file asset threshold.
- Treat asset provenance, runtime reliability, and regression coverage as part of the delivered product surface.

### v0.3.1 (2026-03-29)

Release focused on reliable frontend bootstrap, visible startup diagnostics, and regression coverage for runtime placeholders.

Delivered:

- Replaced the fragile global shell bootstrap with module-based imports shared by the three workspace entrypoints.
- Added visible workspace boot diagnostics so stale placeholders such as v--, Loading, or Waiting are no longer silent failure states.
- Hardened the browser smoke validator to fail when runtime metadata placeholders do not initialize.

Rationale:

- Eliminate bootstrap races that can leave the frontend shell and 3D scenes uninitialized in some real browser runs.
- Turn user-visible startup ambiguity into explicit diagnostics and automated regression coverage.

### v0.3.0 (2026-03-29)

Release focused on trustworthy 3D interaction worlds, stylus-style pointer emulation, and scene-native tactile controls.

Delivered:

- Fixed the bundled three.js runtime so all mode workspaces load coherent module assets without the missing three.core.js failure.
- Upgraded the shared pointer emulator into a stylus-like proxy with safer keyboard capture, surface-state feedback, and activation cues.
- Reworked Braille and desktop scenes around spatially meaningful tactile geometry instead of overlapping explanatory labels.

Rationale:

- Treat the visible 3D worlds as the real interaction contract for no-device execution, not as decorative previews.
- Keep release versioning, packaging metadata, and development history synchronized with each completed implementation cycle.

### v0.2.0 (2026-03-29)

Release focused on real 3D workspace delivery, tactile material modeling, and stricter documentation and diagram governance.

Delivered:

- Added real 3D worlds for Object Explorer, Braille Reader, and Haptic Desktop instead of placeholder surfaces.
- Bundled local OBJ demo assets and exposed material and demo-model catalogs through the API.
- Reworked project documentation and SVG diagrams to match the new runtime baseline and stricter workspace presentation rules.

Rationale:

- Treat spatial and haptic-facing modes as real interaction worlds rather than explanatory mockups.
- Keep versioning, packaging metadata, diagrams, and methodological history synchronized as part of the release surface.

### v0.1.1 (2026-03-28)

Release focused on frontend standardization, workspace separation, and release-governance hardening.

Delivered:

- Replaced the single long frontend with dedicated Object Explorer, Braille Reader, and Haptic Desktop pages.
- Aligned the frontend shell with the reference workbench style: dark theme, technical header, runtime status, panels, and help modal.
- Added scope and motivation documentation and refreshed README, architecture, and user guide to match the actual product structure.
- Synchronized canonical version metadata with README and Windows packaging artifacts.

Rationale:

- Treat frontend structure as a workspace standard rather than an ad hoc implementation detail.
- Make version bumps traceable across code, documentation, and packaging outputs.

### v0.1.0 (2026-03-28)

Initial modern repository bootstrap.

Delivered:

- Python 3.12 project structure
- FastAPI backend
- static frontend shell
- Braille preview API
- null haptic backend abstraction
- standardized documentation set
- tests
- PyInstaller and Inno Setup scaffolding

Rationale:

- establish a stable project spine before implementing deeper 3D and haptic interaction logic
- preserve the verified legacy baseline without overclaiming missing legacy functionality
- keep the application runnable immediately even when no physical haptic hardware is available

## Planned Milestones

### v0.3.x

- richer 3D asset pipeline beyond current OBJ staging
- server-side asset validation and metadata persistence
- tighter mapping from material profiles to device-specific force models

### v0.4.x

- richer Braille document compatibility beyond TXT, HTML, and EPUB
- scene-native library launch for blind-first reading sessions
- improved layout constraints tied to device workspace assumptions

### v2.06.x

- richer haptic_workspace authoring and validation
- blind-first desktop help and cue refinement
- stronger gallery and file-browser interaction coverage

### v2.07.x

- first native physical haptic bridge integration
- device capability detection
- hardware-assisted exploration loop

## Versioning Policy

The canonical modern FeelIT line now uses the workspace fixed-width format `X.XX.XXX`.

For FeelIT, release `2` is the active modernization line because the current repository is a successor to a real prior initiative rather than a disposable greenfield prototype.

That means:

- major release uses the left segment and is normally shown without padding
- minor release uses two digits of padding
- patch release uses three digits of padding
- example: `2.05.002`

When external Python packaging tooling requires normalized numeric segments, it may derive a compatibility version such as `2.5.2`, but the canonical project version shown by the app, documentation, and Windows build metadata remains the padded workspace format.

