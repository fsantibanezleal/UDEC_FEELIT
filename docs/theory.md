# FeelIT Theory

## Scope

This document summarizes the theoretical concepts that inform the current FeelIT design decisions.

## 1. Tactile Accessibility Context

FeelIT is built around the idea that digital content can be represented as a structured tactile scene. In the legacy project, this meant Braille content laid out on a bounded virtual surface. In the modern project, the same principle extends to:

- Braille text
- 3D object shape
- material cues
- interactive controls inside a tactile workspace

## 2. Braille As A Structured Spatial Language

Braille cells use six dots arranged as two columns by three rows:

```text
1 4
2 5
3 6
```

The current runtime represents each character as:

- a six-bit mask
- a six-boolean dot array
- a Unicode Braille character
- a logical row and column position in the preview layout

This is only the logical layer. The current modern frontend already maps these cells into virtual tactile geometry for visual inspection, while the future hardware layer will map the same structure into real force-feedback behavior.

## 3. Workspace-Bounded Tactile Layout

The preserved legacy implementation used a base region plus raised Braille elements. This is important because tactile interaction benefits from a stable reference surface rather than isolated floating targets.

Inference from the legacy code and current literature:

- tactile interaction should happen inside a bounded workspace
- navigation controls should be embedded as stable reference objects
- the user should be able to infer orientation and limits through consistent scene geometry

## 4. Haptic Device Abstraction

Modern haptic ecosystems remain vendor-specific. Official toolchains such as OpenHaptics and Force Dimension SDKs expose different native APIs and capabilities.

Therefore FeelIT uses a device abstraction boundary:

- core logic must not depend on one hardware API
- the application must remain useful without hardware
- backend implementations can be swapped without rewriting the frontend or domain services

## 5. Multimodal Accessibility

Recent research indicates that non-visual interaction is stronger when haptics and audio are combined. This does not mean FeelIT should become audio-first. Instead:

- haptics carries spatial and material structure
- audio can carry labels, confirmations, or guidance

The modern architecture should therefore remain audio-ready even before audio is fully implemented.

## 6. Shape And Texture Representation

For the 3D object explorer, object understanding depends on more than shape alone. Current research signals that tactile interpretation improves when geometry and material cues are intentionally designed together.

FeelIT therefore models and will keep refining:

- geometry
- scale
- tactile material parameters
- optional semantic description

## 7. Material Approximation Limits

Current desktop haptic devices are much better at approximating:

- stiffness differences
- friction differences
- damping differences
- periodic texture or vibration cues

They are weaker at reproducing:

- deep bulk deformation
- rich distributed surface compliance
- large-area multi-point touch

This is why FeelIT uses material profiles as controlled approximations rather than claiming a fully faithful simulation of foam, sponge, cloth, or similar materials.

## 8. Visual Scene As A Haptic Mirror

For FeelIT, the rendered 3D world is not decorative. It is an explanatory mirror of the tactile world that the application is trying to create.

This matters because:

- developers need to inspect scene boundaries, relief height, object placement, and scale
- researchers need a visible representation of what the haptic workspace is attempting to encode
- the application must remain usable in no-device mode

Auxiliary 2D boards may help debugging or teaching, but they are secondary to the spatial scene.

## 9. Braille Translation Layer Versus Scene Layer

The current runtime intentionally separates two concerns:

### Logical translation layer

- text normalization
- character mapping
- dot masks
- row and column placement

### Scene realization layer

- 3D layout
- physical scale
- collision shapes
- force response
- navigation widgets

This separation makes the system easier to test and easier to adapt to new devices.
