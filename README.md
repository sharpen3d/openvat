# OpenVAT – Vertex Animation Toolkit for Blender

**Author:** Luke Stilson  
**Version:** 1.1.2  
**Blender Compatibility:** 4.2.0+ and 5.x (backwards compatible). Please report any issues with 5.x, or issues with previous versions that may arise from these updates.  
**Versions:** Check Development/Builds folder for previous stable builds

## New in 1.1.2
- Fixed encoding failing with `'Scene' object has no attribute 'vat_anim_data'` in 1.1.1. The Animation Data panel (below) is restored.

## New in 1.1.1
- Blender 5.x compatibility for Geometry Nodes modifier inputs and the compositor.

## New in 1.1.0
### Animation Data Panel

A new **Animation Data** panel has been added.

- Allows you to define **animation metadata** that is written into the exported JSON (`-remap_info.json`, under `animations`):
  - Per-animation **name**
  - **Frame ranges** (start/end frames)
  - **Framerate**
  - **Loop / non-loop** designation
- This metadata is **used only by the Unity import pipeline** for now.
- This system is designed to let you carve multiple logical clips (idle, run, attack, etc.) out of a single VAT bake.

> ⚠️ Important behavior notes  
> - **Does not affect encoding**: The animation definitions do **not** change which frames are baked. The full encoding range is still exported.  
> - **No skipping**: Defining animations does **not** “skip” frames in the bake or change how the VAT is generated; it only tags ranges inside the encoded data.  
> - **Global frame ranges**: Animation frame ranges are currently **global** scene frames, *not* relative to the VAT encoding start frame.
> - **Standard mode only**: Panel entries are written for Standard (Position/Normal) encoding. Custom Attribute encoding writes a single full-range entry instead.
> - Only the **Unity** importer currently reads and uses this metadata.
- **Compositor**
  - The new compositor API in Blender 5.0 is still evolving; future Blender releases may require minor adjustments, but the current helper-based approach is designed to minimize breakage.

## Experimental / Advanced Features
For Experimental examples of fluid simulation encoding, check out this video walking through 2 methods available in the experimental fluid simulation encoding template (`Experimental/fluid_simulation_template.blend`):

**Fluid Simulation via Vertex Animation Textures (OpenVAT)**  
https://youtu.be/xoLxKinzBwI

## Overview

**OpenVAT** is a Blender add-on that encodes Vertex Animation Textures (VATs) directly from animated geometry. Designed for real-time engine export (Unity, Unreal, Godot), it supports:
- Frame-based geometry capture via Geometry Nodes.
- Packed or separate normal texture output.
- Custom attribute encoding (up to three float point attributes into R, G, B).
- High-quality PNG or EXR export.
- Auto-setup preview scene and cleanup.
- Verified extension on the Blender Extensions platform.

Curious to know more about VATs in general and how this add-on was created? Check out my overview video:
https://www.youtube.com/watch?v=eTBuDbZxwFg

OpenVAT targets technical artists, shader developers, and studios aiming to bridge Blender simulations, procedural animation, or geometry nodes with performant in-engine playback.

## Key Concepts

- **VAT (Vertex Animation Texture):** A texture where pixel data stores vertex positions (and optionally normals) per frame.
- **Proxy Object:** The "bind pose" reference used as a base for calculating deltas.
- **Remap Info:** JSON metadata storing min/max per channel for accurate reconstruction.
- **Packed Normals:** Normals encoded into the same texture as position (saves memory but limits angular precision).

## Features

### Normal Handling
- **None:** No normal data.
- **Packed:** Normals stored in the same texture as position, as additional rows (doubles texture height).
- **Separate:** Normals stored in a secondary texture.

### Transform Handling
- Encode relative to object space or world space.

### Output
- **Mesh Formats:** FBX, glTF (.glb or .gltf).
- **Texture Formats:** PNG (8 or 16-bit) or OpenEXR (16-bit half or 32-bit full float).
- **Includes:** UV mapping for VAT, optional mesh cleanup, optional proxy export.

## Interface Breakdown

### Encoding Panel (OpenVAT Encoding)
- Select encode target: `Active Object` or `Collection (combined)`
- Choose encoding mode: `Standard (Position/Normal)` or `Custom Attributes (float[3])`
- Define Proxy Method (Deformation Basis): `Start Frame`, `Current Frame`, or `Selected Object`
- Transform space (`Object` or `World`), Normal Encoding, or scanned attribute names (if custom)
- Mesh settings: Strip Vertex Data, Create Normal-Safe Edges

### Output Panel
- Set output directory
- Choose image + mesh formats, Single Row mode, and absolute values (EXR32 only)
- View estimated resolution and vertex counts
- Execute encoding

