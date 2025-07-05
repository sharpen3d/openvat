import bpy
import os
from . import utils
from . import operators

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
        
        row = layout.row()
        layout.separator()
        row = layout.row()
        row.label(text="Vertex Data", icon='RNA')
        row.prop(settings, "encode_type", text="")
        
        if settings.encode_type == 'DEFAULT':
            row = layout.row()
            row.label(text="Vertex Position", icon="EMPTY_ARROWS")
            grid = layout.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
            grid.label(text="Deformation Basis")
            grid.prop(settings, "proxy_method", text="")
            row = layout.row(align=True)
            row.label(text="Transform")
            row.prop(settings, "vat_transform", expand=True)
            layout.separator()
            row = layout.row()
            row.label(text="Vertex Normals", icon='NORMALS_VERTEX')
            row = layout.row()
            row.prop(settings, "vat_normal_encoding", text="")

            layout.separator()
            row = layout.row()
            row.label(text="Mesh Settings", icon="SETTINGS")

            row = layout.row()
            row.prop(settings, "clean_mesh", text="Strip Vertex Data", toggle=True) 
            row = layout.row()
            row.prop(settings, "rip_edges", toggle=True)
       
        else:
            box = layout.box()
            box.operator("object.scan_attributes", text="Scan For Attributes", icon='VIEWZOOM')
            box.prop(settings, "custom_attr_1", text="R Channel")
            box.prop(settings, "custom_attr_2", text="G Channel")
            box.prop(settings, "custom_attr_3", text="B Channel")

            layout.separator()
            row = layout.row()
            row.label(text="Mesh Settings", icon="SETTINGS")

            row = layout.row()
            row.prop(settings, "clean_mesh", text="Strip Vertex Data", toggle=True) 
            row = layout.row()
            row.prop(settings, "rip_edges", toggle=True)
        
# Output Settings - relating to data being exported      
class OBJECT_PT_VAT_OUTPUT(bpy.types.Panel):
    bl_idname = "OBJECT_PT_vat_output"
    bl_label = "OpenVAT Output"
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
        row = layout.row()
        row.prop(settings, "use_single_row", toggle=True)
        if settings.image_format == 'EXR32':
            row = layout.row()
            row.prop(settings, "no_remap", text="Use Absolute Values", toggle=True)
        box = layout.box()
        row = box.row()
        row.prop(settings, "show_encoding_info", icon="INFO_LARGE", emboss=False)

        if settings.show_encoding_info:
            if settings.encode_target == "ACTIVE_OBJECT":
                num_vertices = len(obj.data.vertices)
                max_verts = utils.get_virtual_ripped_vertex_count(obj)
            else:
                num_vertices = 0
                max_verts = 0
                if settings.vat_collection != None:
                    if settings.vat_collection:
                        for child_obj in settings.vat_collection.all_objects:
                            if child_obj.type == 'MESH':
                                num_vertices += len(child_obj.data.vertices)
                                max_verts += utils.get_virtual_ripped_vertex_count(child_obj)
                    
            num_frames = scene.frame_end - scene.frame_start + 1
            
            # Determine resolution
            if settings.use_single_row and settings.encode_type == 'DEFAULT':
                width = num_vertices 
                height = num_frames * (2 if settings.vat_normal_encoding == 'PACKED' else 1)
                maxwidth = max_verts 
                maxheight = num_frames * (2 if settings.vat_normal_encoding == 'PACKED' else 1)
            else:
                if settings.vat_normal_encoding == 'PACKED' and bpy.context.scene.vat_settings.encode_type == 'DEFAULT':
                    width, height, _ = utils.calculate_packed_vat_resolution(num_vertices, num_frames)
                    maxwidth, maxheight, _ = utils.calculate_packed_vat_resolution(max_verts, num_frames)
                else:
                    width, height, _ = utils.calculate_optimal_vat_resolution(num_vertices, num_frames)
                    maxwidth, maxheight, _ = utils.calculate_optimal_vat_resolution(max_verts, num_frames)

            # Encode target info
            if settings.encode_target != "ACTIVE_OBJECT":
                box = layout.box()
                box.label(text=f"Encode Target: {settings.vat_collection.name}", icon='OUTLINER_COLLECTION')
            else:
                if settings.vat_collection is not None:
                    box = layout.box()
                    box.label(text=f"Encode Target: {obj.name}", icon='MESH_DATA')

            row = box.row()
            row.label(text=f"Total Frames: {num_frames}", icon='ANIM')

            # Edge split / range check
            use_range = settings.vat_normal_encoding != 'NONE' and settings.rip_edges

            if use_range:
                box.row().label(text="Estimated Min-Max (Edge-split Potential)", icon='INFO_LARGE')
                box.row().label(text=f"Vertices: {num_vertices} - {max_verts}", icon='VERTEXSEL')
            else:
                box.row().label(text=f"Vertices: {num_vertices}", icon='VERTEXSEL')

            # Resolution reporting
            if settings.encode_target != "COLLECTION_BATCH":
                label = f"Resolution: {width} x {height}" if not use_range else f"Resolution: {width} x {height} - {maxwidth} x {maxheight}"
                row = box.row()
                row.label(text=label, icon='FILE_IMAGE' if use_range else 'IMAGE_DATA')
                if settings.use_single_row:
                    row = box.row()
                    row.label(text="Single Row Mode Enabled", icon='SEQ_LUMA_WAVEFORM')
            else:
                row = box.row()
                row.label(text="Resolution calculated per batch object", icon="OUTLINER_OB_IMAGE")
                

classes = [OBJECT_PT_VAT_OPTIONS, OBJECT_PT_VAT_OUTPUT]