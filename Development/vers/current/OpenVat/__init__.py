import bpy
import bmesh
import math
import os
import json

bl_info = {
    "name": "OpenVAT",
    "blender": (4, 1, 1),
    "category": "Object",
}


# Path to the .blend file containing the node groups
NODE_GROUPS_BLEND_FILE = os.path.join(os.path.dirname(__file__), "vat_node_groups.blend")


def append_node_group(group_name):
    with bpy.data.libraries.load(NODE_GROUPS_BLEND_FILE, link=False) as (data_from, data_to):
        if group_name in data_from.node_groups:
            data_to.node_groups.append(group_name)

def ensure_node_group(group_name):
    if group_name not in bpy.data.node_groups:
        append_node_group(group_name)

class OBJECT_PT_VAT_Calculator(bpy.types.Panel):
    bl_idname = "OBJECT_PT_vat_calculator"
    bl_label = "VAT Calculator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OpenVAT'

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.type == 'MESH':
            num_vertices = len(obj.data.vertices)
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end
            num_frames = frame_end - frame_start + 1

            width, height, num_wraps = calculate_optimal_vat_resolution(num_vertices, num_frames)
            
            
            layout.label(text=f"Active Object: {obj.name}")
            layout.label(text=f"Vertex Count: {len(obj.data.vertices)}, Frame Range: {context.scene.frame_start} - {context.scene.frame_end}")
            layout.label(text=f"Output Resolution: {str(width)} x {str(height)}")
            
            
            layout.prop(context.scene, "vat_output_directory")
            layout.prop(context.scene, "vat_object_space", text="Vertex Normals")
            layout.prop(context.scene, "vat_custom_proxy")

            layout.operator("object.calculate_vat_resolution", text="Create VAT")
        else:
            layout.label(text="No active mesh object selected")

class OBJECT_OT_CalculateVATResolution(bpy.types.Operator):
    bl_idname = "object.calculate_vat_resolution"
    bl_label = "Calculate VAT Resolution"

    def execute(self, context):
        outDir = bpy.context.scene.vat_output_directory
        
        if outDir == "/tmp//":
            outDir = os.path.join(os.path.dirname(bpy.data.filepath), "openVAT")
            
        obj = context.view_layer.objects.active
        obj_name = obj.name
        attribute_name = "colPos"
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        object_space = context.scene.vat_object_space
        custom_proxy = context.scene.vat_custom_proxy
        

        blend_filepath = bpy.data.filepath
        export_directory = bpy.path.abspath(context.scene.vat_output_directory)

        # Create export directory if it does not exist
        if not os.path.exists(export_directory):
            os.makedirs(export_directory)

        object_directory = os.path.join(export_directory, f"{obj_name}_vat")
        if not os.path.exists(object_directory):
            os.makedirs(object_directory)

        output_filepath = os.path.join(object_directory, f"{obj_name}-remap_info.json")
        remap_output_filepath = os.path.join(object_directory, f"{obj_name}-remap_info.json")

        # Ensure the required node groups are available
#        ensure_node_group("ov_encode-from")
        ensure_node_group("ov_generated-pos")
#        ensure_node_group("ov_vat-decoder-os")
        ensure_node_group("ov_vat-decoder-vs")
        ensure_node_group("ov_calculate-position-vs")
#        ensure_node_group("ov_calculate-position-os")
        
        temp_obj = None
        
        if custom_proxy == False:
            temp_obj = obj.copy()
            temp_obj.data = obj.data.copy()
            context.scene.frame_current = frame_start
            context.scene.collection.objects.link(temp_obj)
            for modifier in temp_obj.modifiers[:]:
                apply_modifier(temp_obj, modifier)
        else:
            selected_objects = bpy.context.selected_objects

            # Check if exactly two objects are selected
            if len(selected_objects) == 2:
                # Get the active object
                active_object = bpy.context.active_object
                
                # Identify the selected (non-active) object
                selected_non_active_object = None
                
                for object in selected_objects:
                    if object != active_object:
                        temp_obj = object
                        break
                
                if temp_obj:
                    print("Selected (non-active) object:", temp_obj.name)
                else:
                    print("No selected (non-active) object found.")               
            else:
                print("Exactly two objects must be selected.")

        if temp_obj == None:
            return {'FINISHED'}
        