### Animation Data Panel
- Add/remove named clips with start/end frames, framerate, and looping (see **New in 1.1.0** above)

## Encoding Workflow

1. **Install Add-on** via Preferences.
2. **Select Target:**
   - Mesh or Collection.
   - Choose encoding type.
3. **Configure Settings:**
   - Frame range
   - Attribute remapping
   - Normal packing, cleanup, transform
4. **Set Output Directory**
   - Choose image and mesh output formats
5. **Click “Encode Vertex Animation Texture”**

## File Output

Given target `MyObject`, results are stored like:

```
/MyExportDir/
└── MyObject_vat/
    ├── MyObject_vat.png          ← position + optional packed normal data
    ├── MyObject_vnrm.png         ← (if separate normals)
    ├── MyObject-remap_info.json  ← min/max + animation metadata
    └── MyObject.fbx/.glb/...     ← encoded proxy mesh
```
(`.exr` instead of `.png` when an EXR image format is selected.)

## Previewing
Immediately after VAT creation, a new object (`MyObject_vat`) will be added to the `OpenVATPreview` collection as a copy of the proxy object with all modifiers stripped and the decoder modifier added. It is selected and active when encoding finishes. With Transform set to `World` it lines up with the original; with `Object` it sits at the world origin. Hide or move the original and scrub the timeline or play the scene to see the vertex-encoded animation play.

## Example Use Cases

- Bake **geometry node animations** to textures for engine playback.
- Export **destruction simulations** without heavy Alembic caches.
- Drive **shader-based VFX** with procedural or dynamic meshes.

## Developer & Export Notes

- Blender coordinate system: `-Z Forward, Y Up`
- EXR exports: EXR16 is half-float with ZIP compression, EXR32 is full float uncompressed; no dithering
- PNG exports: 8 or 16-bit RGB, best compatibility
- VAT Preview scene: auto-created and linked to “OpenVATPreview” collection
- Scene cleanup: automatic post-encoding

** Using tangent-space normal maps on VAT-animated meshes can be tricky. In most cases, it is recommended to use an object-space baked normal map for surface detail, and combine this with the animated VAT normal for proper surface lighting during deformation. This requires alteration to the default provided shaders.

### Engine Support

🔒 Licensing Note: Engine Integration Examples

The core OpenVAT tool is licensed under GPL-3.0. However, the contents of the `OpenVAT-Engine_Tools` sub-folder
(including Unity, Unreal, Godot, and EffectHouse integrations) are provided under a separate permissive MIT license. 
These examples are intended to provide clarity and education- to help users implement OpenVAT output in proprietary engines, but should not fall under GPL - so they can safely be used directly in production if necessary.

## Unity

- **Adding the Unity Package**
  - In Unity's package manager, click "Add from Git URL" and paste https://github.com/sharpen3d/openvat-unity.git. This installs OpenVat into Packages of your project, including a custom window for automatic standard setup for basic and PBR usage.
    1. After package is successfully installed, Find the custom panel under "Tools > OpenVAT"
    2. Import the entire folder that was created when exporting your VAT via the OpenVAT blender Extension *including the json sidecar data*. 
    3. Point the Folder Path variable to the location of this folder within your Assets (will be something like Assets/myObject - always starting with "Assets/")
    4. **Optional:** Add standard PBR maps (if available) for your content - Basecolor, Roughness, Metalness, Normal, Emission, Ambient Occlusion *make sure to name maps appropriately, see note below*
    5. Press Process OpenVAT Content - Results in Prefab and Material being created in the same folder, with an automatically looping animation (at default speed) of your content
    6. Modify the base shaders and shader parameters for your use case - add surface texturing, set start/end frames, or set animated = false to define your specific desired frame via animation or scripting.

## Unreal 5

*forward rendering only, I am working on a custom vertex factory for a modern approach to handling VATs in Unreal, along with specific VAT creation options to better utilize VAT in Niagara systems. Currently OpenVAT works in Unreal 5 without forward rendering enabled, however this can lead to undesired lighting issues on the VAT when using lit materials.

Watch the walkthrough:
https://www.youtube.com/watch?v=T1KVvUIduGI

Download the zip from OpenVAT-Engine_Tools/Unreal5 extract, then drop into the Content of your Unreal project (in system file explorer, not directly into engine UI)
Tutorials and best-practices coming soon, getting all of this recorded. But in the meantime, drop these into a project and try it out!

Your project must have forward rendering enabled  (currently)
When you import your own vertex animation texture, make sure its compression is set to RGB16
Split your mesh on any hard edges before baking (or enable **Create Normal-Safe Edges** in OpenVAT's mesh settings), this allows soft and hard edges during vertex sampling.
This was built in UE5, and is NOT UE4 compatible at the moment.

