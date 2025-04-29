"""
Title: OpenVAT Encoder
Description: Encode and preview vertex animation textures
Author: Luke Stilson
Date: 2025-04-29
Version: 1.0.3

Usage:
    python __init__.py [openvatencoder.py source content]
"""

import bpy
import bmesh
import math
import os
import json

# File containing necessicary Node groups, appended when needed in code.
# Methods for appending consolidated here for development purposes
NODE_GROUPS_BLEND_FILE = os.path.join(os.path.dirname(__file__), "vat_node_groups.blend")

def append_node_group(group_name):
    with bpy.data.libraries.load(NODE_GROUPS_BLEND_FILE, link=False) as (data_from, data_to):
        if group_name in data_from.node_groups:
            data_to.node_groups.append(group_name)

def ensure_node_group(group_name):
    if group_name not in bpy.data.node_groups:
        append_node_group(group_name)

        

class OBJECT_PT_VAT_OPTIONS(bpy.types.Panel):
    bl_idname = "OBJECT_PT_vat_options"
    bl_label = "OpenVAT Encoding"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OpenVAT'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        settings = context.scene.vat_settings
        scene = context.scene
        
        grid = layout.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        grid.label(text="Target", icon='CON_OBJECTSOLVER')
        grid.prop(settings, "encode_target", text="")
        
        if settings.encode_target != 'ACTIVE_OBJECT':
            grid = layout.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
            grid.label(text="Target Collection")
            grid.prop(settings, "vat_collection", text="")
        
        layout.separator()
        
        grid = layout.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        grid.label(text="Frame Range", icon='ANIM')
        grid.prop(scene, "frame_start", text="Start")
        grid.separator()
        grid.prop(scene, "frame_end", text="End")
        
        layout.separator()
        row = layout.row()
        grid = layout.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        grid.label(text="Target Attributes", icon='RNA')
        grid.prop(settings, "encode_type", text="")
        
        if settings.encode_type == 'DEFAULT':
            box = layout.box()
            row = box.row()
            row.label(text="Vertex Offset", icon="MESH_DATA")
            grid = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
            grid.label(text="Offset Basis (Proxy)")
            grid.prop(settings, "proxy_method", text="")
            
            box.separator()
            grid = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
            
            grid.label(text="Vertex Normals", icon='NORMALS_VERTEX')
            grid.prop(settings, "vat_normal_encoding", text="")
            
        
        else:
            box = layout.box()
            row = box.row()
            row.label(text="Custom Data", icon="RNA")
            grid = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
            grid.label(text="Custom Vector (RGB)")
            grid.prop(settings, "user_attribute", text="")
#            grid = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
#            grid.label(text="Custom Float (A)")
#            grid.prop(settings, "user_scalar", text="")
        
        
        layout.separator()
        row = layout.row()
        row.label(text="Mesh Settings", icon="SETTINGS")
        row = layout.row(align=True)
        row.label(text="Transform")
        row.prop(settings, "vat_transform", expand=True)
        row = layout.row()
        row.prop(settings, "clean_mesh", text="Strip Vertex Data") 
        row = layout.row()
        row.prop(settings, "rip_edges")
        
