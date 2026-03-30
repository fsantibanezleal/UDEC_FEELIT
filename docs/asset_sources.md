# FeelIT Asset Sources

## Purpose

This document records the provenance of the bundled demo geometry and internal library assets shipped with FeelIT.

## Asset Governance Rules

- Every bundled asset must remain below the repository threshold of `60 MB` per individual file.
- Demo geometry used for internal prototyping must have a traceable origin: upstream URL or explicit in-repository generation note.
- Bundled documents and audio must come from public-domain or equivalently safe-to-bundle sources, with provenance preserved in this file.
- Before public redistribution through packaged installers, the final release process must re-check the attribution and redistribution status of every third-party asset.

## Bundled 3D Models

### Bundled OBJ Models

### Walt Head

- local file: `app/static/assets/models/demo/WaltHead.obj`
- source: `three.js examples`
- upstream URL: `https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/walt/WaltHead.obj`
- use in FeelIT: contour-rich sculpture for facial relief exploration

### Tree

- local file: `app/static/assets/models/demo/tree.obj`
- source: `three.js examples`
- upstream URL: `https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/tree.obj`
- use in FeelIT: organic branching form for irregular silhouette and trunk exploration

### Male Figure

- local file: `app/static/assets/models/demo/male02.obj`
- source: `three.js examples`
- upstream URL: `https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/male02/male02.obj`
- use in FeelIT: human-scale reference for posture and proportion

### Female Figure

- local file: `app/static/assets/models/demo/female02.obj`
- source: `three.js examples`
- upstream URL: `https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/female02/female02.obj`
- use in FeelIT: alternate human-form reference for guided exploration

### Cerberus

- local file: `app/static/assets/models/demo/Cerberus.obj`
- source: `three.js examples`
- upstream URL: `https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/cerberus/Cerberus.obj`
- use in FeelIT: dense creature geometry for complex tactile-path testing

### Ninja Head

- local file: `app/static/assets/models/demo/ninjaHead_Low.obj`
- source: `three.js examples`
- upstream URL: `https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/ninja/ninjaHead_Low.obj`
- use in FeelIT: compact scan for facial contour trials with lower mesh weight than full-body figures

### Closed Book

- local file: `app/static/assets/models/demo/closed_book.obj`
- source: FeelIT internal lightweight geometry
- upstream URL: generated in repository
- use in FeelIT: planar-cover and page-block exploration

### Open Book

- local file: `app/static/assets/models/demo/open_book.obj`
- source: FeelIT internal lightweight geometry
- upstream URL: generated in repository
- use in FeelIT: sloped-page and spine exploration for reading-adjacent interaction demos

### Terrain Peak

- local file: `app/static/assets/models/demo/terrain_peak.obj`
- source: FeelIT internal lightweight geometry
- upstream URL: generated in repository
- use in FeelIT: topographic relief and slope transition exploration

### Low-Poly Vase

- local file: `app/static/assets/models/demo/vase_lowpoly.obj`
- source: FeelIT internal lightweight geometry
- upstream URL: generated in repository
- use in FeelIT: household-object profile exploration with neck and shoulder transitions

### Bundled STL Models

### Tactile Bridge

- local file: `app/static/assets/models/demo/tactile_bridge.stl`
- source: FeelIT internal generated geometry
- upstream URL: generated in repository
- use in FeelIT: tactile path-following trials with supports and one raised guide rail

### Locator Token

- local file: `app/static/assets/models/demo/locator_token.stl`
- source: FeelIT internal generated geometry
- upstream URL: generated in repository
- use in FeelIT: compact navigation token for orientation and rotational recognition trials

### Bundled glTF And GLB Models

### Orientation Marker

- local file: `app/static/assets/models/demo/orientation_marker.gltf`
- source: FeelIT internal generated geometry
- upstream URL: generated in repository
- use in FeelIT: self-contained glTF marker for direction and anchor-cue exploration

### Navigation Puck

- local file: `app/static/assets/models/demo/navigation_puck.glb`
- source: FeelIT internal generated geometry
- upstream URL: generated in repository
- use in FeelIT: binary glTF stepped token used to validate non-OBJ runtime loading in bounded scenes

## Bundled Public-Domain Documents

### Alice's Adventures in Wonderland

- local file: `app/static/assets/library/documents/alice_in_wonderland.txt`
- format: `txt`
- source: Project Gutenberg
- upstream URL: `https://www.gutenberg.org/ebooks/928`
- use in FeelIT: narrative sample for segmented loading and Braille scene generation

### Pride and Prejudice

- local file: `app/static/assets/library/documents/pride_and_prejudice.txt`
- format: `txt`
- source: Project Gutenberg
- upstream URL: `https://www.gutenberg.org/ebooks/1342`
- use in FeelIT: long-form prose sample for larger segmented reading sessions

### Pride and Prejudice (EPUB)

- local file: `app/static/assets/library/documents/pride_and_prejudice.epub`
- format: `epub`
- source: Project Gutenberg
- upstream URL: `https://www.gutenberg.org/ebooks/1342.epub.noimages`
- use in FeelIT: EPUB parsing and normalization validation

### The Raven

- local file: `app/static/assets/library/documents/the_raven.html`
- format: `html`
- source: Project Gutenberg
- upstream URL: `https://www.gutenberg.org/ebooks/1065`
- use in FeelIT: short-form marked-up text for HTML extraction tests

### Feeding the Mind

- local file: `app/static/assets/library/documents/feeding_the_mind.txt`
- format: `txt`
- source: Project Gutenberg
- upstream URL: `https://www.gutenberg.org/ebooks/35535`
- use in FeelIT: compact essay-sized sample for quick Braille scene iteration

## Bundled Public-Domain Audio

### Alice's Adventures in Wonderland, Chapter 1

- local file: `app/static/assets/library/audio/alice_chapter_01.mp3`
- source: Project Gutenberg Audio / LibriVox volunteers
- upstream URL: `https://www.gutenberg.org/files/23716/mp3/23716-01.mp3`
- use in FeelIT: optional companion track for the internal reading library

### Alice's Adventures in Wonderland, Chapter 2

- local file: `app/static/assets/library/audio/alice_chapter_02.mp3`
- source: Project Gutenberg Audio / LibriVox volunteers
- upstream URL: `https://www.gutenberg.org/files/23716/mp3/23716-02.mp3`
- use in FeelIT: second-track continuation for library workflow validation

### The Raven

- local file: `app/static/assets/library/audio/the_raven_librivox.mp3`
- source: Internet Archive / LibriVox volunteers
- upstream URL: `https://archive.org/details/raven`
- use in FeelIT: short-form companion audio example

### A Visit from St. Nicholas

- local file: `app/static/assets/library/audio/visit_from_saint_nicholas_v1.mp3`
- source: Internet Archive / LibriVox volunteers
- upstream URL: `https://archive.org/details/visitfrom_saint_nicholas_0912_librivox`
- use in FeelIT: additional public-domain audio sample for internal library coverage
