# FeelIT Library Catalog

## Purpose

This document summarizes the internal public-domain library currently bundled with FeelIT for reading and companion-audio experiments.

## Design Rule

The internal library exists to make the Braille Reader immediately demonstrable without relying on ad hoc pasted text or remote network access during a session.

The same internal assets now also seed the bundled demo `haptic_workspace` used by Haptic Desktop, and the demo workspace mirrors the full bundled catalog instead of a partial subset. This keeps the desktop launcher and paginated galleries aligned with the real internal library during first-run validation.

The current loading strategy is intentionally segmented:

- full source documents are preserved in the repository
- the Braille Reader loads bounded character segments into the tactile world
- segment sizing is user-adjustable so the 3D reading scene stays coherent

## Supported Document Formats

- `txt`
- `html`
- `epub`

Tracked follow-up compatibility work lives in GitHub issue `#14`.

## Current Document Shelf

| Title | Author | Format | Braille Reader Role |
|---|---|---|---|
| Alice's Adventures in Wonderland | Lewis Carroll | `txt` | narrative sample with paired audio chapters |
| Pride and Prejudice | Jane Austen | `txt` | long-form prose for segmented reading |
| Pride and Prejudice (EPUB) | Jane Austen | `epub` | ebook-format compatibility baseline |
| The Raven | Edgar Allan Poe | `html` | short marked-up poem for HTML extraction |
| Feeding the Mind | Lewis Carroll | `txt` | short essay for quick scene iteration |

## Current Audio Shelf

| Title | Source | Role |
|---|---|---|
| Alice's Adventures in Wonderland, Chapter 1 | Project Gutenberg Audio / LibriVox | paired audio sample |
| Alice's Adventures in Wonderland, Chapter 2 | Project Gutenberg Audio / LibriVox | paired audio continuation |
| The Raven | Internet Archive / LibriVox | poem-length companion audio |
| A Visit from St. Nicholas | Internet Archive / LibriVox | extra public-domain audio coverage |

## Per-File Asset Constraint

Every bundled document, audio file, and 3D demo asset must remain below `60 MB` per individual file so the repository stays GitHub-friendly and packaging remains tractable.

This constraint is enforced by automated tests in `tests/test_library_assets.py`.