#        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.select_all(action='DESELECT')
        
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        positionNodes = bpy.ops.object.modifier_add(type='NODES')
        obj.modifiers[-1].name  = "positionCalculation"
        obj.modifiers[-1].node_group = bpy.data.node_groups["ov_generated-pos"]
        obj.modifiers[-1]["Socket_3"] = temp_obj

        # Execute the main VAT calculation and export process
        main(obj_name, attribute_name, frame_start, frame_end, output_filepath, remap_output_filepath)
        
        min_x, min_y, min_z, max_x, max_y, max_z = read_remap_info(remap_output_filepath)
        context.scene['min_x'] = min_x
        context.scene['min_y'] = min_y
        context.scene['min_z'] = min_z
        context.scene['max_x'] = max_x
        context.scene['max_y'] = max_y
        context.scene['max_z'] = max_z

        self.report({'INFO'}, "VAT Calculation Completed")
        
        context.scene.frame_current = frame_start
        num_vertices = len(obj.data.vertices)
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        num_frames = frame_end - frame_start + 1

        width, height, num_wraps = calculate_optimal_vat_resolution(num_vertices, num_frames)
        
        
        setup_proxy_scene(obj, num_frames, width, height, num_wraps, object_space, temp_obj)
        
        if custom_proxy == False:
            bpy.data.objects.remove(temp_obj)
        bpy.data.scenes.remove(bpy.data.scenes[obj.name + "_proxy_scene"])
        bpy.data.scenes.remove(bpy.data.scenes[obj.name + "_vat"])
        
        bpy.ops.object.select_all(action='DESELECT')
        
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_remove(modifier="positionCalculation")
    

        return {'FINISHED'}

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

    return (width, height, num_wraps)

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

def setup_vat_tracker(vat_scene, obj_name, num_frames, width, height, num_wraps, proxy_name, original_scene, nodegroup_method):
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
        
def setup_proxy_scene(obj, num_frames, width, height, num_wraps, object_space, temp_obj):
    original_scene = bpy.context.scene
    bpy.ops.scene.new(type='NEW')
    proxy_scene = bpy.context.scene
    proxy_scene.name = f"{obj.name}_proxy_scene"

    proxy_scene.frame_end = num_frames - 1
    proxy_scene.frame_start = 0

    proxy_obj = temp_obj.copy()
    proxy_obj.data = temp_obj.data.copy()
    proxy_scene.collection.objects.link(proxy_obj)

    bpy.context.view_layer.objects.active = proxy_obj
    proxy_obj.select_set(True)

    for modifier in proxy_obj.modifiers[:]:
        apply_modifier(proxy_obj, modifier)

    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    bpy.ops.object.modifier_add(type='NODES')
    proxy_obj.modifiers[-1].node_group = bpy.data.node_groups["ov_generated-pos"]

    create_uv_map(proxy_obj, width, height, num_frames)
#    object_space = context.scene.vat_object_space
    setup_vat_scene(proxy_obj, obj.name, original_scene.name, num_frames, width, height, num_wraps, object_space)

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
#    if object_space:
#        vat_obj.modifiers[-1].node_group = bpy.data.node_groups["ov_vat-decoder-os"]
#    else:
    vat_obj.modifiers[-1].node_group = bpy.data.node_groups["ov_vat-decoder-vs"]

    vat_obj.modifiers["GeometryNodes"]["Socket_2_attribute_name"] = "VAT_UV"
    vat_obj.modifiers["GeometryNodes"]["Socket_6"] = num_frames
    vat_obj.modifiers["GeometryNodes"]["Socket_7"] = height
    vat_obj.modifiers["GeometryNodes"]["Socket_9"] = bpy.data.images[obj.name + "_vat.png"]
    vat_obj.modifiers["GeometryNodes"]["Socket_3"] = original_scene['min_x']
    vat_obj.modifiers["GeometryNodes"]["Socket_4"] = original_scene['max_x']
    vat_obj.modifiers["GeometryNodes"]["Socket_10"] = original_scene['min_y']
    vat_obj.modifiers["GeometryNodes"]["Socket_11"] = original_scene['max_y']
    vat_obj.modifiers["GeometryNodes"]["Socket_12"] = original_scene['min_z']
    vat_obj.modifiers["GeometryNodes"]["Socket_13"] = original_scene['max_z']

    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    vat_obj.name = obj.name + "_vat"

    export_vat_fbx()

