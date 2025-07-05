import bpy
import os
import bmesh
from . import utils, core

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

class OBJECT_OT_CalculateVATResolution(bpy.types.Operator):
    bl_idname = "object.calculate_vat_resolution"
    bl_label = "Calculate VAT Resolution"
    bl_description = "Export a UV-Based Vertex Animation Texture, sidecar data and compatible model to the defined Export location"

    def execute(self, context):
        settings = context.scene.vat_settings
        outDir = bpy.path.abspath(bpy.context.scene.vat_settings.vat_output_directory)
        blend_filepath = bpy.data.filepath
        export_directory = bpy.path.abspath(context.scene.vat_settings.vat_output_directory)
        selected_temp = None

        # Validate custom attributes
        if settings.encode_type == 'CUSTOM':
            custom_obj = context.view_layer.objects.active
            attr_names = [settings.custom_attr_1, settings.custom_attr_2, settings.custom_attr_3]
        
            missing = []
            depsgraph = context.evaluated_depsgraph_get()
            eval_obj = custom_obj.evaluated_get(depsgraph)
            eval_mesh = eval_obj.to_mesh()

            try:
                attr_names_mesh = [a.name for a in eval_mesh.attributes]
                for name in attr_names:
                    if name != "NONE" and name not in attr_names_mesh:
                        missing.append(name)
            finally:
                eval_obj.to_mesh_clear()

            if missing:
                self.report({'ERROR'}, f"Missing attributes: {', '.join(missing)}. Please rescan.")
                return {'CANCELLED'}

        if settings.proxy_method == 'START_FRAME':
            
            context.scene.frame_current = context.scene.frame_start
        
        if settings.proxy_method == 'SELECTED_OBJECT':
            selected_objects = bpy.context.selected_objects
            active_object = bpy.context.active_object
            if len(selected_objects) != 2 or active_object not in selected_objects:
                print("Exactly 2 objects must be selected, including the active one.")
                return {'FINISHED'}
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
        
        if settings.encode_type != 'CUSTOM':
            if settings.encode_target == 'COLLECTION_COMBINE': # Collection target only valid when collection_mode is true
                collection_mode = True
                collection_target = settings.vat_collection.name

        core.create_geo_nodes_bake(use_collection=collection_mode, collection_name=collection_target)
        obj = context.view_layer.objects.active
        obj_name = obj.name

        # Perform Normal-Safe Edge Split on new object

        if settings.vat_normal_encoding != 'NONE':
            if settings.rip_edges:
                utils.rip_hard_edges(obj)
        
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
                utils.apply_modifier(temp_obj, modifier)
        else:
            temp_obj = selected_temp
        
        if temp_obj == None:
            return {'FINISHED'}
        
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        
        # Create output directories (for JSON)
        if not os.path.exists(export_directory):
            os.makedirs(export_directory)
        
        # Name json based on target object
        output_rename = obj_name.replace("_ovbake", "")
        existing_obj = bpy.data.objects.get(output_rename + "_vat")
        if existing_obj:
            bpy.data.objects.remove(existing_obj)
        
        object_directory = os.path.join(export_directory, f"{output_rename}_vat")
        
        if not os.path.exists(object_directory):
            os.makedirs(object_directory)
        output_filepath = os.path.join(object_directory, f"{output_rename}-remap_info.json")
        
        # Saturation sampling output
        remap_output_filepath = os.path.join(object_directory, f"{output_rename}-remap_info.json")

        # Ensure the required node groups are available
        utils.ensure_node_group("ov_generated-pos")
        utils.ensure_node_group("ov_vat-decoder-vs")
        utils.ensure_node_group("ov_calculate-position-vs")
        
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
            utils.make_remap_data(obj_name, attribute_name, frame_start, frame_end, output_filepath, remap_output_filepath, "")

            min_x, min_y, min_z, max_x, max_y, max_z = utils.read_remap_info(remap_output_filepath, attribute_name)
            context.scene['min_x'] = min_x
            context.scene['min_y'] = min_y
            context.scene['min_z'] = min_z
            context.scene['max_x'] = max_x
            context.scene['max_y'] = max_y
            context.scene['max_z'] = max_z

        else:
            attr_r = settings.custom_attr_1
            attr_g = settings.custom_attr_2
            attr_b = settings.custom_attr_3

            utils.make_custom_data(obj_name, [attr_r, attr_g, attr_b], frame_start, frame_end, output_filepath, remap_output_filepath)
            attrs = [
                settings.custom_attr_1,
                settings.custom_attr_2,
                settings.custom_attr_3,
            ]

            min_r, min_g, min_b, max_r, max_g, max_b = utils.read_custom_info(remap_output_filepath, attrs)

            context.scene['min_x'] = min_r
            context.scene['min_y'] = min_g
            context.scene['min_z'] = min_b
            context.scene['max_x'] = max_r
            context.scene['max_y'] = max_g
            context.scene['max_z'] = max_b
        
        num_vertices = len(obj.data.vertices)
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        num_frames = frame_end - frame_start + 1
        context.scene.frame_current = frame_start
        
        # Encode Normals
        if settings.encode_type == 'CUSTOM':
            pack_normals = False
            if settings.use_single_row:
                width = num_vertices
                height = num_frames
                num_wraps = 1
            else:
                width, height, num_wraps = utils.calculate_optimal_vat_resolution(num_vertices, num_frames)   
        elif settings.vat_normal_encoding == 'PACKED':
            if settings.use_single_row:
                width = num_vertices
                height = num_frames * 2
                num_wraps = 1
            else:
                width, height, num_wraps = utils.calculate_packed_vat_resolution(num_vertices, num_frames)   
        else:
            if settings.use_single_row:
                width = num_vertices
                height = num_frames
                num_wraps = 1
            else:
                width, height, num_wraps = utils.calculate_optimal_vat_resolution(num_vertices, num_frames)   
        
        # Store name for use after obj is deleted
        obj_name = obj.name
        
        # obj (temp) is deleted on success of the following
        core.setup_proxy_scene(obj, num_frames, width, height, num_wraps, temp_obj, pack_normals, frame_start)
        
        # Clean up creation data
        if context.scene.vat_settings.vat_cleanup_enabled:
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

class OBJECT_OT_ScanFloatPointAttributes(bpy.types.Operator):
    bl_idname = "object.scan_attributes"
    bl_label = "Scan Float Attributes"
    bl_description = "Scan the active object for float point attributes"

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "No valid mesh selected")
            return {'CANCELLED'}

        # NEW: safe evaluated attribute scan
        items = utils.get_evaluated_point_float_attributes(context)

        if not items:
            items = [("NONE", "None", "")]

        # Pre-clear selection to make enums update
        settings = context.scene.vat_settings
        settings.custom_attr_1 = "NONE"
        settings.custom_attr_2 = "NONE"
        settings.custom_attr_3 = "NONE"

        # Cache
        utils._openvat_enum_cache["1"] = items
        utils._openvat_enum_cache["2"] = items
        utils._openvat_enum_cache["3"] = items

        # Auto-assign
        valid_names = [i[0] for i in items if i[0] != "NONE"]
        if len(valid_names) > 0:
            settings.custom_attr_1 = valid_names[0]
        if len(valid_names) > 1:
            settings.custom_attr_2 = valid_names[1]
        if len(valid_names) > 2:
            settings.custom_attr_3 = valid_names[2]

        self.report({'INFO'}, f"Found {len(valid_names)} attribute(s)")
        return {'FINISHED'}




classes = [OBJECT_OT_CalculateVATResolution, OBJECT_OT_OpenOutputDirectory, OBJECT_OT_ScanFloatPointAttributes]