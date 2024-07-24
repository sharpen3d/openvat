import bpy
import json
import math

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
    max_value = float('-inf')
    min_value = float('inf')
    
    for frame, data in all_frames_data.items():
        for vector in data:
            max_value = max(max_value, max(vector))
            min_value = min(min_value, min(vector))
    
    overall_max = round_to_nearest_ten(max_value, math.ceil)
    overall_min = round_to_nearest_ten(min_value, math.floor)

    return overall_max, overall_min

def calculate_deltas(all_frames_data):
    frames = list(all_frames_data.keys())
    delta_data = {}

    for i, frame in enumerate(frames):
        prev_frame = frames[i - 1] if i > 0 else frames[-1]
        current_data = all_frames_data[frame]
        prev_data = all_frames_data[prev_frame]
        
        deltas = []
        for current_vec, prev_vec in zip(current_data, prev_data):
            delta = [round(c - p, 8) for c, p in zip(current_vec, prev_vec)]
            deltas.append(delta)
        
        delta_data[frame] = deltas

    return delta_data

def find_delta_max_min(delta_data):
    delta_max_value = float('-inf')
    delta_min_value = float('inf')
    
    for frame, data in delta_data.items():
        for vector in data:
            delta_max_value = max(delta_max_value, max(vector))
            delta_min_value = min(delta_min_value, min(vector))
    
    delta_max = round_to_nearest_ten(delta_max_value, math.ceil)
    delta_min = round_to_nearest_ten(delta_min_value, math.floor)

    return delta_max, delta_min

def remap_values(value, old_min, old_max, new_min=0, new_max=1):
    return (value - old_min) / (old_max - old_min) * (new_max - new_min) + new_min

def remap_deltas(delta_data, delta_min, delta_max):
    remapped_delta_data = {}
    
    for frame, data in delta_data.items():
        remapped_deltas = []
        for vector in data:
            remapped_vector = [round(remap_values(val, delta_min, delta_max), 8) for val in vector]
            remapped_deltas.append(remapped_vector)
        
        remapped_delta_data[frame] = remapped_deltas

    return remapped_delta_data

def main(obj_name, attribute_name, frame_start, frame_end, output_filepath, delta_output_filepath, remap_output_filepath):
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
    print(f"Overall Max value: {overall_max}")
    print(f"Overall Min value: {overall_min}")

    delta_data = calculate_deltas(all_frames_data)
    write_json(delta_data, delta_output_filepath)
    print(f"Delta data saved to {delta_output_filepath}")

    delta_max, delta_min = find_delta_max_min(delta_data)
    print(f"Delta Max value: {delta_max}")
    print(f"Delta Min value: {delta_min}")

    remapped_delta_data = remap_deltas(delta_data, delta_min, delta_max)
    remap_info = {
        "World Space Remapping": {
            "Min": overall_min,
            "Max": overall_max
        },
        "Delta Space Remapping": {
            "Min": delta_min,
            "Max": delta_max
        }
    }
    write_json(remapped_delta_data, remap_output_filepath)
    remap_info_filepath = remap_output_filepath.replace(".json", "_info.json")
    write_json(remap_info, remap_info_filepath)
    print(f"Remapped delta data saved to {remap_output_filepath}")
    print(f"Remap information saved to {remap_info_filepath}")

# Usage
obj_name = "animcube2"
attribute_name = "colPos"
frame_start = 1
frame_end = 30
output_filepath = "D:/GitHub/openvat/source/output.json"
delta_output_filepath = "D:/GitHub/openvat/source/delta_output.json"
remap_output_filepath = "D:/GitHub/openvat/source/remapped_delta_output.json"

main(obj_name, attribute_name, frame_start, frame_end, output_filepath, delta_output_filepath, remap_output_filepath)
