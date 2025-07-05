# OpenVAT Utility Functions

import bpy
import json
import math
import bmesh
import os

NODE_GROUPS_BLEND_FILE = os.path.join(os.path.dirname(__file__), "vat_node_groups.blend")

def append_node_group(group_name):
    with bpy.data.libraries.load(NODE_GROUPS_BLEND_FILE, link=False) as (data_from, data_to):
        if group_name in data_from.node_groups:
            data_to.node_groups.append(group_name)

def ensure_node_group(group_name):
    if group_name not in bpy.data.node_groups:
        append_node_group(group_name)

def make_custom_data(obj_name, attr_names, frame_start, frame_end, output_filepath, remap_output_filepath):
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"Object '{obj_name}' not found")
        return

    frames = frame_end - frame_start + 1
    channel_remap_data = {}

    for attr in attr_names:
        if not attr or attr.upper() == "NONE":
            channel_remap_data["None"] = {
                "Min": 0.0,
                "Max": 0.0,
                "Frames": frames
            }
            continue

        frame_data = {}
        for frame in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(frame)
            values = get_geometry_nodes_data(obj, attr)
            frame_data[frame] = values

        attr_min, attr_max = find_scalar_max_min(frame_data)
        channel_remap_data[attr] = {
            "Min": attr_min,
            "Max": attr_max,
            "Frames": frames
        }

    # Write or return the remap info
    with open(remap_output_filepath, 'w') as f:
        json.dump(channel_remap_data, f, indent=4)

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

    return min_value, max_value
            
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

def read_custom_info(filepath, attr_names):
    """
    Returns a flat list of min/max per attribute: [min_r, min_g, min_b, max_r, max_g, max_b]
    """
    with open(filepath, 'r') as f:
        data = json.load(f)

    min_vals = []
    max_vals = []

    for attr in attr_names:
        if not attr or attr.upper() == "NONE":
            min_vals.append(0.0)
            max_vals.append(0.0)
            continue
        
        if attr not in data:
            raise ValueError(f"Attribute '{attr}' not found in remap file.")

        min_vals.append(data[attr]["Min"])
        max_vals.append(data[attr]["Max"])


    return (*min_vals, *max_vals)

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
    def next_power_of_2(x):
        return 1 if x <= 1 else 2**math.ceil(math.log2(x))

    def powers_of_two(min_val=64, max_val=8192):
        val = min_val
        while val <= max_val:
            yield val
            val *= 2

    best = None
    best_area = float('inf')

    for width in powers_of_two():
        num_wraps = math.ceil(num_vertices / width)
        height_unrounded = num_frames * num_wraps
        height = next_power_of_2(height_unrounded)

        log2_width = math.log2(width)
        log2_height = math.log2(height)

        if abs(log2_width - log2_height) > 1:
            continue  # Skip if too far from square

        area = width * height
        if area < best_area:
            best = (width, height, num_wraps)
            best_area = area

    return best


def calculate_packed_vat_resolution(num_vertices, num_frames):
    def next_pow2(n):
        return 2 ** math.ceil(math.log2(n))

    def powers_of_two(min_val=64, max_val=8192):
        v = min_val
        while v <= max_val:
            yield v
            v *= 2

    best = None
    best_area = float('inf')

    for width in powers_of_two():
        num_wraps = math.ceil(num_vertices / width)

        pos_height = num_wraps * num_frames
        norm_height = num_wraps * num_frames
        total_height = next_pow2(pos_height + norm_height)

        log_w = math.log2(width)
        log_h = math.log2(total_height)

        if abs(log_w - log_h) > 1:
            continue

        area = width * total_height
        if area < best_area:
            best = (width, total_height, num_wraps)
            best_area = area

    return best

 
 
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
    
def get_point_attributes_filtered(self, context, data_type_filter=None):
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

def get_evaluated_point_float_attributes(context):
    depsgraph = context.evaluated_depsgraph_get()
    obj = context.active_object
    if not obj or obj.type != 'MESH':
        return []

    eval_obj = obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()
    try:
        return [
            (attr.name, attr.name, "")
            for attr in eval_mesh.attributes
            if attr.domain == 'POINT' and attr.data_type == 'FLOAT'
        ]
    finally:
        eval_obj.to_mesh_clear()

_openvat_enum_cache = {
    "1": [("NONE", "None", "")],
    "2": [("NONE", "None", "")],
    "3": [("NONE", "None", "")]
}