# Output Settings - relating to data being exported      
class OBJECT_PT_VAT_OUTPUT(bpy.types.Panel):
    bl_idname = "OBJECT_PT_vat_output"
    bl_label = "Output"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OpenVAT'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        settings = context.scene.vat_settings
        scene = context.scene  
        
        row = layout.row(align=True)
        row.prop(settings, "vat_output_directory", text="")
        
        #
        # Dissallowed output (Hiden UI Scenarios)
        #
        
        if settings.encode_target == 'ACTIVE_OBJECT': 
            if not obj or obj.type != 'MESH' or len(obj.data.polygons) == 0:
                layout.label(text="No valid mesh object selected", icon='ERROR')
                return
            for coll in obj.users_collection:
                if coll.name == 'OpenVATPreview':
                    layout.label(text="Target in OpenVATPreview collection is not allowed", icon='ERROR')
                    return
        else:
            if not settings.vat_collection:
                layout.label(text="No valid collection selected", icon='ERROR')
                return
            if settings.vat_collection.name == "OpenVATPreview":
                layout.label(text="Collection 'OpenVATPreview' cannot be targeted", icon='ERROR')
                return
            has_mesh = any(o.type == 'MESH' and len(o.data.vertices) > 0 for o in settings.vat_collection.all_objects)
            if not has_mesh:
                layout.label(text="Selected collection contains no valid mesh objects", icon='ERROR')
                return
        #
        # Output General Settings
        #
        
        row = layout.row()
        row.scale_y = 1.6
        abs_path = bpy.path.abspath(settings.vat_output_directory)
        if os.path.isdir(abs_path):
            row.operator("object.calculate_vat_resolution", text="Encode Vertex Animation Texture", icon='MOD_DATA_TRANSFER')
        else:
            row.label(text="Export directory not set", icon='WARNING_LARGE')
        abs_path = bpy.path.abspath(settings.vat_output_directory)
        grid = layout.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        grid.prop(settings, "export_mesh", text="Export Model")
        grid.label(text="")
        if settings.export_mesh:
            grid.label(text="Model Format")
            grid.prop(settings, "mesh_format", text="")
        grid.label(text="Image Format")
        grid.prop(settings, "image_format", text="")
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_encoding_info", icon="INFO_LARGE", emboss=False)
        
        #
        # Encoding Details Section
        #
        
        if settings.show_encoding_info:
            if settings.encode_target == "ACTIVE_OBJECT":
                num_vertices = len(obj.data.vertices)
                max_verts = get_virtual_ripped_vertex_count(obj)
            else:
                num_vertices = 0
                max_verts = 0
                if settings.vat_collection != None:
                    if settings.vat_collection:
                        for child_obj in settings.vat_collection.all_objects:
                            if child_obj.type == 'MESH':
                                num_vertices += len(child_obj.data.vertices)
                                max_verts += get_virtual_ripped_vertex_count(child_obj)
                    
            num_frames = scene.frame_end - scene.frame_start + 1
            
            if settings.vat_normal_encoding == 'PACKED' and bpy.context.scene.vat_settings.encode_type == 'DEFAULT':
                width, height, _ = calculate_packed_vat_resolution(num_vertices, num_frames)
            else:
                width, height, _ = calculate_optimal_vat_resolution(num_vertices, num_frames)
            
            if settings.vat_normal_encoding == 'PACKED' and bpy.context.scene.vat_settings.encode_type == 'DEFAULT':
                maxwidth, maxheight, _ = calculate_packed_vat_resolution(max_verts, num_frames)
            else:
                maxwidth, maxheight, _ = calculate_optimal_vat_resolution(max_verts, num_frames)
            
            if settings.encode_target != "ACTIVE_OBJECT":     
                box = layout.box()
                box.label(text=f"Encode Target: {settings.vat_collection.name}", icon='OUTLINER_COLLECTION')
            else:
                if settings.vat_collection != None:
                    box = layout.box()
                    box.label(text=f"Encode Target: {obj.name}", icon='MESH_DATA') 
            row = box.row()
            row.label(text=f"Total Frames: {num_frames}", icon='ANIM')
            if settings.vat_normal_encoding != 'NONE':
                if settings.rip_edges:
                    use_range = True
                else:
                    use_range = False
            else:
                use_range = False
            if use_range:
                row=box.row()
                row.label(text=f"Estimated Min-Max (Edge-split Potential)", icon = 'INFO_LARGE')
                row = box.row()
                row.label(text=f"Vertices: {num_vertices} - {max_verts}", icon='VERTEXSEL')
                if settings.encode_target != "COLLECTION_BATCH":
                    row = box.row()
                    row.label(text=f"Resolution: {width} x {height} - {maxwidth} x {maxheight}", icon='FILE_IMAGE')
                else:
                    row = box.row()
                    row.label(text=f"Resolution calculated per batch object", icon="OUTLINER_OB_IMAGE")
            else:
                row = box.row()
                row.label(text=f"Vertices: {num_vertices}", icon='VERTEXSEL')
                if settings.encode_target != "COLLECTION_BATCH":
                    row = box.row()
                    row.label(text=f"Resolution: {width} x {height}")
                else:
                    row = box.row()
                    row.label(text=f"Resolution calculated per batch object", icon="OUTLINER_OB_IMAGE")                    
            row=box.row()
            row.label(text="Estimates based on currently-realized data", icon="DECORATE_KEYFRAME")

        
