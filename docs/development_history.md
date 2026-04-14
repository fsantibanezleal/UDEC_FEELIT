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

### v2.18.008 (2026-04-14)

Add asset-aware library previews and item-level editing to the Haptic Workspace Manager so curated descriptor authoring can happen safely from the UI instead of raw JSON edits.

Delivered:

- Extended the workspace descriptor preview contract with full authored item lists plus discovered content-root candidates per category.
- Added safe add, update, reorder, and remove operations for user-registered workspace library items, with API coverage and descriptor persistence.
- Expanded the Workspace Manager UI so users can curate model, text, and audio entries directly from the manager.

Rationale:

- The manager can now author curated workspace subsets and ordering instead of stopping at aggregate count previews.
- This closes the main product gap left after descriptor preview and lifecycle actions were added in previous cycles.

### v2.18.007 (2026-04-14)

Add descriptor preview and structured editing to the Haptic Workspace Manager so registered workspace files can be inspected and edited before lifecycle actions rewrite them.

Delivered:

- Added descriptor-preview and structured-editing API surfaces for registered workspaces plus repair-preview payloads for invalid descriptors.
- Extended the Workspace Manager UI with an editable descriptor form, a pending-edit preview, and current-versus-rescan preview summaries for models, texts, and audio.
- Expanded automated coverage around descriptor preview, structured updates, repair preview, and the updated browser-smoke capture surface.

Rationale:

- Lifecycle actions without preview kept the manager too opaque for real workspace authoring work.
- This slice moves the manager from registry maintenance toward a safer descriptor-authoring surface while preserving conservative write rules.

### v2.18.006 (2026-04-13)

Add lifecycle actions to the Haptic Workspace Manager so registered descriptors can be rescanned, unregistered, and conservatively repaired from the UI.

Delivered:

- Added registry-backed lifecycle actions for Haptic Workspace Manager workspaces: unregister, library rescan, and invalid-descriptor repair.
- Extended the FastAPI workspace endpoints plus Python tests so registry operations are covered through both core functions and the public API surface.
- Updated the manager UI so selected workspaces and invalid registry entries expose lifecycle actions directly instead of remaining read-only diagnostics.

Rationale:

- Workspace management had progressed beyond first registration, so the route needed real recovery and maintenance operations rather than another passive diagnostics panel.
- The new actions close the most immediate lifecycle gap while leaving richer descriptor editing and preview tooling as a separate future concern.

### v2.18.005 (2026-04-13)

Extend scene-native control reachability regression coverage from Object Explorer into Braille Reader and Haptic Desktop.

Delivered:

- Exposed Braille Reader and Haptic Desktop debug geometry for scene-native targets plus current pointer bounds so reachability can be asserted from browser smoke.
- Extended browser smoke to verify critical launcher, return, gallery, and file-browser controls remain inside the bounded interaction volume across the other spatial routes.
- Added targeted helper tests for the shared reachability assertions and documented the deeper validation surface through the release metadata update.

Rationale:

- Object Explorer already proved that static scene-control layout can drift out of the navigable volume unless the browser smoke contract checks geometry explicitly.
- Reachability is a blind-first runtime guarantee, so it should be enforced consistently across the spatial routes instead of route by route.

### v2.18.004 (2026-04-13)

Hide internal workspace descriptor files from the tactile browser and make Object Explorer scene-native controls provably reachable inside the pointer workspace.

Delivered:

- Filtered .haptic_workspace.json descriptor files out of the Haptic Desktop file browser payload so internal metadata no longer appears as unsupported user content.
- Derived the Object Explorer exploration control rail from the staged object bounds and exposed debug geometry so the Launcher and material-cycle targets stay inside the navigable pointer volume.
- Extended browser smoke and Python tests to validate scene-native control reachability plus the new browser filtering rule.

Rationale:

- The tactile browser should present user content, not implementation metadata.
- Object Explorer control reachability needed an explicit geometric rule and regression coverage rather than another static layout tweak.

### v2.18.003 (2026-04-12)

Established an enforced Ruff baseline and wired it into the repo-managed validation flow.

Delivered:

