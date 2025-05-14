# OpenVAT VAT Encoder for Blender

The ZIP in this main repo openvat.zip is always the latest Blender Addon - simply download the raw file.
Other files in this repo are associated work, templates and shaders.

The OpenVAT VAT Encoder for Blender interface consists of a tool present in the 3D Viewport - Category "OpenVAT".

# OpenVAT – Vertex Animation Toolkit for Blender

**Author:** Luke Stilson  
**Version:** 1.0.3a  
**License:** GPL-2.0-or-later  
**Blender Compatibility:** 4.2.0+  
**Website:** [https://github.com/sharpen3d/openvat](https://github.com/sharpen3d/openvat)

## Overview

**OpenVAT** is a Blender add-on that encodes Vertex Animation Textures (VATs) directly from animated geometry. Designed for real-time engine export (Unity, Unreal, Godot), it supports:
- Frame-based geometry capture via Geometry Nodes.
- Packed or separate normal texture output.
- Arbitrary attribute encoding (RGB vector + optional scalar).
- High-quality PNG or EXR export.
- Auto-setup preview scene and cleanup.
- Verified extension on the Blender Extensions platform.

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

### Engine Support
  - Unity Engine URP support and examples for OpenVat exist, but need documentation and walk-throughs.

- **Adding the Unity Package**
  - In Unity's package manager, click "Add from Git URL" and paste https://github.com/sharpen3d/openvat-unity.git. This installs OpenVat into Packages of your project, including a custom window for automatic standard setup for basic and PBR usage.
    1. After package is sucessfully installed, Find the custom panel under "Tools > OpenVAT"
    2. Import the entire folder that was created when exporting your VAT via the OpenVAT blender Extension *including the json sidecar data*. 
    3. Point the Folder Path variable to the location of this folder within your Assets (will be something like Assets/myObject - always starting with "Assets/")
    4. **Optional:** Add standard PBR maps (if available) for your content - Basecolor, Roughness, Metalness, Normal, Emission, Ambient Occlusion *make sure to name maps approprately, see note below*
    5. Press Process OpenVAT Content - Results in Prefab and Material being created in the same folder, with an automatically looping animation (at default speed) of your content

**PBR NAMING**
  - If PBR maps are included, use recognized PBR naming to let the script automatically apply these textures to your model
  - These need to be in the same folder as the VAT content (the folder named your object name)
  - PBR textures can always be added to the openVAT_decoder shader. If no PBR maps are found in your object folder, openVAT_decoder_basic shader is used (solid color) - to add maps, swap the shader to openVAT_decoder, then you can manually place maps in any of the slots

Recognized naming conventions:
basecolor = "_basecolor", "_albedo"
normal = "_nrml", "_normal"
roughness = "_roug", "_roughness"
metallic = "_metl", "_metallic"
ambient occlusion = "_ao", "_ambient", "_occlusion"
emission = "_emis", "_emission"

- **Notes**
  - Vertex Normals (VNRM) are in an Experimental/Testing phase for unity and **may not work** at this time, these are disabled in the standard openVAT_decoder_basic, but are enabled in the PBR-accepting openVAT_decoder for testing purposes. Leaving VNRM blank in your material will have no adverse consequences.
  
  