class OBJECT_OT_OpenOutputDirectory(bpy.types.Operator):
    bl_idname = "object.open_output_directory"
    bl_label = "Open Output Directory"
    bl_description = "Open the output directory in the system file explorer"

    def execute(self, context):
        import os
        import subprocess
        output_dir = bpy.path.abspath(context.scene.vat_settings.vat_output_directory)
        if os.path.isdir(output_dir):
            subprocess.Popen(f'explorer "{output_dir}"' if os.name == 'nt' else ['xdg-open', output_dir])
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Directory does not exist")
            return {'CANCELLED'}

# Main Operation
class OBJECT_OT_CalculateVATResolution(bpy.types.Operator):
    bl_idname = "object.calculate_vat_resolution"
    bl_label = "Calculate VAT Resolution"
    bl_description = "Export a UV-Based Vertex Animation Texture, sidecar data and compatible model to the defined Export location"

    def execute(self, context):
        settings = context.scene.vat_settings
        outDir = bpy.path.abspath(bpy.context.scene.vat_settings.vat_output_directory)
        blend_filepath = bpy.data.filepath
        export_directory = bpy.path.abspath(context.scene.vat_settings.vat_output_directory)
        
        #
        # Geometry Setup
        #
        
        selected_temp = None
        
        # Encoding starts with start frame based proxy
        if settings.proxy_method == 'START_FRAME':
            
            context.scene.frame_current = context.scene.frame_start
        
        # Collection mode defaults to false unless selected
        collection_mode = False
        collection_target = ""
        custom_proxy = False
        
        if settings.proxy_method == 'SELECTED_OBJECT':
            custom_proxy = True
            selected_objects = bpy.context.selected_objects
            if len(selected_objects) == 2:
                active_object = bpy.context.active_object
                selected_non_active_object = None
                for object in selected_objects:
                    if object != active_object:
                        selected_temp = object
                        break
                if selected_temp:
                    print("Selected (non-active) object:", selected_temp.name)
                else:
                    print("No selected (non-active) object found.")               
            else:
                print("Exactly two objects must be sel ected.")
        
        if settings.encode_target == 'COLLECTION_COMBINE': # Collection target only valid when collection_mode is true
            collection_mode = True
            collection_target = settings.vat_collection.name
        
        # Creates new object, representing target geometry
        create_geo_nodes_bake(use_collection=collection_mode, collection_name=collection_target)
        obj = context.view_layer.objects.active
        obj_name = obj.name
            
        # Perform Normal-Safe Edge Split on new object
        if settings.vat_normal_encoding != 'NONE':
            if settings.rip_edges:
                rip_hard_edges(obj)
        
        obj.select_set(True)
        
        if settings.vat_normal_encoding == 'PACKED':
            pack_normals = True
            
        else:
            pack_normals = False
        
        # Proxy creation and selection
        temp_obj = None
        if custom_proxy == False:
            temp_obj = obj.copy()
            temp_obj.data = obj.data.copy()
            if settings.proxy_method == 'START_FRAME':
                context.scene.frame_current = context.scene.frame_start
            context.scene.collection.objects.link(temp_obj)
            for modifier in temp_obj.modifiers[:]:
                apply_modifier(temp_obj, modifier)
        else:
            temp_obj = selected_temp
        
        if temp_obj == None:
            return {'FINISHED'}
        
        #
        # Initiate Saturation Sampling
        #
        
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        
        # Create output directories (for JSON)
        if not os.path.exists(export_directory):
            os.makedirs(export_directory)
        
        # Name json based on target object
        output_rename = obj_name.replace("_ovbake", "")
        
        # Directory target + '_vat'
        object_directory = os.path.join(export_directory, f"{output_rename}_vat")
        if not os.path.exists(object_directory):
            os.makedirs(object_directory)
        
        # Create json output directory
        output_filepath = os.path.join(object_directory, f"{output_rename}-remap_info.json")
        
        # Saturation sampling output
        remap_output_filepath = os.path.join(object_directory, f"{output_rename}-remap_info.json")

        # Ensure the required node groups are available
        ensure_node_group("ov_generated-pos")
        ensure_node_group("ov_vat-decoder-vs")
        ensure_node_group("ov_calculate-position-vs")
        
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = obj # ensure new generated mesh is active
        obj.select_set(True)
        
        positionNodes = bpy.ops.object.modifier_add(type='NODES')
        obj.modifiers[-1].name  = "positionCalculation"
        obj.modifiers[-1].node_group = bpy.data.node_groups["ov_generated-pos"]
        obj.modifiers[-1]["Socket_3"] = temp_obj

        # Execute the saturation remapping
        if settings.encode_type == 'DEFAULT':
            attribute_name = "colPos"
        else:
            attribute_name = settings.user_attribute
            
        make_remap_data(obj_name, attribute_name, frame_start, frame_end, output_filepath, remap_output_filepath, "")
        
        #! Should update to better usage, not in scene props
        min_x, min_y, min_z, max_x, max_y, max_z = read_remap_info(remap_output_filepath, attribute_name)
        context.scene['min_x'] = min_x
        context.scene['min_y'] = min_y
        context.scene['min_z'] = min_z
        context.scene['max_x'] = max_x
        context.scene['max_y'] = max_y
        context.scene['max_z'] = max_z
        
        num_vertices = len(obj.data.vertices)
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        num_frames = frame_end - frame_start + 1
        context.scene.frame_current = frame_start
        
        # Encode Normals
        if settings.encode_type == 'CUSTOM':
            pack_normals = False
            width, height, num_wraps = calculate_optimal_vat_resolution(num_vertices, num_frames)
        elif settings.vat_normal_encoding == 'PACKED':
            width, height, num_wraps = calculate_packed_vat_resolution(num_vertices, num_frames)   
        else:
            width, height, num_wraps = calculate_optimal_vat_resolution(num_vertices, num_frames)   
        
        # Store name for use after obj is deleted
        obj_name = obj.name
        
        # obj (temp) is deleted on success of the following
        setup_proxy_scene(obj, num_frames, width, height, num_wraps, temp_obj, pack_normals, frame_start)
        
        # Clean up creation data
        print("Cleaning up temporary node_groups, objects, and modifiers")
        if custom_proxy == False:
            bpy.data.objects.remove(temp_obj)
        bpy.data.scenes.remove(bpy.data.scenes[obj_name + "_proxy_scene"])
        bpy.data.scenes.remove(bpy.data.scenes[obj_name + "_vat"])
        bpy.ops.outliner.orphans_purge()
        
        # Finish
        self.report({'INFO'}, "VAT Encoding Completed")
        print("VAT Encoding Finished")
        print("Thank you for using OPENVAT - Your favorite Vertex Animation Encoder - Developed by Luke Stilson 2024 - Visit www.lukestilson.com for more information")
    
        return {'FINISHED'}

