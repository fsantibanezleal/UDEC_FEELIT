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

### v2.10.000 (2026-03-30)

Add a reproducible native haptic bridge bootstrap surface with toolchain diagnostics and a compiled probe scaffold.

Delivered:

- Added toolchain detection for CMake, Ninja, clang++, MSBuild, Visual Studio, the MSVC toolset, and the Windows resource compiler inside the haptic runtime snapshot and configuration page.
- Added a native bridge scaffold project, a PowerShell bootstrap script, and a compiled JSON probe executable that FeelIT can discover, run, and classify as scaffold-only versus device-ready.
- Expanded the haptic-configuration route, documentation, SVG diagrams, diagnostics script, and browser validation so the native bridge workflow is visible and reproducible before live device enumeration ships.

Rationale:

- This release adds a new system surface rather than only refining an existing page: FeelIT can now bootstrap, build, and probe a native bridge scaffold locally.
- The haptic backend path now exposes reproducible build-tool and bridge-contract state, which materially changes what the application can support during hardware integration.

### v2.09.000 (2026-03-30)

Add haptic runtime configuration, backend diagnostics, and contact-model baselines

Delivered:

- Added a dedicated haptic-configuration route with backend-selection intent, SDK and bridge tracking, and runtime diagnostics for the first serious physical-stack candidates.
- Added a runtime manager that persists requested-backend configuration, reports vendor-stack readiness, and keeps the visual pointer emulator as the safe active fallback.
- Documented and surfaced the proxy-first collision pipeline and material-rendering baseline through new API payloads, docs, SVG diagrams, and browser validation.

Rationale:

- This release materially expands FeelIT with a new routed workspace and a real haptic-runtime management surface rather than only refining an existing page.
- The project now exposes the central physical-backend problem as part of the product and documentation surface, which is a substantial capability boundary change.

### v2.08.001 (2026-03-30)

This patch improves Haptic Desktop workspace browsing with server-side pagination, reduces repeated external text extraction through freshness-aware caching, and stops exposing absolute local workspace paths by default in the workspace-facing frontend surfaces.

Delivered:

- Added server-side file-browser pagination metadata and lighter directory payloads for Haptic Desktop workspace browsing.
- Added freshness-aware caching for extracted text loaded from external workspace files so Braille segment navigation does not keep reparsing the same source document.
- Sanitized workspace-facing payloads and UI so descriptor labels and registry labels are shown without exposing absolute local paths by default.

Rationale:

- The delivered changes improve performance, privacy, and runtime stability inside existing workflows without introducing a new major user-facing mode.
- The release is a patch because it refines the shipped workspace-management and reading surfaces rather than materially expanding the application capability boundary.
### v2.08.000 (2026-03-29)

Expand FeelIT model loading beyond OBJ with bundled STL, glTF, and GLB demos across Object Explorer and Haptic Desktop.

Delivered:

- Added a shared browser-side model-loading layer that resolves OBJ, STL, glTF, and GLB assets for Object Explorer and Haptic Desktop.
- Bundled new lightweight internal STL, glTF, and GLB demo models and exposed their format metadata through the demo-model API and workspace payloads.
- Extended browser smoke validation to open a GLB session in Object Explorer and an STL file through the Haptic Desktop file browser.

Rationale:

- This release materially expands the 3D asset capability of FeelIT instead of only refining an existing flow, so it warrants a minor-version increment.
- The desktop and explorer should share one consistent model-ingestion contract so workspace browsing and curated demos do not diverge by format.
- Non-OBJ support needed to be proven through bundled demos and browser automation, not only through static catalog metadata.

### v2.07.000 (2026-03-29)

Add a scene-native object-session launcher and blind-first session flow to the 3D Object Explorer.

Delivered:

- Rebuilt Object Explorer around a paged scene-native launcher for curated demo-model sessions instead of booting directly into one preloaded object.
- Added in-scene Launcher plus material-cycling controls so a session can open, evolve, and return without depending only on the surrounding browser panel.
- Extended browser smoke validation to prove launcher pagination, launcher-driven model entry, exploration-scene opening, and return to the originating launcher page.
- Froze a new sparse visual baseline for the route under the `v2.07.000` archive after the launcher redesign.

Rationale:

- The Explorer needed the same blind-first interaction standard already established in Braille Reader and Haptic Desktop.
- Curated demo sessions should begin from tactile scene targets inside the 3D world, not only from form controls outside it.
- Launcher-driven validation is necessary so the regression suite protects the real interaction contract rather than only API availability.

### v2.06.002 (2026-03-29)

Extend deterministic frontend capture and browser-driven desktop validation for the demo workspace.

Delivered:

- Made curated frontend snapshots deterministic by resetting routed pages into stable canonical capture states before writing the tracked images.
- Extended Haptic Desktop smoke coverage to open supported text, audio, and model files from the file browser and validate the return path back to the browser scene.
- Expanded the bundled demo file browser root so the desktop demo can browse models as well as library documents and audio through the same controlled tree.

Rationale:

- Sparse visual history should archive meaningful UI change, not incidental drift from idle animation or leftover test state.
- The desktop browser contract should be validated through real mode dispatch from the file tree, not only through gallery flows or action labels.
- The demo workspace should expose a coherent browser path to the same model assets that the desktop claims to support.

### v2.06.001 (2026-03-29)

Stabilize workspace identity, surface registry diagnostics, and harden release metadata synchronization.

