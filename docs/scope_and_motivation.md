# FeelIT Scope And Motivation

## Origin

FeelIT originates from an accessibility project conceived to help people with visual impairment interact with information that is normally delivered as visual shape, texture, or spatial arrangement.

The original university-era effort explored digital-to-Braille conversion and optional haptic interaction. The modern rebuild expands that idea into a broader interaction platform while remaining honest about what the preserved legacy actually confirms.

## Core Motivation

Many relevant objects are inaccessible through direct touch:

- landmarks that are physically distant
- animals or artifacts that cannot be safely manipulated
- terrains, mountains, and large-scale forms
- textures or material cues that are not available in the immediate environment
- text or desktop content that should remain accessible without monopolizing the audio channel

FeelIT exists to convert those inaccessible visual domains into structured tactile interaction spaces.

## Foundational Idea

The project assumes that a bounded haptic workspace can represent more than force feedback alone. It can act as a tactile scene where the user:

- explores 3D shape
- senses material cues
- reads Braille content
- activates virtual objects that stand in for desktop actions

The haptic device is therefore not treated as a game controller. It is treated as an access instrument.

## Base Concepts

### Tactile Scene

A bounded virtual surface where objects exist as structured targets for exploration, reading, or activation.

### Haptic Pointer

The device-controlled point that moves through the scene and becomes the main means of contact with virtual objects.

### Material Profile

A simplified representation of qualities such as smoothness, roughness, rigidity, metallic hardness, or softness that can later be expressed through haptic force behavior.

### Braille Surface

A constrained reading plane where Braille cells are arranged with enough spatial coherence to support tactile scanning.

### Haptic Desktop Object

A virtual item such as a folder, document, button, or launcher represented as a touchable object with an associated label and action.

### Scene-Native Control

A control that exists inside the 3D tactile world itself rather than as a conventional web button. This is a core accessibility requirement when the blind user is expected to operate the experience through the haptic device alone.

## Scope Of The Modern Application

The modern FeelIT scope is organized into three major workspaces.

### 1. 3D Object Explorer

Purpose:

- load or stage 3D objects
- scale them to a bounded exploration space
- assign tactile material profiles
- support guided exploration of shape and contour

### 2. Braille Reader

Purpose:

- ingest text content
- map it into Braille cells
- place those cells on a bounded tactile reading surface
- allow the user to read without depending exclusively on audio output

### 3. Haptic Desktop

Purpose:

- represent digital actions as tactile objects
- provide labeled interaction targets for folders, media, settings, and tools
- support future audio-assisted but not audio-dependent desktop interaction

## Accessibility Position

FeelIT is not designed around the assumption that audio alone is enough. Audio can complement the experience, but the project goal is to preserve tactile agency.

That is especially important for:

- Braille users who want tactile reading rather than passive listening
- users who already depend on audio for other tasks
- scenarios where shape and texture matter as much as verbal description

## Hardware Position

The modern implementation must remain usable even when no haptic device is attached.

That means:

- visual fallback execution is required
- hardware integration must be isolated behind a backend abstraction
- the application should never fail entirely just because the physical device is absent

## Scope Boundaries For The Current Baseline

The current baseline already delivers:

- a shared backend and frontend application spine
- dedicated pages for the three major workspaces
- a working Braille translation workflow
- a bundled internal library of public-domain documents and companion audio samples
- first-format document ingestion for TXT, HTML, and EPUB sources
- real 3D workspace rendering for object, Braille, and desktop modes
- stylus-style pointer emulation for no-device execution
- scene-native tactile controls inside the Braille reading world
- bundled OBJ demo models and local OBJ staging
- initial haptic material profiles grounded in current desktop-haptics capabilities
- a null backend strategy for hardware-safe execution

The current baseline does not yet deliver:

- physical haptic bridge integration
- full desktop action execution model
- full-document compatibility beyond the current TXT, HTML, and EPUB baseline
- scene-native library selection for blind-first document session launch
- force-feedback realization of the material profiles

## Success Criteria

The project is moving in the right direction when:

- each major interaction goal has a dedicated, coherent workspace
- tactile reading is operational and reliable
- 3D object exploration can be staged inside bounded space even without a device
- hardware support can be added without rewriting the whole application
- documentation preserves the motivation and methodological intent behind the project