def clean_mesh_data(obj):

    if obj and obj.type == 'MESH':
        mesh = bpy.data.meshes.get(obj.data.name)
        color_attrs = [attr for attr in mesh.attributes if attr.data_type in {'FLOAT_COLOR', 'BYTE_COLOR'}]
        for attr in color_attrs:
            mesh.attributes.remove(attr)
        if mesh.shape_keys:
            key = mesh.shape_keys
            for block in list(key.key_blocks):
                key.key_blocks.remove(block)
            obj.shape_key_clear()
        while obj.vertex_groups:
            obj.vertex_groups.active_index = 0  # Set a valid active index
            obj.vertex_groups.remove(obj.vertex_groups[0])

# Calculation for estimating max amount of verts if all edges are ripped
def get_virtual_ripped_vertex_count(obj):
    if not obj or obj.type != 'MESH':
        return 0
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()
    count = len(eval_mesh.loops)
    eval_obj.to_mesh_clear()
    
    return count

# Best working approximations for output size based on realized data available
def calculate_optimal_vat_resolution(num_vertices, num_frames):
    total_pixels = num_vertices * num_frames
    approx_side = math.sqrt(total_pixels)

    def closest_power_of_2(n):
        return 2 ** math.floor(math.log2(n))

    width = closest_power_of_2(approx_side)
    height = closest_power_of_2(approx_side)

    while width * height < total_pixels:
        if width < height:
            width *= 2
        else:
            height *= 2

    num_wraps = math.ceil(num_vertices / width)

    # Ensure height is tall enough to fit all frame rows
    while height < num_frames * num_wraps:
        height *= 2

    return (int(width), int(height), num_wraps)

