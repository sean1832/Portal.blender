import bpy
import time
import uuid

class PORTAL_OT_OpenDictItemEditor(bpy.types.Operator):
    bl_idname = "portal.dict_item_editor"
    bl_label = "Dictionary Item Editor"
    bl_description = "The dictionary item editor"
    uuid: bpy.props.StringProperty()  # type: ignore

    def invoke(self, context, event):
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )
        if not connection:
            self.report({"ERROR"}, "Connection not found!")
            return {"CANCELLED"}
        # run operator in modal state, open a dialog to edit the dictionary item
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )
        if not connection:
            return
        row = layout.row()
        row.template_list(
            "PORTAL_UL_DictItems",
            "",
            connection,
            "dict_items",
            connection,
            "dict_items_index",
            rows=5,
        )
        col = row.column(align=True)
        col.operator("portal.add_dict_item", icon="ADD", text="").uuid = self.uuid
        col.operator("portal.remove_dict_item", icon="REMOVE", text="").uuid = self.uuid

        if connection.dict_items:
            item = connection.dict_items[connection.dict_items_index]
            box = layout.box()
            box.prop(item, "key")
            box.prop(item, "value_type")

            # BASIC TYPES
            if item.value_type == "STRING":
                box.prop(item, "value_string")
            elif item.value_type == "BOOL":
                box.prop(item, "value_bool")
            elif item.value_type == "NUMBER":
                box.prop(item, "value_number")
            elif item.value_type == "SCENE_OBJECT":
                box.prop(item, "value_scene_object")

            # ADVANCED TYPES
            elif item.value_type == "PROPERTY_PATH":
                box.prop(item, "value_property_path", text="Property Path")
            elif item.value_type == "TIMESTAMP":
                box.label(text=str(int(time.time() * 1000)))
            elif item.value_type == "UUID":
                box.prop(item, "value_uuid", text="UUID")

    def execute(self, context):
        return {"FINISHED"}


class PORTAL_UL_DictItems(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.label(text=item.key)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class PORTAL_OT_AddDictItem(bpy.types.Operator):
    bl_idname = "portal.add_dict_item"
    bl_label = "Add Dictionary Item"
    bl_description = "Add a new dictionary item"
    uuid: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )
        if not connection:
            self.report({"ERROR"}, "Connection not found!")
            return {"CANCELLED"}
        connection.dict_items.add()
        connection.dict_item_index = len(connection.dict_items) - 1
        index = connection.dict_item_index
        connection.dict_items[index].key = f"key-{len(connection.dict_items)}"
        connection.dict_items[index].value_uuid = str(uuid.uuid4())

        return {"FINISHED"}


class PORTAL_OT_RemoveDictItem(bpy.types.Operator):
    bl_idname = "portal.remove_dict_item"
    bl_label = "Remove Dictionary Item"
    bl_description = "Remove the selected dictionary item"
    uuid: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )
        if not connection:
            self.report({"ERROR"}, "Connection not found!")
            return {"CANCELLED"}
        if not connection.dict_items:
            return {"CANCELLED"}
        connection.dict_items.remove(connection.dict_items_index)
        connection.dict_items_index = min(connection.dict_items_index, len(connection.dict_items) - 1)
        return {"FINISHED"}

def register():
    bpy.utils.register_class(PORTAL_OT_OpenDictItemEditor)
    bpy.utils.register_class(PORTAL_UL_DictItems)
    bpy.utils.register_class(PORTAL_OT_AddDictItem)
    bpy.utils.register_class(PORTAL_OT_RemoveDictItem)

def unregister():
    bpy.utils.unregister_class(PORTAL_OT_OpenDictItemEditor)
    bpy.utils.unregister_class(PORTAL_UL_DictItems)
    bpy.utils.unregister_class(PORTAL_OT_AddDictItem)
    bpy.utils.unregister_class(PORTAL_OT_RemoveDictItem)