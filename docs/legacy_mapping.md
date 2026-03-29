# FeelIT Legacy Mapping

## Why This Document Exists

The preserved FeelIT archive is valuable, but it does not justify claiming that every modern target feature was already implemented in the original codebase. This document separates:

- what is verified from preserved evidence
- what is a modernization target

## Verified Legacy Behavior

### Confirmed

- text-file loading
- character-by-character Braille conversion
- OpenGL visual rendering of Braille cells
- optional haptic interaction through a legacy device stack
- no-device execution mode

### Not Verified As Implemented In The Preserved Code

- finished 3D object explorer for arbitrary models
- finished haptic desktop for folders and digital actions
- modern document-format ingestion

## Legacy To Modern Mapping

| Legacy Evidence | Modern Equivalent |
|---|---|
| Braille text mode | Modern Braille Reader mode |
| Haptic base plane plus raised Braille nodes | Bounded tactile workspace with semantic geometry |
| Device-specific `hdl.dll` integration | Pluggable backend abstraction |
| Windows Forms + OpenGL | FastAPI + web frontend + future native haptic bridge |
| Character-by-character navigation | Pagination, scene controls, and richer reading workflows |

## Design Rule

The modern repository treats the Braille reader as inherited scope and the other two major modes as deliberate modernization expansion.

