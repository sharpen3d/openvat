# OpenVAT core functions

import bpy
import bmesh
import os
from . import utils

# Create VAT UV map with bmesh
def create_uv_map(obj, screen_width, screen_height, frames):
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.new("VAT_UV")
    index_layer = bm.verts.layers.int.new("index_orig")

    for i, vert in enumerate(bm.verts):
        vert[index_layer] = i

    sorted_verts = sorted(bm.verts, key=lambda v: v[index_layer], reverse=True)
    num_verts = len(sorted_verts)
    pixel_size_x = 1.0 / screen_width
    pixel_size_y = 1.0 / screen_height

    for i, vert in enumerate(sorted_verts):
        uv_x = (i % screen_width) / screen_width + pixel_size_x / 2
        uv_y = 1.0 - ((i // screen_width) * frames) / screen_height - pixel_size_y / 2

        for loop in vert.link_loops:
            loop[uv_layer].uv = (uv_x, uv_y)

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.uv_layers.active_index = len(obj.data.uv_layers) - 1

# The bulk of the encoding computation happens within an appended geometry node group - The following code defines properties to set up the geometry nodes to capture data
def setup_vat_tracker(vat_scene, obj_name, num_frames, width, height, num_wraps, proxy_name, original_scene, nodegroup_method, pack_normals, use_custom, custom_attribute, custom_remap):
    bpy.ops.mesh.primitive_plane_add(location=(0, 5, 0))
    tracker_plane = bpy.context.object
    tracker_plane.name = f"{obj_name}_vat-tracking"
    
    bpy.ops.object.modifier_add(type='NODES')
    tracker_plane.modifiers["GeometryNodes"].node_group = bpy.data.node_groups[nodegroup_method]
    tracker_plane.modifiers["GeometryNodes"]["Socket_4"] = bpy.data.objects[obj_name]
    tracker_plane.modifiers["GeometryNodes"]["Socket_2"] = num_frames
    tracker_plane.modifiers["GeometryNodes"]["Socket_10"] = num_wraps
    tracker_plane.modifiers["GeometryNodes"]["Socket_8"] = width
    tracker_plane.modifiers["GeometryNodes"]["Socket_9"] = height
    tracker_plane.modifiers["GeometryNodes"]["Socket_11"] = bpy.data.objects[proxy_name]
    tracker_plane.modifiers["GeometryNodes"]["Socket_6"] = original_scene['min_x']
    tracker_plane.modifiers["GeometryNodes"]["Socket_7"] = original_scene['max_x']
    tracker_plane.modifiers["GeometryNodes"]["Socket_12"] = original_scene['min_y']
    tracker_plane.modifiers["GeometryNodes"]["Socket_13"] = original_scene['max_y']
    tracker_plane.modifiers["GeometryNodes"]["Socket_14"] = original_scene['min_z']
    tracker_plane.modifiers["GeometryNodes"]["Socket_15"] = original_scene['max_z']
    tracker_plane.modifiers["GeometryNodes"]["Socket_19"] = vat_scene.frame_start
    
    if use_custom:
        tracker_plane.modifiers["GeometryNodes"]["Socket_23"] = True
        tracker_plane.modifiers["GeometryNodes"]["Socket_20"] = custom_attribute
        if custom_remap:
            tracker_plane.modifiers["GeometryNodes"]["Socket_22"] = True
    else:
        if bpy.data.scenes[original_scene.name].vat_settings.vat_normal_encoding == 'PACKED':
            normal_tracker = tracker_plane.copy()
            normal_tracker.data = tracker_plane.data.copy()
            vat_scene.collection.objects.link(normal_tracker)
            normal_tracker.location[1] = 0
            normal_tracker.modifiers["GeometryNodes"]["Socket_17"] = True
        
        
def setup_proxy_scene(obj, num_frames, width, height, num_wraps, temp_obj, pack_normals, framestart):
    original_scene = bpy.context.scene
    settings = original_scene.vat_settings
    
    bpy.ops.scene.new(type='NEW')
    proxy_scene = bpy.context.scene
    proxy_scene.name = f"{obj.name}_proxy_scene"

    proxy_scene.frame_end = framestart + num_frames - 1
    
    if settings.proxy_method == 'START_FRAME':
        proxy_scene.frame_current = framestart
    proxy_scene.frame_start = framestart

    proxy_obj = temp_obj.copy()
    proxy_obj.data = temp_obj.data.copy()
    proxy_scene.collection.objects.link(proxy_obj)
    
    bpy.context.view_layer.objects.active = proxy_obj
    proxy_obj.select_set(True)

    for modifier in proxy_obj.modifiers[:]:
        utils.apply_modifier(proxy_obj, modifier)
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    bpy.ops.object.modifier_add(type='NODES')
    proxy_obj.modifiers[-1].node_group = bpy.data.node_groups["ov_generated-pos"]
    create_uv_map(proxy_obj, width, height, num_frames)
        
    # Main VAT render
    setup_vat_scene(proxy_obj, obj.name, original_scene.name, num_frames, width, height, num_wraps, pack_normals)
    
    # Get VAT Result
    image_result = bpy.data.images[obj.name.replace("_ovbake", "") + "_vat." + original_scene.vat_settings.image_format.lower()]
    
    
    bpy.context.window.scene = proxy_scene
    vat_obj = proxy_obj.copy()
    vat_obj.data = proxy_obj.data.copy()
    
    original_scene.collection.objects.link(vat_obj)
    bpy.context.window.scene = original_scene
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = vat_obj
    vat_obj.select_set(True)
    
    for modifier in vat_obj.modifiers[:]:
        vat_obj.modifiers.remove(modifier)
    bpy.ops.object.modifier_add(type='NODES')
    vat_obj.modifiers[-1].node_group = bpy.data.node_groups["ov_vat-decoder-vs"]
    
    vat_obj.modifiers["GeometryNodes"]["Socket_2_attribute_name"] = "VAT_UV"
    vat_obj.modifiers["GeometryNodes"]["Socket_6"] = num_frames
    vat_obj.modifiers["GeometryNodes"]["Socket_7"] = height
    vat_obj.modifiers["GeometryNodes"]["Socket_9"] = image_result
    vat_obj.modifiers["GeometryNodes"]["Socket_3"] = original_scene['min_x']
    vat_obj.modifiers["GeometryNodes"]["Socket_4"] = original_scene['max_x']
    vat_obj.modifiers["GeometryNodes"]["Socket_10"] = original_scene['min_y']
    vat_obj.modifiers["GeometryNodes"]["Socket_11"] = original_scene['max_y']
    vat_obj.modifiers["GeometryNodes"]["Socket_12"] = original_scene['min_z']
    vat_obj.modifiers["GeometryNodes"]["Socket_13"] = original_scene['max_z']
    vat_obj.modifiers["GeometryNodes"]["Socket_14"] = original_scene.frame_start

    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    vat_obj.name = obj.name.replace("_ovbake", "_vat")
    
    # Move to OpenVATPreview collection
    vat_coll = bpy.data.collections.get("OpenVATPreview")
    if not vat_coll:
        vat_coll = bpy.data.collections.new("OpenVATPreview")
        #original_scene.collection.children.link(vat_coll)
    
    original_scene.collection.objects.unlink(vat_obj)
    vat_coll.objects.link(vat_obj)
    tempmain = vat_obj.name.replace("_vat", "_ovbake")
    bpy.ops.object.select_all(action='DESELECT')
    vat_obj.select_set(True)
    
    bpy.context.view_layer.objects.active = vat_obj
    if settings.clean_mesh:
        utils.clean_mesh_data(vat_obj)
    
    vat_obj.data.name=vat_obj.name.replace("_vat", "_mesh")
    bpy.data.objects.remove(obj)
    
    if settings.export_mesh:
        export_vat_model(settings.mesh_format, include_materials=False, include_tangents=True)


def setup_vat_scene(proxy_obj, obj_name, original_scene_name, num_frames, width, height, num_wraps, pack_normals):
    bpy.ops.scene.new(type='NEW')
    vat_scene = bpy.context.scene
    vat_scene.name = f"{obj_name}_vat"
    original_scene = bpy.data.scenes[original_scene_name]
    output_dir = bpy.path.abspath(original_scene.vat_settings.vat_output_directory)
    
    vat_scene.frame_start = bpy.data.scenes[original_scene_name].frame_start
    vat_scene.frame_end = bpy.data.scenes[original_scene_name].frame_end
    camera = bpy.data.cameras.new("Camera")
    camera_obj = bpy.data.objects.new("Camera", camera)
    vat_scene.collection.objects.link(camera_obj)
    vat_scene.camera = camera_obj
    camera_obj.location = (0, 0, 10)
    camera_obj.data.type = 'ORTHO'
    camera_obj.data.ortho_scale = 10
    
    vat_scene.render.resolution_x = width
    vat_scene.render.resolution_y = height
    vat_scene.display_settings.display_device = 'sRGB'
    vat_scene.view_settings.view_transform = 'Raw'
    vat_scene.render.film_transparent = True
    
    if original_scene.vat_settings.image_format == 'PNG':
        # Based on settings
        vat_scene.render.image_settings.file_format = 'PNG'
        vat_scene.render.image_settings.color_mode = 'RGBA'
    
    elif original_scene.vat_settings.image_format == 'EXR':
        vat_scene.render.image_settings.file_format = 'OPEN_EXR'
        vat_scene.render.image_settings.color_mode = 'RGBA'
        
    # Extension-Agnostic
    vat_scene.render.image_settings.color_depth = '16'
    vat_scene.render.image_settings.compression = 0
    vat_scene.render.dither_intensity = 0
    vat_scene.render.use_compositing = False
    vat_scene.render.use_sequencer = False
    vat_scene.eevee.taa_render_samples = 1
    
    image_format = '.' + original_scene.vat_settings.image_format.lower()
        
    original_scene = bpy.data.scenes[original_scene_name]
    os.makedirs(output_dir, exist_ok=True)
    render_vat_scene(vat_scene, 0, output_dir, image_format)
    vat_scene.render.use_compositing = True
    
    # Set compositing nodes in VAT scene
    setup_compositing(vat_scene, output_dir, vat_scene.name, proxy_obj, image_format)
    nodegroup_method = "ov_calculate-position-vs"
    
    encode_settings = original_scene.vat_settings
    use_custom = False
    custom_attribute = ""
    custom_remap = False
    if encode_settings.encode_type == 'CUSTOM':
        use_custom = True
        custom_attribute = encode_settings.user_attribute # Custom Vector
        custom_remap = encode_settings.custom_remap
        pack_normals = False
         
    setup_vat_tracker(vat_scene, obj_name, num_frames, width, height, num_wraps, proxy_obj.name, original_scene, nodegroup_method, pack_normals, use_custom, custom_attribute, custom_remap)
    print ("VAT Tracker Created")
    print ("Starting render process...")
    # Render VAT   
    render_vat_scene(vat_scene, num_frames, output_dir, image_format)
    if not pack_normals: 
        if bpy.data.scenes[original_scene_name].vat_settings.encode_type == 'DEFAULT':
            if bpy.data.scenes[original_scene_name].vat_settings.vat_normal_encoding != 'NONE':
                print ("Starting normals render process...")
                bpy.context.object.modifiers["GeometryNodes"]["Socket_17"] = True
                rendername = vat_scene.name.replace("_ovbake_vat", "_vnrm")
                vat_scene.render.use_compositing = False
            
                # Prep
                render_vat_nrml(vat_scene, 0, output_dir, image_format)
                vat_scene.render.use_compositing = True
                tree = vat_scene.node_tree
                image_node = tree.nodes["Image"]
                image = bpy.data.images.get(rendername + image_format)
                image_node.image = image
                image.colorspace_settings.name = 'Non-Color'
                
                #Render
                render_vat_nrml(vat_scene, num_frames, output_dir, image_format)   
    
# Set up compositing for the per frame capture overlay in the vat scene
def setup_compositing(vat_scene, output_dir, scene_name, proxy_obj, image_format):
    vat_scene.use_nodes = True
    tree = vat_scene.node_tree
    links = tree.links              
    for node in tree.nodes:
        tree.nodes.remove(node)
    render_layers_node = tree.nodes.new(type="CompositorNodeRLayers")
    image_node = tree.nodes.new(type="CompositorNodeImage")
    zcombine_node = tree.nodes.new(type="CompositorNodeZcombine")
    composite_node = tree.nodes.new(type="CompositorNodeComposite")
    links.new(render_layers_node.outputs[0], zcombine_node.inputs[2])
    links.new(image_node.outputs[0], zcombine_node.inputs[0])
    links.new(zcombine_node.outputs[0], composite_node.inputs[0])
    image = bpy.data.images.get(vat_scene.name.replace("_ovbake", "") + image_format)
    image_node.image = image
    image.colorspace_settings.name = 'Non-Color'
    zcombine_node.use_alpha = True
    zcombine_node.use_antialias_z = False
    print("VAT Compositing Nodes sucessfully set in " + str(vat_scene))

# Called to render temporary frames to first prime the compositor, then through sequence for vat and optionally vnrm    
def render_vat_scene(vat_scene, num_frames, output_dir, image_format):
    start_frame = vat_scene.frame_start
    end_frame = vat_scene.frame_start + num_frames
    output_name = vat_scene.name.replace("_ovbake", "")
    output_path = os.path.join(output_dir, f"{output_name}", f"{output_name}{image_format}")
    nrmoutput_path = os.path.join(output_dir, f"{output_name}", vat_scene.name.replace("_vat", "_vnrm") + image_format)
    if os.path.exists(output_path):
        bpy.data.images.remove(bpy.data.images.load(output_path))
    for frame in range(start_frame -1, end_frame):
        vat_scene.frame_set(frame)
        vat_scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.get(output_name + image_format)
        if img is not None:
            img.reload()
        else:
            img = bpy.data.images.load(output_path)
            print(f"Rendered template frame for compositing {frame}")
            
    vat_scene.render.image_settings.color_mode = 'RGB'
    img = bpy.data.images.load(output_path)
    if img is not None:
        img.reload()
        vat_scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        
        #Reset Color Mode
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
        
        ## If Custom Scalar...

    print(f"VAT Encoding finished, exported to {output_dir}")
    
# Similar to render_vat_scene above, but to a new texture name
def render_vat_nrml(vat_scene, num_frames, output_dir, image_format):
    start_frame = vat_scene.frame_start
    end_frame = vat_scene.frame_start + num_frames
    output_name = vat_scene.name.replace("_ovbake", "")
    rendername = output_name.replace("_vat", "_vnrm")
    output_path = os.path.join(output_dir, f"{output_name}", f"{rendername}{image_format}")
    if os.path.exists(output_path):
        bpy.data.images.remove(bpy.data.images.load(output_path)) 
    for frame in range(start_frame -1, end_frame):
        vat_scene.frame_set(frame)
        vat_scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.get(rendername + image_format)
        if img is not None:
            img.reload()
        else:
            img = bpy.data.images.load(output_path)
            print(f"Rendered template frame for normals compositing {frame}")
    
    vat_scene.render.image_settings.color_mode = 'RGB'
    img = bpy.data.images.load(output_path)
    if img is not None:
        img.reload()
        vat_scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        
        #Reset Color Mode
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
    print(f"VNRM Encoding finished, exported to {output_dir}")

# Export the selected object with default export settings for openVAT
def export_vat_model(file_format='FBX', include_materials=False, include_tangents=True):
    obj = bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        raise Exception("Active object must be a mesh")

    bpy.ops.mesh.customdata_custom_splitnormals_add()

    export_directory = bpy.path.abspath(bpy.context.scene.vat_settings.vat_output_directory)
    object_directory = os.path.join(export_directory, obj.name)
    os.makedirs(object_directory, exist_ok=True)

    export_name = obj.name.replace("_vat", "")
    export_ext = 'fbx' if file_format.upper() == 'FBX' else 'glb' if file_format.upper() == 'GLB' else 'gltf'
    export_path = os.path.join(object_directory, f"{export_name}.{export_ext}")

    if file_format.upper() == 'FBX':
        bpy.ops.export_scene.fbx(
            filepath=export_path,
            use_selection=True,
            use_active_collection=False,
            global_scale=1.0,
            apply_unit_scale=True,
            bake_space_transform=False,
            object_types={'MESH'},
            use_mesh_modifiers=False,
            use_mesh_modifiers_render=False,
            mesh_smooth_type='OFF',
            use_subsurf=False,
            use_mesh_edges=False,
            use_tspace=include_tangents,
            add_leaf_bones=False,
            bake_anim=False,
            path_mode='COPY' if include_materials else 'STRIP',
            embed_textures=include_materials
        )

    elif file_format.upper() in {'GLB', 'GLTF'}:
        bpy.ops.export_scene.gltf(
            filepath=export_path,
            export_format='GLB' if file_format.upper() == 'GLB' else 'GLTF_SEPARATE',
            use_selection=True,
            export_apply=True,
            export_texcoords=True,
            export_normals=True,
            export_tangents=include_tangents,
            export_materials='EXPORT' if include_materials else 'NONE',
            export_yup=True,
            export_cameras=False,
            export_lights=False,
            export_extras=False,
            will_save_settings=False
        )

    else:
        raise ValueError(f"Unsupported export format: {file_format}. Use 'FBX', 'GLB', or 'GLTF'.")

    print(f"Exported {obj.name} to {export_path} as {file_format.upper()}")


def create_geo_nodes_bake(use_collection=False, collection_name=""):
    context = bpy.context
    scene = context.scene
    vat_settings = scene.vat_settings
    
    active_obj = context.active_object
    if not use_collection:
        if not active_obj:
            raise RuntimeError("No active object selected")

    base_name = collection_name if use_collection else active_obj.name
    bake_name = f"{base_name}_ovbake"

    # Create empty mesh + object
    mesh = bpy.data.meshes.new(f"{bake_name}_mesh")
    obj = bpy.data.objects.new(bake_name, mesh)
    scene.collection.objects.link(obj)

    # Add Geometry Nodes modifier and fresh group
    node_group = bpy.data.node_groups.new(f"{bake_name}_group", 'GeometryNodeTree')
    mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
    mod.node_group = node_group

    # Setup nodes
    nodes = node_group.nodes
    links = node_group.links
    nodes.clear()

    # Add output socket via interface
    # Create socket via 4.4 API
    node_group.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    output_node = nodes.new("NodeGroupOutput")
    output_node.location = (600, 0)
    output_node.is_active_output = True
    output_node = nodes.new("NodeGroupOutput")
    output_node.location = (600, 0)
    output_node.is_active_output = True

    realize_node = nodes.new("GeometryNodeRealizeInstances")
    realize_node.location = (400, 0)

    if use_collection:
        if collection_name not in bpy.data.collections:
            raise ValueError(f"Collection '{collection_name}' not found")
        source_node = nodes.new("GeometryNodeCollectionInfo")
        collection = bpy.data.collections[collection_name]
        if collection.name not in scene.collection.children:
            scene.collection.children.link(collection)
        source_node.inputs["Collection"].default_value = collection
        source_node.inputs["Separate Children"].default_value = False
        source_node.inputs["Reset Children"].default_value = False
        source_node.transform_space = 'RELATIVE'
        links.new(source_node.outputs["Instances"], realize_node.inputs["Geometry"])
    else:
        source_node = nodes.new("GeometryNodeObjectInfo")
        source_node.inputs["Object"].default_value = active_obj
        source_node.transform_space = vat_settings.vat_transform

        source_node.inputs["As Instance"].default_value = False
        links.new(source_node.outputs["Geometry"], realize_node.inputs["Geometry"])

    source_node.location = (0, 0)

    # Link nodes
    links.new(realize_node.outputs["Geometry"], output_node.inputs["Geometry"])  # ← this now works

    # Deselect all, activate new object
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    context.view_layer.objects.active = obj

    # Duplicate and apply modifiers
    bpy.ops.object.duplicate()
    dup = context.active_object
    bpy.ops.object.convert(target='MESH')

    # Join back into original
    obj.select_set(True)
    dup.select_set(True)
    context.view_layer.objects.active = obj
    bpy.ops.object.join()
    
    if vat_settings.proxy_method == 'COLLAPSE':
        
        # ops to collapse mesh to center (tbd replace with more stable data calls)
        bpy.context.scene.cursor.location[0] = 0
        bpy.context.scene.cursor.location[1] = 0
        bpy.context.scene.cursor.location[2] = 0
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.merge(type='CURSOR')
        bpy.ops.object.editmode_toggle()

    scene = bpy.context.scene  # Make sure 'scene' is defined

    # Ensure OpenVATPreview collection exists
    vat_coll = bpy.data.collections.get("OpenVATPreview")
    if not vat_coll:
        vat_coll = bpy.data.collections.new("OpenVATPreview")
        scene.collection.children.link(vat_coll)
    # If it exists but isn't linked into this scene, link it
    elif vat_coll.name not in {c.name for c in scene.collection.children}:
        scene.collection.children.link(vat_coll)

    # Move object into OpenVATPreview
    for c in obj.users_collection:
        c.objects.unlink(obj)
    vat_coll.objects.link(obj)

    # Final selection state
    obj.select_set(True)
    context.view_layer.objects.active = obj
    if active_obj:
        active_obj.select_set(False)