- Configured Ruff to enforce structural rules while staging the historical line-length backlog as explicit debt.
- Integrated lint into scripts/validate_repo.py and GitHub Actions so local and CI validation now share the same enforced baseline.
- Fixed the import-order and unused-import findings that blocked the initial enforced Ruff pass.

Rationale:

- The repository now has CI, so lint needed to become actionable instead of remaining a local-only failing report.
- A progressive baseline is more credible than either ignoring Ruff completely or trying to clean hundreds of line-length findings in one noisy slice.

### v2.18.002 (2026-04-12)

Strengthened FeelIT's validation baseline and documentation-facing screenshot workflow.

Delivered:

- Extended the browser smoke workflow so Braille launcher and Braille reading-world screenshots are captured as separate curated artifacts.
- Added a repo-managed validation entrypoint with unit, browser-smoke, full, and lint-baseline modes.
- Added GitHub Actions CI for unit/API validation plus browser smoke on pushes and pull requests.

Rationale:

- README-facing screenshots should come from intentional canonical states instead of manual drift-prone updates.
- FeelIT needed one validation contract that works locally and in GitHub Actions instead of relying only on manual discipline.

### v2.18.001 (2026-04-02)

Add progressive disclosure to Haptic Configuration and expose runtime-query frontiers

Delivered:

- Reworked the Haptic Configuration route into explicit `Focus`, `Contracts`, `Execution`, and `Bridge` review lanes so the operator no longer has to scan the full route wall to find the active diagnostic path.
- Collapsed advanced SDK-root, bridge-path, and preferred-selector editing behind disclosure panels so the route keeps the current operating focus visible while still preserving full engineering detail.
- Added focused runtime-summary cards for next pilot, readiness, and next engineering step so the selected backend drill-down is actionable above the fold.
- Extended the bridge contract and runtime manager with explicit runtime-query frontier semantics plus queryable-versus-already-queried characteristic lists, giving OpenHaptics and Force Dimension a more honest diagnostic boundary.
- Refreshed the README, user guide, runtime design notes, implementation-gap audit, and haptic-configuration screenshot to reflect the new review flow and query-frontier terminology.

Rationale:

- This is a patch-level release because it improves the structure, diagnosability, and honesty of the shipped haptic runtime surface without claiming a new full native control milestone.
- The route was carrying too much technically relevant information at one flat hierarchy level. Progressive disclosure plus explicit query-frontier language reduces operator scanning cost while keeping the haptics workbench technically deep.

### v2.18.000 (2026-04-02)

Expand bounded native execution to Force Dimension and sharpen Haptic Configuration focus

Delivered:

- Extended the native bridge so the Force Dimension DHD path can execute one bounded rigid-surface pilot step in the same explicit no-force safety envelope already used for the OpenHaptics button-actuation path.
- Added stronger Haptic Configuration route hierarchy with a native spotlight summary, execution-coverage summary, default focus on the richest native backend, and clearer card-state semantics for active runtime versus inspector focus versus spotlight.
- Expanded runtime, smoke, and native integration coverage so the second bounded native execution path and the new configuration-page focus rules are both validated automatically.
- Refreshed README, technical haptics docs, screenshots, and SVG wording so the release no longer describes bounded execution as OpenHaptics-only.

Rationale:

- This is a material capability expansion rather than a patch because the native bridge now covers bounded execution across two vendor stacks instead of only one.
- The release also closes a real UX comprehension gap in the Haptic Configuration route by making the richest native evidence visible above the fold without conflating it with the active visual fallback path.

### v2.17.000 (2026-04-01)

Execute the first bounded native haptic pilot step through the OpenHaptics bridge boundary.

Delivered:

- Extended the native bridge so it can consume the existing pilot command contract and execute one bounded OpenHaptics button-actuation step in a clamped no-force safety mode.
- Surfaced bounded execution state beside acknowledgement state in the Haptic Configuration route and runtime snapshot.
- Updated the haptic runtime, bootstrap, and implementation-gap documentation so the product no longer describes this milestone as acknowledgement-only.

Rationale:

