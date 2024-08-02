# OpenVAT VAT Encoder for Blender

The ZIP in this main repo openvat.zip is always the latest Blender Addon - simply download the raw file.
Other files in this repo are associated work, templates and shaders.

The OpenVAT VAT Encoder for Blender interface consists of a tool present in the 3D Viewport - Category "OpenVAT".

## Encoding

The tool presents a "VAT Calculator" panel in the OpenVAT category in the 3D Viewport, featuring information, options, and an operator to run the tool.

### Panel Labels

Labels in the panel preemptively define to the user information which will result in VAT creation.

- **Active Object:** 
  - Shows the name of the current active object, whose deformation will be recorded to VAT information.
- **Vertex Count, Frame Range:**
  - Vertex count of the Active Object, frame range (as defined in your scene's Output Properties).
- **Output Resolution:**
  - The calculated resolution of the resulting VAT, determined by the smallest ^2 that can account for frame range * number of vertices. It is recommended not to exceed an output resolution above 4096x4096.

### Panel Options

User-defined properties that affect the output or output process.

- **Output Directory:**
  - The absolute path on disk where resulting content will be exported.
- **Vertex Normals:**
  - Export the resulting vertex normal VAT information (currently as a separate PNG export). This can be helpful in the engine to correct reflection and rendering on manipulated/deforming animated objects, but is not always necessary.
- **Debug Mode:**
  - When creating the VAT with Debug Mode enabled, the script 'shows its work' by keeping all temporary scene, object, and compositing construction (which is hidden and removed by default). Debug mode will keep 2 Scenes (active-object-name_vat - referred to as "VAT Tracker Scene", and active-object-name_proxy_scene - referred to as "VAT Proxy Scene"). If "Use Custom Proxy" is False, it also keeps the temporary VAT Basis (automatic proxy created from frame 1).

### Panel Operators

The main VAT creation operations, currently this is a blanket single operator "Create VAT" - which runs the creation and export process with settings defined in the panel.

- **Create VAT:**
  - This operator runs a large process consisting of multiple automatic processes and cleanup.
    1. The Active Object and Custom Proxy (or frame 1 of the Active Object if proxy is not defined) are compared over the frame range to calculate the largest difference in X, Y, and Z of each vertex over the duration of the animation. A simple Geometry Node setup passing Position into "colPos" property exposes this vertex data from the dependency graph.
    2. Min/Max Values are defined as float properties for each channel X, Y, Z based on the calculation above. These values are stored in `bpy.context.current_scene` properties (the scene the operation was run from). New properties are created if they do not exist (`x_min`, `x_max`, `y_min`, `y_max`, `z_min`, `z_max`).
    3. JSON sidecar data is created containing the Min/Max values for Game Engine Shader handling.
    4. Proxy Object is copied into a "Proxy Scene" named active-object + "proxy_scene" - to be safely referenced in the VAT Tracker geometry nodes in the next step. VAT_UV (new UV layer) is calculated and appended to the proxy object, ordering vertices to become functional with the resulting VAT.
    5. VAT Tracker scene and VAT tracker are created. Another new scene is added, named active-object + "_vat". A camera is added to this scene, render properties and resolution are set. The VAT Tracker is created by appending a geometry node dependency contained within the extension to a new plane in the scene. Settings on this Geometry Node group are set in order to capture the relative object-space vertex positional data difference between the active-object and proxy. A single frame of this scene is rendered temporarily to the export location (named active-object-name + "_vat").
    6. Compositing Nodes are set up and enabled in the VAT Tracker scene. The rendered image is loaded back into Blender as an image in the compositor, z-layered with the scene output from the VAT Tracker scene.
    7. VAT Rendering - each frame as defined in the frame range is rendered through the compositor as an overlay (in raw space) of the previous frame. Each render accounts for all verts relative position on a single frame. The result is a vertex-over-time per pixel representation of animation.
    8. Automatic Preview - the resulting VAT is set up on the proxy object via geometry node group `ov_vat_decoder_vs` and is copied back into the original scene.
    9. Cleanup - if Debug is False, cleans up the appended and added content, leaving only the resulting VAT preview and removing the background work (scenes and objects) created.

## Previewing

Immediately after VAT creation, a new object will be added to the scene as a copy of the proxy object with all modifiers stripped and the decoder modifier added. This will be added in the exact location as the active_object and is unselected by default. Hide or move the original and scrub the timeline or play the scene to see the vertex-encoded animation play.

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
  
  
