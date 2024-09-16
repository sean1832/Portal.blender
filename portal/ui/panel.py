import queue

import bpy

from ..handlers.string_handler import StringHandler
from ..utils.managers import get_server_manager, remove_server_manager

MODAL_OPERATORS = {}


# Custom property group to hold connection properties
class PortalConnection(bpy.types.PropertyGroup):
    connection_type: bpy.props.EnumProperty(
        name="Connection Type",
        description="Choose the type of connection",
        items=[
            ("NAMED_PIPE", "Named Pipe", "Local pipe stream"),
            ("MMAP", "Memory Mapped File", "Local memory-mapped file"),
            ("WEBSOCKETS", "WebSockets", "Local / Remote WebSockets"),
            ("UDP", "UDP", "Local / Remote UDP"),
        ],
        default="NAMED_PIPE",
    )  # type: ignore
    name: bpy.props.StringProperty(name="Connection Name", default="testpipe")  # type: ignore
    port: bpy.props.IntProperty(name="Port", default=6000)  # type: ignore
    is_external: bpy.props.BoolProperty(name="Listen Remote", default=False)  # type: ignore
    buffer_size: bpy.props.IntProperty(name="Buffer Size (KB)", default=1024)  # type: ignore
    data_type: bpy.props.EnumProperty(
        name="Data Type",
        items=[
            ("Mesh", "Mesh", "Receive data as mesh"),
            ("Camera", "Camera", "Receive data as camera"),
            ("Custom", "Custom", "Handle data with custom handler"),
        ],
        default="Mesh",
    )  # type: ignore
    event_timer: bpy.props.FloatProperty(name="Interval (sec)", default=0.01, min=0.001, max=1.0)  # type: ignore
    running: bpy.props.BoolProperty(name="Running", default=False)  # type: ignore
    show_details: bpy.props.BoolProperty(name="Show Details", default=True)  # type: ignore


# Operator to add new connection
class PORTAL_OT_AddConnection(bpy.types.Operator):
    bl_idname = "portal.add_connection"
    bl_label = "Add New Connection"
    bl_description = "Add a new connection"

    def execute(self, context):
        # Check if there are any existing connections
        connections = context.scene.portal_connections
        new_connection = connections.add()
        new_connection.name = f"channel-{len(connections)}"
        new_connection.port = 6000 + len(connections) - 1

        if len(connections) > 1:
            # If there's at least one existing connection, use the same connection type as the last one
            last_connection = connections[-2]  # Get the last existing connection
            new_connection.connection_type = last_connection.connection_type
            new_connection.data_type = last_connection.data_type
        return {"FINISHED"}


# Operator to remove selected connection
class PORTAL_OT_RemoveConnection(bpy.types.Operator):
    bl_idname = "portal.remove_connection"
    bl_label = "Remove Selected Connection"
    bl_description = "Remove the selected connection"
    index: bpy.props.IntProperty()  # type: ignore

    def execute(self, context):
        global MODAL_OPERATORS
        connection = context.scene.portal_connections[self.index]
        
        # Check if the server is running and stop it before removing the connection
        if connection.running:
            server_manager = get_server_manager(connection.connection_type, self.index)
            if server_manager and server_manager.is_running():
                server_manager.stop_server()
                connection.running = False
                remove_server_manager(self.index)

            # Cancel the modal operator if it is running
            if self.index in MODAL_OPERATORS:
                modal_operator = MODAL_OPERATORS[self.index]
                modal_operator.cancel(context)

        # Now safe to remove the connection
        context.scene.portal_connections.remove(self.index)
        return {"FINISHED"}


# Operator to start/stop server
class PORTAL_OT_ToggleServer(bpy.types.Operator):
    bl_idname = "portal.toggle_server"
    bl_label = "Start/Stop Server"
    bl_description = "Start or stop the selected server"
    index: bpy.props.IntProperty()  # type: ignore

    def execute(self, context):
        connection = context.scene.portal_connections[self.index]
        server_manager = get_server_manager(connection.connection_type, self.index)

        if connection.running:
            # Stop the server if it's running
            if server_manager and server_manager.is_running():
                server_manager.stop_server()
                connection.running = False
                remove_server_manager(self.index)  # Remove the manager from SERVER_MANAGERS
        else:
            # Start the server if it's not running
            if server_manager and not server_manager.is_running():
                server_manager.start_server()
                # Start a unique modal operator for this instance
                bpy.ops.wm.modal_operator("INVOKE_DEFAULT", index=self.index)
                connection.running = True
        return {"FINISHED"}


# Modal operator for server event handling
class ModalOperator(bpy.types.Operator):
    bl_idname = "wm.modal_operator"
    bl_label = "Listener Modal Operator"
    bl_description = "Modal operator to handle server events"

    index: bpy.props.IntProperty()  # type: ignore

    def __init__(self):
        self._timer = None

    def modal(self, context, event):
        # Check if the connection still exists
        if self.index >= len(context.scene.portal_connections):
            # Connection has been removed; cancel the modal operator
            self.cancel(context)
            return {"CANCELLED"}

        connection = context.scene.portal_connections[self.index]
        server_manager = get_server_manager(connection.connection_type, self.index)

        if server_manager and server_manager.is_shutdown():
            self.cancel(context)
            return {"CANCELLED"}

        if event.type == "TIMER" and connection.running:
            while not server_manager.data_queue.empty():
                try:
                    data = server_manager.data_queue.get_nowait()
                    StringHandler.handle_string(
                        data, connection.data_type, self.index, connection.name
                    )
                except queue.Empty:
                    break
        return {"PASS_THROUGH"}

    def execute(self, context):
        global MODAL_OPERATORS
        connection = context.scene.portal_connections[self.index]
        self._timer = context.window_manager.event_timer_add(
            connection.event_timer, window=context.window
        )
        context.window_manager.modal_handler_add(self)

        # Store this modal operator in the global dictionary
        MODAL_OPERATORS[self.index] = self

        return {"RUNNING_MODAL"}

    def cancel(self, context):
        global MODAL_OPERATORS
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        self._timer = None

        # Remove the modal operator from the dictionary
        if self.index in MODAL_OPERATORS:
            del MODAL_OPERATORS[self.index]

        return {"CANCELLED"}


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
            ).index = index
            row.operator("portal.remove_connection", text="", icon="X").index = index

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

                box.prop(connection, "event_timer")

        layout.operator("portal.add_connection", text="Add New Connection", icon="ADD")


# Register properties, classes, and UI panel
def register_ui():
    bpy.utils.register_class(PortalConnection)
    bpy.utils.register_class(PORTAL_OT_AddConnection)
    bpy.utils.register_class(PORTAL_OT_RemoveConnection)
    bpy.utils.register_class(PORTAL_OT_ToggleServer)
    bpy.utils.register_class(ModalOperator)
    bpy.utils.register_class(PORTAL_PT_ServerControl)

    bpy.types.Scene.portal_connections = bpy.props.CollectionProperty(type=PortalConnection)
    bpy.types.Scene.portal_active_connection_index = bpy.props.IntProperty()


def unregister_ui():
    bpy.utils.unregister_class(PortalConnection)
    bpy.utils.unregister_class(PORTAL_OT_AddConnection)
    bpy.utils.unregister_class(PORTAL_OT_RemoveConnection)
    bpy.utils.unregister_class(PORTAL_OT_ToggleServer)
    bpy.utils.unregister_class(ModalOperator)
    bpy.utils.unregister_class(PORTAL_PT_ServerControl)

    del bpy.types.Scene.portal_connections
    del bpy.types.Scene.portal_active_connection_index