def calculate_packed_vat_resolution(num_vertices, num_frames):
    total_pixels = num_vertices * num_frames

    def closest_power_of_2(n):
        return 2 ** math.floor(math.log2(n))

    def next_power_of_2(n):
        return 2 ** math.ceil(math.log2(n))

    approx_side = math.sqrt(total_pixels)
    width = closest_power_of_2(approx_side)
    height = closest_power_of_2(approx_side)

    while width * height < total_pixels:
        if width < height:
            width *= 2
        else:
            height *= 2

    num_wraps = math.ceil(num_vertices / width)
    additional_rows_for_normals = num_wraps

    height_with_normals = height + additional_rows_for_normals
    height = next_power_of_2(height_with_normals)
    
    if height > width * 2:
        height /= 2
        width *= 2
        
    num_wraps = math.ceil(num_vertices / width)
        
    if ((num_wraps * 2) * num_frames) > height:
        if width < height:
            width *= 2
        else:
            height *= 2
        
    width = int(width)
    height = int(height)

    return (width, height, num_wraps)

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
        apply_modifier(proxy_obj, modifier)
    
    # Refresh
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
        clean_mesh_data(vat_obj)
    
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



#
# Saturation Functions - JSON min/max
#

def make_remap_data(obj_name, attribute_name, frame_start, frame_end, output_filepath, remap_output_filepath, scalar_value):
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"Object '{obj_name}' not found")
        return
    
    # Remap data for vector properties
    all_frames_data = {}
    scalar_data = {}
    frames = frame_end - frame_start + 1

    for frame in range(frame_start, frame_end + 1):
        bpy.context.scene.frame_set(frame)
        frame_data = get_geometry_nodes_data(obj, attribute_name)
        all_frames_data[frame] = frame_data
    overall_max, overall_min = find_max_min_values(all_frames_data)
    
    if attribute_name == "colPos":
        attribute_name = "os-remap"
        
    # Scalar value for alpha data
    if scalar_value:
        for frame in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(frame)
            frame_data = get_geometry_nodes_data(obj, scalar_value)
            scalar_data[frame] = frame_data
        
        scalar_max, scalar_min = find_scalar_max_min(scalar_data)
        
        remap_info = {
            attribute_name: {
                "Min": overall_min,
                "Max": overall_max,
                "Frames": frames
            },
            scalar_value: {
                "Min": scalar_min,
                "Max": scalar_max,
            }
        }
    else:
        remap_info = {
            attribute_name: {
                "Min": overall_min,
                "Max": overall_max,
                "Frames": frames
            }
    }
    
    write_json(remap_info, remap_output_filepath)
    print(f"Remap information saved to {remap_output_filepath}")
    
