# OpenVAT – Vertex Animation Toolkit for Blender

**Author:** Luke Stilson  
**Version:** 1.0.4
**Blender Compatibility:** 4.2.0+  (4.4 recommended)

Documentation needs update to 1.0.4 - visit openvat.org for more information on the new encoding options for 1.0.4 and detailed technical overview. 

For Experimental examples of fluid simulation encoding, check out this video walking through 2 methods available in the experimental fluid simulation encoding template
## OverviewFluid Simulation via Vertex Animation Textures (OpenVAT)
https://youtu.be/xoLxKinzBwI

**OpenVAT** is a Blender add-on that encodes Vertex Animation Textures (VATs) directly from animated geometry. Designed for real-time engine export (Unity, Unreal, Godot), it supports:
- Frame-based geometry capture via Geometry Nodes.
- Packed or separate normal texture output.
- Arbitrary attribute encoding (RGB vector + optional scalar).
- High-quality PNG or EXR export.
- Auto-setup preview scene and cleanup.
- Verified extension on the Blender Extensions platform.

Curious to know more about VATS in general and this add-on was created? Check out my overview video:
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
- **Packed:** Normals packed into same texture (RGBA).
- **Separate:** Normals stored in a secondary texture.

### Transform Handling
- Encode relative to object space or world space.

### Output
- **Mesh Formats:** FBX, glTF (.glb or .gltf).
- **Texture Formats:** 16-bit PNG or EXR (half-float).
- **Includes:** UV mapping for VAT, optional mesh cleanup, optional proxy export.

## Interface Breakdown

### Encoding Panel (OpenVAT Encoding)
- Select encode target: `Active Object` or `Collection (combined)`
- Choose encoding mode: `OpenVAT Standard` or `Custom`
- Define Proxy Method: `Start Frame`, `Current Frame`, or `Selected Object`
- Normal Encoding, Attribute names (if custom), and Remap options

### Output Panel
- Set output directory
- Choose image + mesh formats
- View estimated resolution and vertex counts
- Execute encoding

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
    ├── MyObject.png             ← position+optional normal data
    ├── MyObject-vnrm.png        ← (if separate normals)
    ├── MyObject-remap_info.json← min/max metadata
    └── MyObject.fbx/.glb/...    ← encoded proxy mesh
```

## Previewing
Immediately after VAT creation, a new object will be added to the scene as a copy of the proxy object with all modifiers stripped and the decoder modifier added. This will be added in the exact location as the active_object and is unselected by default. Hide or move the original and scrub the timeline or play the scene to see the vertex-encoded animation play.

## Example Use Cases

- Bake **geometry node animations** to textures for engine playback.
- Export **destruction simulations** without heavy Alembic caches.
- Drive **shader-based VFX** with procedural or dynamic meshes.

## Developer & Export Notes

- Blender coordinate system: `-Z Forward, Y Up`
- EXR exports: 16-bit ZIP compression, no dithering
- PNG exports: 16-bit RGBA, best compatibility
- VAT Preview scene: auto-created and linked to “OpenVATPreview” collection
- Scene cleanup: automatic post-encoding

** Using tangent-space normal maps on VAT-animated meshes can be tricky. In most cases, it is recommended to use an object-space baked normal map for surface detail, and comine this with the animated VAT normal for proper surface lighting during deformation. This requires alteration to the default provided shaders.

### Engine Support

🔒 Licensing Note: Engine Integration Examples

The core OpenVAT tool is licensed under GPL-3.0. However, the contents of the `OpenVAT-Engine_Tools` sub-folder
(including Unity, Unreal, Godot, and EffectHouse integrations) are provided under a separate permissive MIT license. 
These examples are provided are intended to provide clarity and education- to help users implement OpenVAT output in proprietary engines, but should not fall under GPL - so they can safely be used directly in production if necessary.

## Unity

- **Adding the Unity Package**
  - In Unity's package manager, click "Add from Git URL" and paste https://github.com/sharpen3d/openvat-unity.git. This installs OpenVat into Packages of your project, including a custom window for automatic standard setup for basic and PBR usage.
    1. After package is sucessfully installed, Find the custom panel under "Tools > OpenVAT"
    2. Import the entire folder that was created when exporting your VAT via the OpenVAT blender Extension *including the json sidecar data*. 
    3. Point the Folder Path variable to the location of this folder within your Assets (will be something like Assets/myObject - always starting with "Assets/")
    4. **Optional:** Add standard PBR maps (if available) for your content - Basecolor, Roughness, Metalness, Normal, Emission, Ambient Occlusion *make sure to name maps approprately, see note below*
    5. Press Process OpenVAT Content - Results in Prefab and Material being created in the same folder, with an automatically looping animation (at default speed) of your content
    6. Modify the base shaders and shader parameters for your use case - add surface texturing, set start/end frames, or set animated = false to define your specific desired frame via animation or scripting.

## Unreal 5

*forward rendering only, I am working on a custom vertex factory for a modern approach to handling VATs in Unreal, along with specific VAT creation options to better utilize VAT in Niagara systems. Currently OpenVAT works in Unreal 5 without forward rendering enabled, however this can lead to undesired lighting issues on the VAT when using lit materials.

Watch the walkthrough:
https://www.youtube.com/watch?v=T1KVvUIduGI

Download the zip from Engine_Tools/Unreal5 extract, then drop into the Content of your Unreal project (in system file explorer, not directly into engine UI)
Tutorials and best-practices coming soon, getting all of this recorded. But in the meantime, drop these into a project and try it out!

Your project must have forward rendering enabled  (currently)
When you import your own vertex animation texture, make sure it's compression is set to RGB16
Split your mesh on any hard edges before baking (I will be integrating tools to help with this process), this allows soft and hard edges during vertex sampling.
This was built in UE5, and is NOT UE4 compatible at the moment.