- This is a real capability expansion beyond the earlier acknowledgement-only milestone because the native bridge now crosses the first execution boundary for one bounded pilot primitive.
- The release still stays honest about scope: this is not full force output, calibration, homing, or a scene-coupled servo loop.
### v2.16.002 (2026-04-01)

Refine Haptic Desktop navigation clarity and normalize native haptic capability reporting.

Delivered:

- Added a Haptic Desktop navigation trail panel plus smoke coverage for launcher, gallery, browser, and reading-scene ancestry.
- Normalized native bridge capability reporting into a shared runtime-feature schema with verified-versus-inferred evidence in the configuration route.
- Updated haptic runtime docs and user guidance so the reported backend state matches the current bridge and UX surface.

Rationale:

- This iteration improves diagnostics, UX clarity, and rollout reliability without yet introducing live force execution or a new routed workspace capability boundary.

### v2.16.001 (2026-04-01)

Declare and install python-multipart so multipart upload routes boot correctly in the project environment.

Delivered:

- Added python-multipart as a required runtime dependency in the project manifest and lightweight requirements surface.
- Reinstalled the project environment in editable mode so the .venv now contains the multipart parser required by the upload and form routes.
- Validated the repaired environment through the full automated test suite and pip dependency checks.

Rationale:

- The application currently exposes Form and UploadFile routes, so multipart parsing is part of the real runtime contract rather than an optional extra.
- This is a patch-level runtime dependency fix that restores environment correctness without changing the product capability boundary.

### v2.16.000 (2026-04-01)

Add a dry-run native acknowledgement boundary for bounded haptic pilot commands.

Delivered:

- Added bridge-facing pilot command contracts for backend-specific haptic pilots.
- Extended the native bridge executable so it can validate and acknowledge one bounded pilot command payload in dry-run mode.
- Surfaced bridge-side pilot acknowledgement through the Haptic Configuration route and runtime snapshot.
- Expanded runtime, API, and native-bridge tests for the new acknowledgement boundary.

Rationale:

- This is a material expansion of the haptic backend surface because FeelIT now proves a bridge-side contract boundary beyond probe-only diagnostics.
- The release still stays honest about scope: acknowledgement exists, but execution, force output, and servo-loop ownership remain future work.

### v2.15.000 (2026-03-31)

Deepen the haptic runtime surface with explicit scene contracts, backend-aware pilot rollout planning, and preferred vendor device selection for the next native-contact milestone.

Delivered:

- Added persisted preferred device selectors so OpenHaptics probing can start from an operator-defined target before falling back to its default selectors.
- Added explicit scene-to-backend haptic contracts with reusable primitive families, backend-readiness rows, and mode-specific return-flow expectations.
- Expanded the haptic configuration route with backend-aware contact rollout planning, pilot profiles, and runtime-feature coverage alignment against reported bridge capabilities.
- Release-synced the preferred device selector path plus the richer OpenHaptics and Force Dimension diagnostics already accumulated on develop.

Rationale:

- This is a material expansion of FeelIT's haptic runtime capability surface, not just a small patch, because the app now exposes a coherent next-step boundary between diagnostics and scene-coupled haptics.
- The release stays honest about what is still missing: native force execution is still pending, but the configuration route can now express the first bounded pilots in a backend-specific way.

### v2.14.000 (2026-03-31)

Deepen the OpenHaptics native bridge with conservative default-device probing and richer capability diagnostics.

Delivered:

- Extended the OpenHaptics native probe so it can attempt a conservative default-device open instead of stopping at runtime-load plus minimal symbol validation.
- Added probe payload fields for enumeration mode, capability scope, resolved symbols, attempted selectors, reported capability channels, and probe notes.
- Surfaced the richer bridge diagnostics through the runtime manager and the Haptic Configuration route so capability reporting is visible inside the product.
- Expanded native integration coverage and refreshed the haptic runtime documentation to match the stronger OpenHaptics bridge boundary.

Rationale:

- This batch materially expands the native haptic backend truth surface rather than only refining existing text or visuals.
- OpenHaptics now crosses a more meaningful readiness boundary that the runtime and the docs can expose honestly before live scene-coupled force output exists.

