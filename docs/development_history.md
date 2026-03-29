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

- richer Braille document ingestion
- improved layout constraints tied to device workspace assumptions

### v0.5.x

- first native physical haptic bridge integration
- device capability detection
- hardware-assisted exploration loop

### v0.6.x

- haptic desktop content graph
- audio labels and action objects
- curated desktop interaction execution model

## Versioning Policy

The modern rebuild starts in `0.x` because the repository currently represents a new implementation foundation rather than a feature-complete successor to the legacy system.

The first mature release that fully delivers the modern target product can be promoted to `1.0.0` or directly aligned to a legacy-aware `2.0.0` once the scope justifies it.

