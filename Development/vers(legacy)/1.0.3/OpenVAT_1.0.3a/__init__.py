"""
Title: OpenVAT Encoder
Description: Encode and preview vertex animation textures
Author: Luke Stilson
Date: 2025-04-29
Version: 1.0.3a

"""

import bpy

from . import props, operators, panels

classes = []
classes.extend(props.classes)
classes.extend(panels.classes)
classes.extend(operators.classes)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vat_settings = bpy.props.PointerProperty(type=props.VATSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.vat_settings


if __name__ == "__main__":
    register()