# Get data from dependency graph
def get_geometry_nodes_data(obj, attribute_name):
    data = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.data

    if attribute_name in mesh.attributes:
        attr = mesh.attributes[attribute_name]
        attr_data = attr.data

        if attr.domain not in {'POINT'}:
            print(f"Warning: Unsupported domain '{attr.domain}' for attribute '{attribute_name}'")

        for item in attr_data:
            if hasattr(item, 'vector'):
                data.append([round(val, 8) for val in item.vector])
            elif hasattr(item, 'value'):
                data.append(round(item.value, 8))
            else:
                print(f"Warning: Unknown attribute type for '{attribute_name}'")
    else:
        print(f"Attribute '{attribute_name}' not found in '{obj.name}'")

    return data

def find_scalar_max_min(all_frames_data):
    max_value = float('-inf')
    min_value = float('inf')
    
    for frame, data in all_frames_data.items():
        for value in data:
            max_value = max(max_value, value)
            min_value = min(min_value, value)
    if max_value == float('-inf'):
        max_value = None
    if min_value == float('inf'):
        min_value = None

    if max_value is not None:
        max_value = round_to_nearest_ten(max_value, math.ceil)
    if min_value is not None:
        min_value = round_to_nearest_ten(min_value, math.floor)

    return max_value, min_value
            
# Function to find x, y, z min/max from JSON
def find_max_min_values(all_frames_data):
    max_values = [float('-inf'), float('-inf'), float('-inf')]
    min_values = [float('inf'), float('inf'), float('inf')]

    for frame, data in all_frames_data.items():
        for vector in data:
            for i in range(3):
                max_values[i] = max(max_values[i], vector[i])
                min_values[i] = min(min_values[i], vector[i])

    max_values = [val if val != float('-inf') else None for val in max_values]
    min_values = [val if val != float('inf') else None for val in min_values]

    overall_max = [round_to_nearest_ten(val, math.ceil) if val is not None else None for val in max_values]
    overall_min = [round_to_nearest_ten(val, math.floor) if val is not None else None for val in min_values]

    return overall_max, overall_min

def round_to_nearest_ten(val, func):
    return func(val * 10) / 10

def read_remap_info(filepath, attribute):
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if attribute == "colPos":
        attribute = "os-remap"
    min_values = data[attribute]["Min"]
    max_values = data[attribute]["Max"]

    min_x, min_y, min_z = min_values
    max_x, max_y, max_z = max_values

    return min_x, min_y, min_z, max_x, max_y, max_z

def write_json(data, filepath):
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, float):
                return format(obj, ".8f")
            return json.JSONEncoder.default(self, obj)

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4, cls=CustomEncoder)



def apply_modifier(obj, modifier):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_from_eval = bpy.data.meshes.new_from_object(obj_eval)

    obj.modifiers.remove(modifier)
    obj.data = mesh_from_eval
 
def rip_hard_edges(obj):
    if not obj or obj.type != 'MESH':
        raise Exception("Active object must be a mesh")

    mesh = obj.data

    depsgraph = bpy.context.evaluated_depsgraph_get() # Gets evaluated edges post-modifiers
    eval_obj = obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()

    sharp_edge_indices = {
        i for i, e in enumerate(eval_mesh.edges)
        if e.use_edge_sharp
    }
    eval_obj.to_mesh_clear()

    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    edges_to_split = []
    for i, e in enumerate(bm.edges):
        if i in sharp_edge_indices:
            edges_to_split.append(e)
            continue

        if not e.smooth:
            edges_to_split.append(e)
            continue

        linked_faces = e.link_faces
        if len(linked_faces) == 2:
            if not linked_faces[0].smooth and not linked_faces[1].smooth:
                edges_to_split.append(e)

    # Perform Edge Split
    bmesh.ops.split_edges(bm, edges=edges_to_split)

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
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