Delivered:

- Made workspace browser entries, auto-populated workspace items, and arbitrary text payloads use collision-resistant stable slugs derived from source identity.
- Surfaced invalid registered haptic workspaces through the manager payload and frontend diagnostics instead of silently dropping them.
- Made the version bump helper fail fast when required source or README anchors are missing, and added regression tests for those failure modes.

Rationale:

- Distinct files must not collapse onto the same logical target inside Haptic Desktop scenes or arbitrary text ingestion flows.
- Workspace management should expose repairable registry problems instead of hiding them from the user and the maintainer.
- Release tooling should fail explicitly when synchronization anchors drift, so documentation and packaging metadata cannot silently go stale.

### v2.06.000 (2026-03-29)

Introduce a scene-native Braille library launcher so tactile reading sessions can begin and return inside the 3D world.

Delivered:

- Added a paged 3D Braille library launcher with tactile document targets as the primary entry path for bundled reading sessions.
- Extended the Braille reading world with scene-native previous and next segment controls plus a tactile return path back to the library launcher.
- Exposed route-level Braille debug hooks and expanded browser smoke coverage to validate launcher-to-reading and reading-to-library transitions.

Rationale:

- This release materially expands the Braille workflow rather than only refining an existing surface, so it warrants a minor-version increment.
- Blind-first access now begins inside the scene itself instead of depending exclusively on surrounding browser controls.

### v2.05.006 (2026-03-29)

Adopt sparse frontend snapshot history so FeelIT only archives changed route images per version while preserving full current baselines.

Delivered:

- Updated the browser smoke workflow to archive only materially changed route captures and to preserve per-route provenance in snapshot manifests.
- Added automated tests for sparse snapshot archiving and redundant-history normalization.
- Documented the snapshot policy so current baselines stay complete while version history stays visually non-redundant.

Rationale:

- Frontend snapshot history should show meaningful UI evolution rather than repeating identical images in every version folder.
- Visual evidence still needs traceability, so unchanged routes now inherit the last valid archived baseline through manifest metadata instead of duplicated files.

### v2.05.005 (2026-03-29)

Preserve the user-adjusted 3D camera viewpoint across scene changes while staying on the same FeelIT route.

Delivered:

- Added shared per-route camera view persistence so orbit, pan, and zoom survive scene transitions inside the same page.
- Updated Haptic Desktop and Braille scene rebuilds to reuse the persisted user view instead of forcing a new camera framing on each scene change.
- Exposed route-level scene debug handles and extended browser smoke coverage to verify persisted camera state across Haptic Desktop scene transitions.

Rationale:

- Scene-driven exploration should not force the user to reframe the viewport after every haptic activation.
- Camera persistence is part of the route interaction contract and needs automated validation, not just manual observation.

### v2.05.004 (2026-03-29)

Compact the shared FeelIT workbench shell so desktop routes fit inside the viewport without document-level vertical scrolling.

Delivered:

- Converted the shared shell into a fixed-height viewport layout with internal panel scrolling instead of page scrolling on desktop.
- Reduced stage and panel expansion pressure so Object Explorer, Braille Reader, Haptic Desktop, and Workspace Manager all fit the desktop viewport.
- Extended the browser smoke validator to fail when any routed page overflows vertically beyond the viewport.

Rationale:

- The workbench layout should present the active scene immediately without forcing the user to scroll before reaching the primary interaction surface.
- Viewport-fit behavior is a frontend contract and needs regression coverage, not just visual spot checks.

### v2.05.003 (2026-03-29)

Tighten the Haptic Desktop gallery and browser return flow so users land on explicit scene hubs instead of falling back onto a content item.

Delivered:

- Added explicit Gallery and Browser hub controls so paginated scenes now open on a scene-level anchor before item-level exploration.
- Changed opened Haptic Desktop scenes to expose contextual return controls labeled Gallery or Browser, alongside Launcher and Start or Root controls.
- Extended the browser smoke validator to assert gallery and file-browser hub focus across launcher, page-turn, return, and folder-entry transitions.

Rationale:

- Blind-first navigation should communicate scene context first, not drop the user directly onto a single item tile.
- Return controls need to make the difference between launcher, current origin page, and first-page or root return paths explicit and testable.

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

### v2.10.x

- vendor-aware bridge probe that can report SDK load results, runtime library load results, device count, and failure reasons
- clearer SDK bootstrap notes and remediation paths for the first tracked hardware families
- follow-up stabilization of the haptic-configuration diagnostics and native bridge authoring workflow

### v2.11.x

- first live native device enumeration path with calibration, homing, and device-selection diagnostics
- initial device-backed collision-proxy integration for object, Braille, and desktop scenes
- first hardware-assisted interaction loop that goes beyond the current scaffold-only bridge contract

## Versioning Policy

The canonical modern FeelIT line now uses the workspace fixed-width format `X.XX.XXX`.

For FeelIT, release `2` is the active modernization line because the current repository is a successor to a real prior initiative rather than a disposable greenfield prototype.

That means:

- major release uses the left segment and is normally shown without padding
- minor release uses two digits of padding
- patch release uses three digits of padding
- example: `2.05.002`

When external Python packaging tooling requires normalized numeric segments, it may derive a compatibility version such as `2.5.2`, but the canonical project version shown by the app, documentation, and Windows build metadata remains the padded workspace format.