def setup_vat_scene(proxy_obj, obj_name, original_scene_name, num_frames, width, height, num_wraps, object_space):
    bpy.ops.scene.new(type='NEW')
    vat_scene = bpy.context.scene
    vat_scene.name = f"{obj_name}_vat"
    original_scene = bpy.data.scenes[original_scene_name]
    output_dir = original_scene.vat_output_directory    
    
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
    vat_scene.render.image_settings.file_format = 'PNG'
    vat_scene.render.image_settings.color_mode = 'RGBA'
    vat_scene.render.image_settings.color_depth = '16'
    vat_scene.render.image_settings.compression = 0
    vat_scene.render.dither_intensity = 0
    vat_scene.render.use_compositing = False
    vat_scene.render.use_sequencer = False
    vat_scene.eevee.taa_render_samples = 1
    
    original_scene = bpy.data.scenes[original_scene_name] 
    
    os.makedirs(output_dir, exist_ok=True)
    render_vat_scene(vat_scene, 1, output_dir)
    vat_scene.render.use_compositing = True
   
    # Set compositing nodes in VAT scene
    setup_compositing(vat_scene, output_dir, vat_scene.name, proxy_obj)
    

    nodegroup_method = "ov_calculate-position-vs"
    
    setup_vat_tracker(vat_scene, obj_name, num_frames, width, height, num_wraps, proxy_obj.name, original_scene, nodegroup_method)
    
    # Render VAT   
    render_vat_scene(vat_scene, num_frames, output_dir)
    
    if (object_space):  
        bpy.context.object.modifiers["GeometryNodes"]["Socket_17"] = True    
        
        rendername = vat_scene.name.replace("_vat", "_vnrm")
        vat_scene.render.use_compositing = False
        render_vat_nrml(vat_scene, 1, output_dir)
        vat_scene.render.use_compositing = True
        tree = vat_scene.node_tree
        
        image_node = tree.nodes["Image"]
        image = bpy.data.images.get(rendername + ".png")
        image_node.image = image
        image.colorspace_settings.name = 'Non-Color'

        render_vat_nrml(vat_scene, num_frames, output_dir)
        
    

def setup_compositing(vat_scene, output_dir, scene_name, proxy_obj):
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
    
    image = bpy.data.images.get(vat_scene.name + ".png")
    image_node.image = image
    image.colorspace_settings.name = 'Non-Color'
    zcombine_node.use_alpha = True
    zcombine_node.use_antialias_z = False
    
def render_vat_scene(vat_scene, num_frames, output_dir):
    start_frame = vat_scene.frame_start
    end_frame = vat_scene.frame_end
    output_path = os.path.join(output_dir, f"{vat_scene.name}", f"{vat_scene.name}.png")
    nrmoutput_path = os.path.join(output_dir, f"{vat_scene.name}", vat_scene.name.replace("_vat", "_vnrm") + ".png")

    if os.path.exists(output_path):
        bpy.data.images.remove(bpy.data.images.load(output_path))
    
    for frame in range(start_frame -1, end_frame + 1):
        vat_scene.frame_set(frame)
        vat_scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.get(vat_scene.name + ".png")
        if img is not None:
            img.reload()
        else:
            img = bpy.data.images.load(output_path)
        print(f"Rendered and reloaded frame {frame}")
    

def render_vat_nrml(vat_scene, num_frames, output_dir):
    start_frame = vat_scene.frame_start
    end_frame = vat_scene.frame_end
    
    rendername = vat_scene.name.replace("_vat", "_vnrm")
    output_path = os.path.join(output_dir, f"{vat_scene.name}", f"{rendername}.png")

    if os.path.exists(output_path):
        bpy.data.images.remove(bpy.data.images.load(output_path))
    
    for frame in range(start_frame -1, end_frame + 1):
        vat_scene.frame_set(frame)
        vat_scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.get(rendername + ".png")
        if img is not None:
            img.reload()
        else:
            img = bpy.data.images.load(output_path)
        print(f"Rendered and reloaded frame {frame}")