def get_point_attributes_filtered(self, context, data_type_filter=None):
    """
    Returns a list of point attributes for the active object, optionally filtered by data_type.
    
    Args:
        data_type_filter (str or None): 'FLOAT', 'FLOAT_VECTOR', etc. or None for no filtering.
    
    Returns:
        list: List of (identifier, name, description) tuples for EnumProperty items.
    """
    items = []
    obj = context.active_object
    if obj and obj.type == 'MESH':
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        mesh = obj_eval.data
        
        for attr in mesh.attributes:
            if attr.domain != 'POINT':
                continue
            if attr.name.startswith('.') or attr.name.startswith('_') or len(attr.name) > 32:
                continue
            if data_type_filter and attr.data_type != data_type_filter:
                continue
            items.append((attr.name, attr.name, ""))
                
    if not items:
        items.append(('None', 'None', 'No attributes found'))
        
    return items


        
#       
# Properties
#

class VATSettings(bpy.types.PropertyGroup):
    vat_output_directory: bpy.props.StringProperty(
        name="Output Directory",
        description="Directory to save exported content (defaults to render output directory)",
        subtype='DIR_PATH',
        default="",  # Will be initialized from the scene on draw or execution
    )
    
    show_encoding_info: bpy.props.BoolProperty(
        name="Encoding Details",
        description="Show encoding details based on your current settings",
        default=False
    )

    vat_custom_proxy: bpy.props.BoolProperty(
        name="Use Custom Proxy",
        description="Selected object acts as proxy - which can be thought of as a Bind Pose or Basis. This will become the deformation of the static mesh export which vat encoding is relative to. Custom Proxy MUST have the exact vert count/order as the Target",
        default=False
    )
    
    vat_transform: bpy.props.EnumProperty(
        name="Transform Space",
        description="Interpret options for object transforms (world location of object)",
        items=[
            ('ORIGINAL', "Object", "Resulting mesh does not take object transforms into account, apply transforms on Target object for best results"),
            ('RELATIVE', "World", "Target object's world transforms are baked into VAT data, origin of VAT mesh is (0,0,0). Animated or current world transforms become deformation data"),
        ],
        default='ORIGINAL'
    )
    
    proxy_method: bpy.props.EnumProperty(
        name="Proxy Method (Mesh Basis)",
        description="Vertex Animation is represented as an offset from a static mesh, similar to a Bind-Pose",
        items=[
            ('START_FRAME', "Start Frame", "The target's deformation as it appears in the first encoded frame becomes the Proxy"),
            ('CURRENT_FRAME', "Current Frame", "The target's deformation as it appears in the scene's current frame becomes the Proxy"),
            ('SELECTED_OBJECT', "Selected Object", "A single selected object in scene may be chosen to be used as the proxy, valid only when Target and Proxy share exact vert/face count"),
        ],
        default='START_FRAME'
    )

    # Legacy
    vat_cleanup_enabled: bpy.props.BoolProperty(
        name="Perform Cleanup",
        description="Removes all generated data",
        default=True
    )
    
    rip_edges: bpy.props.BoolProperty(
        name="Create Normal-Safe Edges",
        description="Splits the resulting mesh on all sharp edges to provide proper per-vertex normal data (does not affect face count, increases final mesh vertex count along identified edges). Target geometry (source) is unaffected",
        default=True
    )
    
    encode_type: bpy.props.EnumProperty(
        name="Encoding Mode",
        description="Choose a format to export, always in Blender transform space (-Z Forward, Y Up)",
        items=[
            ('DEFAULT', "OpenVAT Standard", "Export vat-compatible mesh as .fbx"),
            ('CUSTOM', "Custom", "Choose custom attributes to encode"),
        ],
        default='DEFAULT'
    )
    
    user_attribute: bpy.props.StringProperty(
        name="Custom Vector (RGB)",
        description="Vector point attribute from the target object",
        default="",
#        items=lambda self, context: get_point_attributes_filtered(self, context, data_type_filter='FLOAT_VECTOR')
    )
    
    user_scalar: bpy.props.StringProperty(
        name="Custom Float (A)",
        description="Scalar point attribute from the active object",
        default="",
#        items=lambda self, context: get_point_attributes_filtered(self, context, data_type_filter='FLOAT')
    )
    
    custom_remap: bpy.props.BoolProperty(
        name="Force 0-1 Range",
        description="Export with data in the range of (0-1) only, and provide remapping details in JSON",
        default=True
    )
    
    export_mesh: bpy.props.BoolProperty(
        name="Include Mesh Export",
        description="Selected object acts as proxy to active object. If False, uses frame 1 as proxy deformation",
        default=True
    )
    
    clean_mesh: bpy.props.BoolProperty(
        name="Strip Data",
        description="Remove vertex groups, shape keys and vertex colors from the resulting model. Target geometry (source) is unaffected",
        default=True
    )
    
    mesh_format: bpy.props.EnumProperty(
        name="Mesh Format",
        description="Choose a format to export, always in Blender transform space (-Z Forward, Y Up)",
        items=[
            ('FBX', "FBX", "Export vat-compatible mesh as .fbx"),
            ('GLB', "glTF Binary", "Export vat-compatible mesh as .glb"),
            ('GLTF', "glTF Separate", "Export vat-compatible as .gltf + .bin + textures"),
        ],
        default='FBX'
    )
    
    use_transform: bpy.props.BoolProperty(
        name="Bake World Transform",
        description="Encode the world transform, as defined on the encode-target's object data - result pivot will always be (0,0,0)",
        default=True
    )
    
    encode_target: bpy.props.EnumProperty(
        name="Encode Target Type",
        description="Choose a method of encoding",
        items=[
            ('ACTIVE_OBJECT', "Active Object", "Encode the active object's Animation to VAT"),
            ('COLLECTION_COMBINE', "Collection (combined)", "Encode all the objects in a specified collection, combined into a single object"),
        ],
        default='ACTIVE_OBJECT'
    )
    
    image_format: bpy.props.EnumProperty(
        name="Image Format",
        description="Choose a method of encoding",
        items=[
            ('PNG', "PNG", "Lossless PNG with 16 bit color-depth"),
            ('EXR', "EXR", "Lossless OpenEXR Float (half) in ZIP Codec with 16 bit color-depth"),
        ],
        default='PNG'
    )
    
    vat_collection: bpy.props.PointerProperty(
        name="Target Collection",
        description="Reference to a Blender collection",
        type=bpy.types.Collection
    )
    
    vat_normal_encoding: bpy.props.EnumProperty(
        name="Normal Encoding",
        description="Choose how vertex normals are stored",
        items=[
            ('NONE', "None", "Only encode position data, do not export vertex normals data"),
            ('PACKED', "Packed", "Pack vertex normals into the same VAT as position"),
            ('SEPARATE', "Separate Map", "Use a separate texture output for vertex normals"),
        ],
        default='PACKED'
    )


def register():
    bpy.utils.register_class(VATSettings)
    bpy.types.Scene.vat_settings = bpy.props.PointerProperty(type=VATSettings)

    bpy.utils.register_class(OBJECT_PT_VAT_OPTIONS)
    bpy.utils.register_class(OBJECT_OT_CalculateVATResolution)
    bpy.utils.register_class(OBJECT_OT_OpenOutputDirectory)
    bpy.utils.register_class(OBJECT_PT_VAT_OUTPUT)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_CalculateVATResolution)
    bpy.utils.unregister_class(OBJECT_PT_VAT_OPTIONS)
    bpy.utils.unregister_class(OBJECT_OT_OpenOutputDirectory)
    bpy.utils.unregister_class(OBJECT_PT_VAT_OUTPUT)

    del bpy.types.Scene.vat_settings
    bpy.utils.unregister_class(VATSettings)
    

if __name__ == "__main__":
    register()
    ensure_node_group("ov_calculate-position-vs")