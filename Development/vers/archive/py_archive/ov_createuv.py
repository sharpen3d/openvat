import bpy
import bmesh

def create_uv_map(obj, frames):
    # Get the screen resolution
    screen_width, screen_height = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y

    # Switch to Edit mode and get the bmesh representation of the object
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    # Create a new UV layer
    uv_layer = bm.loops.layers.uv.new("VAT_UV")

    # Create a custom data layer for storing original vertex indices
    index_layer = bm.verts.layers.int.new("index_orig")

    # Store original vertex indices
    for i, vert in enumerate(bm.verts):
        vert[index_layer] = i

    # Sort vertices based on original indices in descending order
    sorted_verts = sorted(bm.verts, key=lambda v: v[index_layer], reverse=True)

    # Calculate the number of vertices
    num_verts = len(sorted_verts)

    # Assign UV coordinates based on sorted vertex order
    for i, vert in enumerate(sorted_verts):
        # Calculate the UV position
        uv_x = (i % screen_width) / screen_width
        uv_y = 1.0 - ((i // screen_width) * frames) / screen_height  # Invert Y axis and space lines by frames

        for loop in vert.link_loops:
            loop[uv_layer].uv = (uv_x, uv_y)

    # Update the mesh with the new UV map
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Ensure the object has the new UV map set as active
    obj.data.uv_layers.active_index = len(obj.data.uv_layers) - 1

# Example usage
obj = bpy.context.object
frames = 24  # Specify the number of frames to move down per line wrap
create_uv_map(obj, frames)
                