import bpy
import bmesh
import math
import os

bl_info = {
    "name": "OpenVAT",
    "blender": (2, 80, 0),
    "category": "Object",
}

class OBJECT_PT_VAT_Calculator(bpy.types.Panel):
    bl_idname = "OBJECT_PT_vat_calculator"
    bl_label = "VAT Calculator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tools'

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.type == 'MESH':
            layout.label(text=f"Active Object: {obj.name}")
            layout.label(text=f"Vertex Count: {len(obj.data.vertices)}")
            layout.label(text=f"Frame Range: {context.scene.frame_start} - {context.scene.frame_end}")
            
            layout.operator("object.calculate_vat_resolution", text="Calculate VAT Resolution")
        else:
            layout.label(text="No active mesh object selected")

class OBJECT_OT_CalculateVATResolution(bpy.types.Operator):
    bl_idname = "object.calculate_vat_resolution"
    bl_label = "Calculate VAT Resolution"

    def execute(self, context):
        obj = context.object
        if obj and obj.type == 'MESH':
            num_vertices = len(obj.data.vertices)
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end
            num_frames = frame_end - frame_start + 1

            width, height, num_wraps = self.calculate_optimal_vat_resolution(num_vertices, num_frames)
            
            self.report({'INFO'}, f"Resolution: {width} x {height}, Number of wraps: {num_wraps}")
            
            # Proceed to setup the proxy scene
            self.setup_proxy_scene(context, obj, num_frames, width, height, num_wraps)
        else:
            self.report({'ERROR'}, "No active mesh object selected")
        
        return {'FINISHED'}
    
    def calculate_optimal_vat_resolution(self, num_vertices, num_frames):
        total_pixels = num_vertices * num_frames
        approx_side = math.sqrt(total_pixels)

        def closest_power_of_2(n):
            return 2 ** math.ceil(math.log2(n))
        
        width = closest_power_of_2(approx_side)
        height = closest_power_of_2(approx_side)
        
        while width * height < total_pixels:
            if width < height:
                width *= 2
            else:
                height *= 2
        
        num_wraps = math.ceil(num_vertices / width)
        
        return (width, height, num_wraps)

    def setup_proxy_scene(self, context, obj, num_frames, width, height, num_wraps):
        original_scene = context.scene
        original_scene_name = original_scene.name
        
        bpy.ops.scene.new(type='NEW')
        proxy_scene = bpy.context.scene
        proxy_scene.name = f"{obj.name}_proxy_scene"
        
        proxy_scene.frame_end = original_scene.frame_end
        proxy_scene.frame_start = original_scene.frame_start
        
        proxy_obj = obj.copy()
        proxy_obj.data = obj.data.copy()
        proxy_scene.collection.objects.link(proxy_obj)
        
        bpy.context.view_layer.objects.active = proxy_obj
        proxy_obj.select_set(True)
        
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        for mod in proxy_obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        
        self.create_uv_map(proxy_obj, width, height, num_frames)
        
        bpy.ops.object.modifier_add(type='NODES')
        proxy_obj.modifiers[-1].node_group = bpy.data.node_groups["ov_vat-decoder-ws"]
        proxy_obj.modifiers["GeometryNodes"]["Socket_2_attribute_name"] = "VAT_UV"
        proxy_obj.modifiers["GeometryNodes"]["Socket_6"] = num_frames
        proxy_obj.modifiers["GeometryNodes"]["Socket_7"] = height
        
        self.setup_vat_scene(proxy_obj, obj.name, original_scene_name, num_frames, width, height, num_wraps)
        
        bpy.context.window.scene = proxy_scene
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        
    def create_uv_map(self, obj, screen_width, screen_height, frames):
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

    def setup_vat_scene(self, proxy_obj, obj_name, original_scene_name, num_frames, width, height, num_wraps):
        bpy.ops.scene.new(type='NEW')
        vat_scene = bpy.context.scene
        vat_scene.name = f"{obj_name}_vat"
        
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
        vat_scene.render.image_settings.compression = 0
        vat_scene.render.dither_intensity = 0
        vat_scene.render.use_compositing = False
        vat_scene.render.use_sequencer = False
        vat_scene.eevee.taa_render_samples = 1
        
        output_dir = os.path.join(os.path.dirname(bpy.data.filepath), "openVAT", vat_scene.name)
        os.makedirs(output_dir, exist_ok=True)
        self.render_vat_scene(vat_scene, 1, output_dir)
        vat_scene.render.use_compositing = True
        self.setup_compositing(vat_scene, output_dir, vat_scene.name, proxy_obj)
        self.setup_vat_tracker(vat_scene, obj_name, num_frames, width, height, num_wraps)
        self.render_vat_scene(vat_scene, num_frames, output_dir)

        
    def render_vat_scene(self, vat_scene, num_frames, output_dir):
        start_frame = vat_scene.frame_start
        end_frame = vat_scene.frame_end
        output_path = os.path.join(output_dir, f"{vat_scene.name}.png")

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
        
    def setup_compositing(self, vat_scene, output_dir, scene_name, proxy_obj):
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
        
        proxy_obj.modifiers["GeometryNodes"]["Socket_9"] = image

    def setup_vat_tracker(self, vat_scene, obj_name, num_frames, width, height, num_wraps):
        bpy.ops.mesh.primitive_plane_add(location=(0, 5, 0))
        tracker_plane = bpy.context.object
        tracker_plane.name = f"{obj_name}_vat-tracking"
        
        bpy.ops.object.modifier_add(type='NODES')
        tracker_plane.modifiers["GeometryNodes"].node_group = bpy.data.node_groups["ov_calculate-position"]
        tracker_plane.modifiers["GeometryNodes"]["Socket_4"] = bpy.data.objects[obj_name]
        tracker_plane.modifiers["GeometryNodes"]["Socket_2"] = num_frames
        tracker_plane.modifiers["GeometryNodes"]["Socket_10"] = num_wraps
        tracker_plane.modifiers["GeometryNodes"]["Socket_8"] = width
        tracker_plane.modifiers["GeometryNodes"]["Socket_9"] = height

    def export_proxy_model(self, context, proxy_obj, output_dir):
        proxy_obj.modifiers[-1]["Input_9"] = bpy.data.images.load(os.path.join(output_dir, f"{proxy_obj.name}.png"))
        bpy.ops.export_scene.fbx(filepath=os.path.join(output_dir, f"{proxy_obj.name}.fbx"))

def register():
    bpy.utils.register_class(OBJECT_PT_VAT_Calculator)
    bpy.utils.register_class(OBJECT_OT_CalculateVATResolution)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_VAT_Calculator)
    bpy.utils.unregister_class(OBJECT_OT_CalculateVATResolution)

if __name__ == "__main__":
    register()