def export_vat_fbx():
    obj = bpy.context.active_object
    if obj is None:
        raise Exception("No active object selected")

#    blend_filepath = bpy.data.filepath
#    blend_directory = os.path.dirname(blend_filepath)
    export_directory = bpy.path.abspath(bpy.context.scene.vat_output_directory)
    object_directory = os.path.join(export_directory, obj.name)
    if not os.path.exists(object_directory):
        os.makedirs(object_directory)

    export_path = os.path.join(object_directory, f"{obj.name}.fbx")

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
        use_tspace=False,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        use_armature_deform_only=False,
        bake_anim=False,
        path_mode='AUTO'
    )

    print(f"Exported {obj.name} to {export_path}")

def get_geometry_nodes_data(obj, attribute_name):
    data = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.data

    if attribute_name in mesh.attributes:
        attr_data = mesh.attributes[attribute_name].data
        for item in attr_data:
            data.append([round(val, 8) for val in item.vector])
    else:
        print(f"Attribute '{attribute_name}' not found in '{obj.name}'")

    return data

def write_json(data, filepath):
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, float):
                return format(obj, ".8f")
            return json.JSONEncoder.default(self, obj)

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4, cls=CustomEncoder)

def round_to_nearest_ten(val, func):
    return func(val * 10) / 10

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

def remap_values(value, old_min, old_max, new_min=0, new_max=1):
    if old_max == old_min:
        return new_min
    return (value - old_min) / (old_max - old_min) * (new_max - new_min) + new_min

def main(obj_name, attribute_name, frame_start, frame_end, output_filepath, remap_output_filepath):
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"Object '{obj_name}' not found")
        return

    all_frames_data = {}

    for frame in range(frame_start, frame_end + 1):
        bpy.context.scene.frame_set(frame)
        frame_data = get_geometry_nodes_data(obj, attribute_name)
        all_frames_data[frame] = frame_data

    write_json(all_frames_data, output_filepath)
    overall_max, overall_min = find_max_min_values(all_frames_data)

    print(f"Data saved to {output_filepath}")
    print(f"Overall Max values: {overall_max}")
    print(f"Overall Min values: {overall_min}")

    remap_info = {
        "os-remap": {
            "Min": overall_min,
            "Max": overall_max
        }
    }
    write_json(remap_info, remap_output_filepath)
    print(f"Remap information saved to {remap_output_filepath}")

def read_remap_info(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)

    min_values = data["os-remap"]["Min"]
    max_values = data["os-remap"]["Max"]

    min_x, min_y, min_z = min_values
    max_x, max_y, max_z = max_values

    return min_x, min_y, min_z, max_x, max_y, max_z

def apply_modifier(obj, modifier):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_from_eval = bpy.data.meshes.new_from_object(obj_eval)

    obj.modifiers.remove(modifier)
    obj.data = mesh_from_eval

def register():
    bpy.types.Scene.vat_output_directory = bpy.props.StringProperty(
        name="Output Directory",
        description="Directory to save VAT files",
        default="/tmp\\"
    )
    bpy.types.Scene.vat_object_space = bpy.props.BoolProperty(
        name="Object Space",
        description="Exports an additional map containing animated vertex normal data",
        default=False
    )
    bpy.types.Scene.vat_custom_proxy = bpy.props.BoolProperty(
        name="Use Custom Proxy",
        description="Selected object acts as proxy to active object. If False, uses frame 1 as proxy deformation",
        default=False
    )
    bpy.utils.register_class(OBJECT_PT_VAT_Calculator)
    bpy.utils.register_class(OBJECT_OT_CalculateVATResolution)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_VAT_Calculator)
    bpy.utils.unregister_class(OBJECT_OT_CalculateVATResolution)
    del bpy.types.Scene.vat_output_directory
    del bpy.types.Scene.vat_object_space
    del bpy.types.Scene.vat_custom_proxy

if __name__ == "__main__":
    register()