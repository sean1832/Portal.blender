# pyright: reportInvalidTypeForm=false
import bpy


class DictionaryItem(bpy.types.PropertyGroup):
    key: bpy.props.StringProperty(name="Key", default="")

    value_type: bpy.props.EnumProperty(
        name="Value Type",
        items=[
            ("STRING", "String", "String value"),
            ("NUMBER", "Number", "Numerical value"),
            ("BOOL", "Boolean", "Boolean value"),
            ("SCENE_OBJECT", "Scene Object", "Scene object value"),
            ("PROPERTY_PATH", "Property Path", "Property path value"),
            ("TIMESTAMP", "Timestamp", "Timestamp value"),
            ("UUID", "UUID", "UUID value"),
        ],
        default="STRING",
    )
    
    value_string: bpy.props.StringProperty(name="Value", default="")
    value_number: bpy.props.FloatProperty(name="Value", default=0.0)
    value_bool: bpy.props.BoolProperty(name="Value", default=False)
    value_scene_object: bpy.props.PointerProperty(name="Value", type=bpy.types.Object)

    value_property_path: bpy.props.StringProperty(name="Value", default="")
    value_uuid: bpy.props.StringProperty(name="Value", default="")

def register():
    bpy.utils.register_class(DictionaryItem)

def unregister():
    bpy.utils.unregister_class(DictionaryItem)

