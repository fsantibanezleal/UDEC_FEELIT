# FeelIT Material Profiles

## Purpose

FeelIT uses haptic material profiles as controlled approximations of how current desktop haptic systems can differentiate surfaces.

These profiles are not claims of perfect material simulation. They are pragmatic combinations of stiffness, damping, friction, and texture cues that map better to current device capabilities.

## Current Catalog

### Polished Metal

- high stiffness
- low damping
- low friction
- very small texture amplitude
- strong fit for rigid smooth surfaces

### Carved Stone

- very high stiffness
- moderate damping
- higher friction
- coarse texture spacing
- useful for relief-rich sculptures and rock-like surfaces

### Unfinished Wood

- medium-high stiffness
- moderate friction
- grain-like texture assumption
- good for organic branching models and carved forms

### Rubber Pad

- moderate stiffness
- high damping
- high friction
- good approximation for grippy compliant surfaces

### Foam Block

- low stiffness
- heavy damping
- muted texture
- represents softness only approximately, not full bulk deformation

### Textured Polymer

- medium stiffness
- crisp microtexture
- stable friction profile
- useful for engineered surfaces and generic demo figures

### Coated Paper

- light stiffness
- subtle drag
- very shallow surface grain
- useful for books, document stacks, and Braille-adjacent reading props

### Glazed Ceramic

- rigid smooth response
- low texture amplitude
- cleaner drag profile than stone
- useful for vessels and other polished household objects

## Parameter Families

Each profile currently exposes:

- `stiffness_n_per_mm`
- `damping`
- `static_friction`
- `dynamic_friction`
- `texture_amplitude_mm`
- `texture_spacing_mm`
- `vibration_hz`
- `viscosity`
- visual rendering hints for color, roughness, and metalness

## Design Rule

Material profiles should remain physically honest about the capabilities of desktop haptics:

- rigid contact and friction contrast are usually easier to approximate
- periodic microtexture is often representable
- deep softness and distributed contact remain limited

Future hardware integrations should map these profiles into device-specific force and texture behavior without changing the higher-level project vocabulary.
