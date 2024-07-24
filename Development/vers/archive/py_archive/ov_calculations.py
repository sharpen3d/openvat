import bpy
import math

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
        else:
            self.report({'ERROR'}, "No active mesh object selected")
        
        return {'FINISHED'}
    
    def calculate_optimal_vat_resolution(self, num_vertices, num_frames):
        total_pixels = num_vertices * num_frames
        
        # Approximate the side length of the square
        approx_side = math.sqrt(total_pixels)
        
        # Find the closest power of 2 less than or equal to approx_side
        def closest_power_of_2(n):
            return 2 ** math.floor(math.log2(n))
        
        width = closest_power_of_2(approx_side)
        height = closest_power_of_2(approx_side)
        
        # Adjust width and height to fit all pixels
        while width * height < total_pixels:
            if width < height:
                width *= 2
            else:
                height *= 2
        
        # Calculate the number of wraps
        num_wraps = math.ceil(num_vertices / width)
        
        return (width, height, num_wraps)

def register():
    bpy.utils.register_class(OBJECT_PT_VAT_Calculator)
    bpy.utils.register_class(OBJECT_OT_CalculateVATResolution)

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_VAT_Calculator)
    bpy.utils.unregister_class(OBJECT_OT_CalculateVATResolution)

if __name__ == "__main__":
    register()
