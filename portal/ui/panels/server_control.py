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
        layout.use_property_split = True
        layout.use_property_decorate = False  # no animation
        scene = context.scene

        # List of connections
        for index, connection in enumerate(scene.portal_connections):
            box = layout.box()
            box.use_property_split = False  # Compact view for the box

            # Main row with name, start/stop button, and remove button
            row = box.row(align=True)  # Align row to reduce padding
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
                depress=connection.running,  # Highlight button if running
            ).uuid = connection.uuid
            row.operator("portal.remove_connection", text="", icon="X").uuid = connection.uuid

            if connection.show_details:
                # Compact view for connection settings
                sub_box = box.column(align=True)  # Aligning columns for compactness
                sub_box.use_property_split = True

                # Change here: make the enum appear side by side
                row = sub_box.row(align=True)  # Create a new row for side-by-side layout
                row.prop(connection, "direction", expand=True)
                sub_box.separator()
                sub_box.prop(connection, "connection_type", text="Connection")

                # Connection settings based on type
                if connection.connection_type == "NAMED_PIPE":
                    sub_box.prop(connection, "name", text="Pipe Name")
                elif connection.connection_type == "MMAP":
                    sub_box.prop(connection, "name", text="MMAP Name")
                    sub_box.prop(connection, "buffer_size", text="Buffer Size (KB)")
                elif connection.connection_type == "WEBSOCKETS":
                    row = sub_box.row(align=True)
                    if connection.direction == "SEND":
                        row.prop(connection, "host", text="Address")
                        row.prop(connection, "port", text="Port")
                    else:
                        row.prop(connection, "port", text="Port")
                        row.prop(connection, "is_external", text="Remote")
                elif connection.connection_type == "UDP":
                    row = sub_box.row(align=True)
                    if connection.direction == "SEND":
                        row.prop(connection, "host", text="Address")
                        row.prop(connection, "port", text="Port")
                    else:
                        row.prop(connection, "port", text="Port")
                        row.prop(connection, "is_external", text="Remote")

                if connection.direction == "RECV":
                    sub_box.prop(connection, "data_type", text="Data Type")
                    if connection.data_type == "Custom":
                        # Handler with prop_search and file browser icon in a compact row
                        row = sub_box.row(align=True)
                        row.prop_search(
                            connection, "custom_handler", bpy.data, "texts", text="Handler"
                        )
                        row.operator(
                            "portal.load_file_to_text_block",
                            text="",
                            icon="FILEBROWSER",
                        ).uuid = connection.uuid

                        if connection.custom_handler:
                            sub_box.operator(
                                "portal.open_text_editor", text="Open in Text Editor"
                            ).text_name = connection.custom_handler
                else:
                    sub_box.prop(connection, "send_data", text="Send Data")

                sub_box.separator()
                sub_box.prop(connection, "event_timer")

        layout.operator("portal.add_connection", text="Add New Connection", icon="ADD")


def register():
    bpy.utils.register_class(PORTAL_PT_ServerControl)


def unregister():
    bpy.utils.unregister_class(PORTAL_PT_ServerControl)