### v2.13.000 (2026-03-30)

Expand the Object Explorer import pipeline with server-side validation, staging guidance, and bundle-aware local glTF intake.

Delivered:

- Added server-side validation endpoints for local model uploads and multi-file local bundles across OBJ, STL, GLTF, and GLB flows.
- Derived staging guidance from geometry bounds, dominant-axis analysis, and workspace-scale recommendations before browser-side scene opening.
- Extended the local import UX with multi-file bundle selection, explicit main-file choice, bundle diagnostics, and bundle-aware sidecar loading for local glTF assets.
- Hardened browser smoke validation so benign Chromium GPU `ReadPixels` warnings do not produce false 404-style failures during release snapshot capture.
- Updated README, user guidance, implementation-gap notes, curated screenshots, and automated coverage to reflect the stronger import pipeline.

Rationale:

- The Object Explorer now crosses a new capability boundary by moving from browser-only parsing into a documented backend-assisted import path.
- Bundle-aware local glTF intake and backend-derived staging guidance materially expand what the application can accept and explain to the user before scene entry.

### v2.12.000 (2026-03-30)

Extend the native bridge layer with a vendor-aware OpenHaptics probe that loads runtime libraries and reports non-scaffold capability states.

Delivered:

- Added an OpenHaptics vendor-aware native probe path that loads the HD runtime library set and checks minimal HDAPI entry points through the existing bridge JSON contract.
- Extended the runtime manager and haptic-configuration diagnostics so OpenHaptics can move beyond scaffold-only into an explicit runtime-loaded capability state without pretending safe device enumeration exists yet.
- Added isolated native integration coverage with a mock OpenHaptics SDK root and runtime DLLs, and refreshed the docs and SVGs to reflect the broader vendor-aware bridge baseline.

Rationale:

- This release materially expands FeelIT's native bridge coverage from one vendor family to two tracked vendor paths.
- The application can now prove vendor-aware runtime loading for OpenHaptics instead of treating that stack as marker-only bootstrap state.

### v2.11.000 (2026-03-30)

Add the first vendor-aware native bridge probe path by loading the Force Dimension DHD runtime and surfacing real device enumeration results.

Delivered:

- Extended the native bridge probe so the Force Dimension backend can dynamically load the DHD runtime library, report the SDK version, and enumerate device identities through the existing JSON contract.
- Updated the runtime manager and haptic-configuration inspector to surface richer bridge-probe states, runtime summaries, and detected device identities without breaking the safe visual fallback path.
- Added native-bridge integration coverage with a mock DHD runtime DLL, refreshed the docs and SVG suite, and kept the current visual snapshot archive aligned with the new configuration surface.

Rationale:

- This release materially expands FeelIT beyond bootstrap-only diagnostics by giving one tracked vendor stack a real vendor-aware probe path with runtime loading and device enumeration.
- The application can now distinguish scaffold-only readiness from a concrete vendor runtime that loads and reports devices, which changes what the haptic backend layer can actually prove.

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

### v2.13.x

- persistent normalized model metadata and preprocessing artifacts for reused local import sessions
- repair or repackaging support for incomplete or external-resource-heavy 3D asset bundles
- richer server-side import constraints for orientation, scale normalization, and safer asset reuse across scenes

### v2.14.x

- first live native device activation path with calibration, homing, and device-selection diagnostics
- initial device-backed collision-proxy integration for object, Braille, and desktop scenes
- first hardware-assisted interaction loop that goes beyond probe-only enumeration

## Versioning Policy

The canonical modern FeelIT line now uses the workspace fixed-width format `X.XX.XXX`.

For FeelIT, release `2` is the active modernization line because the current repository is a successor to a real prior initiative rather than a disposable greenfield prototype.

That means:

- major release uses the left segment and is normally shown without padding
- minor release uses two digits of padding
- patch release uses three digits of padding
- example: `2.05.002`

When external Python packaging tooling requires normalized numeric segments, it may derive a compatibility version such as `2.5.2`, but the canonical project version shown by the app, documentation, and Windows build metadata remains the padded workspace format.

