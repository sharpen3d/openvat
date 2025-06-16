import bpy

class RIGIDBODYTOOLS_PT_multi_editor(bpy.types.Panel):
    bl_label = "Rigid Body Multi-Edit"
    bl_idname = "RIGIDBODYTOOLS_PT_multi_editor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Rigid Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.rigidbody_tools_props

        row = layout.row()
        row.operator("rigidbodytools.add_active", icon="PHYSICS")
        row.operator("rigidbodytools.add_passive", icon="MOD_PHYSICS")

        layout.operator("rigidbodytools.remove", icon="X")

        layout.separator()
        layout.label(text="Batch Settings:")

        layout.prop(props, "type")
        layout.prop(props, "mass")
        layout.prop(props, "friction")
        layout.prop(props, "restitution")
        layout.prop(props, "use_deactivation")
        layout.prop(props, "collision_shape")

        layout.operator("rigidbodytools.apply_settings", icon="CHECKMARK")


class RIGIDBODYTOOLS_OT_add_active(bpy.types.Operator):
    bl_idname = "rigidbodytools.add_active"
    bl_label = "Add Active Rigid Body"
    bl_description = "Add active rigid body to selected objects"

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                if not obj.rigid_body:
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.rigidbody.object_add()
                obj.rigid_body.type = 'ACTIVE'
        return {'FINISHED'}


class RIGIDBODYTOOLS_OT_add_passive(bpy.types.Operator):
    bl_idname = "rigidbodytools.add_passive"
    bl_label = "Add Passive Rigid Body"
    bl_description = "Add passive rigid body to selected objects"

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                if not obj.rigid_body:
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.rigidbody.object_add()
                obj.rigid_body.type = 'PASSIVE'
        return {'FINISHED'}


class RIGIDBODYTOOLS_OT_remove(bpy.types.Operator):
    bl_idname = "rigidbodytools.remove"
    bl_label = "Remove Rigid Body"
    bl_description = "Remove rigid body physics from selected objects"

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.rigid_body:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.rigidbody.object_remove()
        return {'FINISHED'}


class RIGIDBODYTOOLS_OT_apply_settings(bpy.types.Operator):
    bl_idname = "rigidbodytools.apply_settings"
    bl_label = "Apply Rigid Body Settings"
    bl_description = "Apply settings to selected rigid body objects"

    def execute(self, context):
        props = context.scene.rigidbody_tools_props
        for obj in context.selected_objects:
            if obj.rigid_body:
                obj.rigid_body.type = props.type
                obj.rigid_body.mass = props.mass
                obj.rigid_body.friction = props.friction
                obj.rigid_body.restitution = props.restitution
                obj.rigid_body.use_deactivation = props.use_deactivation
                obj.rigid_body.collision_shape = props.collision_shape
        return {'FINISHED'}


class RIGIDBODYTOOLS_Props(bpy.types.PropertyGroup):
    type: bpy.props.EnumProperty(
        name="Rigid Body Type",
        items=[
            ('ACTIVE', "Active", ""),
            ('PASSIVE', "Passive", "")
        ],
        default='ACTIVE'
    )
    mass: bpy.props.FloatProperty(name="Mass", default=1.0, min=0.001)
    friction: bpy.props.FloatProperty(name="Friction", default=0.5, min=0.0, max=1.0)
    restitution: bpy.props.FloatProperty(name="Bounciness", default=0.0, min=0.0, max=1.0)
    use_deactivation: bpy.props.BoolProperty(name="Enable Deactivation", default=True)
    collision_shape: bpy.props.EnumProperty(
        name="Collision Shape",
        items=[
            ('BOX', "Box", ""),
            ('SPHERE', "Sphere", ""),
            ('CAPSULE', "Capsule", ""),
            ('CYLINDER', "Cylinder", ""),
            ('CONE', "Cone", ""),
            ('CONVEX_HULL', "Convex Hull", ""),
            ('MESH', "Mesh", "")
        ],
        default='CONVEX_HULL'
    )


classes = [
    RIGIDBODYTOOLS_PT_multi_editor,
    RIGIDBODYTOOLS_OT_add_active,
    RIGIDBODYTOOLS_OT_add_passive,
    RIGIDBODYTOOLS_OT_remove,
    RIGIDBODYTOOLS_OT_apply_settings,
    RIGIDBODYTOOLS_Props,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rigidbody_tools_props = bpy.props.PointerProperty(type=RIGIDBODYTOOLS_Props)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.rigidbody_tools_props


if __name__ == "__main__":
    register()
