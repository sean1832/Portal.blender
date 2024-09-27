import bpy

# Main panel to show connections
class PORTAL_PT_ServerControl(bpy.types.Panel):
    bl_label = "Portal Server"
    bl_idname = "PORTAL_PT_ServerControl"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Portal"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # List of connections
        for index, connection in enumerate(scene.portal_connections):
            box = layout.box()

            # Main row with name, start/stop button, and remove button
            row = box.row()
            row.prop(
                connection,
                "show_details",
                icon="TRIA_DOWN" if connection.show_details else "TRIA_RIGHT",
                emboss=False,
                text="",
            )
            row.prop(connection, "name", text="")
            row.operator(
                "portal.toggle_server",
                text="Start" if not connection.running else "Stop",
                icon="PLAY" if not connection.running else "PAUSE",
                depress=True if connection.running else False,  # Highlight button if running
            ).uuid = connection.uuid
            row.operator("portal.remove_connection", text="", icon="X").uuid = connection.uuid

            if connection.show_details:
                # split layout into left and right for detailed settings
                split = box.split(factor=0.35)
                col_left = split.column()
                col_right = split.column()

                # Connection settings based on type
                col_left.label(text="Connection")
                col_right.prop(connection, "connection_type", text="")
                if connection.connection_type == "NAMED_PIPE":
                    col_left.label(text="Pipe Name")
                    col_right.prop(connection, "name", text="")
                elif connection.connection_type == "MMAP":
                    col_left.label(text="MMAP Name")
                    col_right.prop(connection, "name", text="")
                    col_left.label(text="Buffer Size (KB)")
                    col_right.prop(connection, "buffer_size", text="")
                elif connection.connection_type == "WEBSOCKETS":
                    col_left.label(text="Port")
                    col_right.prop(connection, "port", text="")
                    col_left.label(text="Remote")
                    col_right.prop(connection, "is_external", text="")
                elif connection.connection_type == "UDP":
                    col_left.label(text="Port")
                    col_right.prop(connection, "port", text="")
                    col_left.label(text="Remote")
                    col_right.prop(connection, "is_external", text="")

                col_left.label(text="Data Type")
                col_right.prop(connection, "data_type", text="")

                if connection.data_type == "Custom":
                    col_left.label(text="Handler")
                    # Create a row with a split layout to have prop_search and button side by side
                    row = col_right.row(align=True)
                    split = row.split(factor=0.85)  # Adjust the factor to control the width ratio

                    split.prop_search(connection, "custom_handler", bpy.data, "texts", text="")

                    # Load file button on the right
                    split.operator(
                        "portal.load_file_to_text_block",
                        text="",
                        icon="FILEBROWSER",
                    ).uuid = connection.uuid

                    if connection.custom_handler:
                        col_right.operator(
                            "portal.open_text_editor", text="Open in Text Editor"
                        ).text_name = connection.custom_handler

                box.prop(connection, "event_timer")

        layout.operator("portal.add_connection", text="Add New Connection", icon="ADD")


def register():
    bpy.utils.register_class(PORTAL_PT_ServerControl)

def unregister():
    bpy.utils.unregister_class(PORTAL_PT_ServerControl)