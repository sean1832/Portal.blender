import queue
import uuid

import bpy

from ..handlers.string_handler import StringHandler
from ..utils.managers import get_server_manager, remove_server_manager

MODAL_OPERATORS = {}


def is_connection_duplicated(connections, name_to_check, uuid_to_ignore=None):
    """Helper function to check if a connection name is duplicated"""
    for conn in connections:
        if conn.name == name_to_check and conn.uuid != uuid_to_ignore:
            return True
    return False


# Custom property group to hold connection properties
class PortalConnection(bpy.types.PropertyGroup):
    uuid: bpy.props.StringProperty(default=str(uuid.uuid4()))  # type: ignore
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
    custom_handler: bpy.props.StringProperty(name="Custom Handler", default="")  # type: ignore


# Operator to add new connection
class PORTAL_OT_AddConnection(bpy.types.Operator):
    bl_idname = "portal.add_connection"
    bl_label = "Add New Connection"
    bl_description = "Add a new connection"

    def execute(self, context):
        # Check if there are any existing connections
        connections = context.scene.portal_connections
        new_name = f"channel-{len(connections) + 1}"
        if is_connection_duplicated(connections, new_name):
            self.report({"ERROR"}, f"Connection name '{new_name}' already exists!")
            return {"CANCELLED"}

        new_connection = connections.add()
        new_connection.uuid = str(uuid.uuid4())
        new_connection.name = new_name
        new_connection.port = 6000 + len(connections) - 1

        if len(connections) > 1:
            # If there's at least one existing connection, use the same connection type as the last one
            last_connection = connections[-2]  # Get the last existing connection
            new_connection.connection_type = last_connection.connection_type
            new_connection.data_type = last_connection.data_type
        return {"FINISHED"}


class PORTAL_OT_RemoveConnection(bpy.types.Operator):
    bl_idname = "portal.remove_connection"
    bl_label = "Remove Selected Connection"
    bl_description = "Remove the selected connection"
    uuid: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        global MODAL_OPERATORS
        # Find the connection with the given UUID
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )

        if connection:
            index = context.scene.portal_connections.find(connection.name)
            server_manager = get_server_manager(connection.connection_type, self.uuid)

            # Stop the server if it's running
            if connection.running:
                if server_manager and server_manager.is_running():
                    server_manager.stop_server()
                    connection.running = False
                    remove_server_manager(self.uuid)

                # Cancel the modal operator if it is running
                if uuid in MODAL_OPERATORS:
                    modal_operator = MODAL_OPERATORS[uuid]
                    modal_operator.cancel(context)

            # Now safe to remove the connection
            context.scene.portal_connections.remove(index)
        return {"FINISHED"}


# Operator to start/stop server
class PORTAL_OT_ToggleServer(bpy.types.Operator):
    bl_idname = "portal.toggle_server"
    bl_label = "Start/Stop Server"
    bl_description = "Start or stop the selected server"
    uuid: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )

        if not connection:
            self.report({"ERROR"}, "Connection not found!")
            return {"CANCELLED"}

        if is_connection_duplicated(
            context.scene.portal_connections, connection.name, connection.uuid
        ):
            self.report({"ERROR"}, f"Connection name '{connection.name}' already exists!")
            return {"CANCELLED"}

        server_manager = get_server_manager(connection.connection_type, self.uuid)

        if connection.running or (server_manager and server_manager.is_running()):
            # Stop the server if it's running
            if server_manager and server_manager.is_running():
                server_manager.stop_server()
                connection.running = False
                remove_server_manager(self.uuid)  # Remove the manager from SERVER_MANAGERS
        else:
            # Start the server if it's not running
            if server_manager and not server_manager.is_running():
                server_manager.start_server()
                bpy.ops.wm.modal_operator("INVOKE_DEFAULT", uuid=self.uuid)
                connection.running = True

        return {"FINISHED"}


# Add operator to load a local file into a Blender text block
class PORTAL_OT_LoadFileToTextBlock(bpy.types.Operator):
    bl_idname = "portal.load_file_to_text_block"
    bl_label = "Load File to Text Block"
    bl_description = "Load a file from your local system into a Blender text block"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    uuid: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        # Check if the file exists and can be read
        try:
            with open(self.filepath, "r") as file:
                content = file.read()
        except FileNotFoundError:
            self.report({"ERROR"}, "File not found!")
            return {"CANCELLED"}
        except IOError:
            self.report({"ERROR"}, "Cannot read the file!")
            return {"CANCELLED"}

        # Create or update a Blender text block
        text_name = bpy.path.basename(self.filepath)
        if text_name in bpy.data.texts:
            text_block = bpy.data.texts[text_name]
            text_block.clear()  # Clear existing content
        else:
            text_block = bpy.data.texts.new(text_name)

        text_block.from_string(content)

        # Set the connection's custom_handler property to reference the loaded text block
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )
        if connection:
            connection.custom_handler = text_name

        self.report({"INFO"}, f"Loaded '{text_name}' into Blender Text Editor.")
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)  # Open file browser
        return {"RUNNING_MODAL"}


class PORTAL_OT_OpenTextEditor(bpy.types.Operator):
    bl_idname = "portal.open_text_editor"
    bl_label = "Open Text in Editor"
    bl_description = "Open the selected text block in Blender's text editor"

    text_name: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        text = bpy.data.texts.get(self.text_name)
        if not text:
            self.report({"WARNING"}, f"Text block '{self.text_name}' not found!")
            return {"CANCELLED"}

        # Try to find an existing Text Editor area
        for area in context.screen.areas:
            if area.type == "TEXT_EDITOR":
                area.spaces.active.text = text
                return {"FINISHED"}

        # Try to find a non-critical area (e.g., VIEW_3D or OUTLINER) to turn into a TEXT_EDITOR
        for area in context.screen.areas:
            if area.type not in {"PROPERTIES", "OUTLINER", "PREFERENCES", "INFO"}:
                area.type = "TEXT_EDITOR"
                area.spaces.active.text = text
                return {"FINISHED"}

        # If no suitable area, open a new window with a TEXT_EDITOR
        new_window = bpy.ops.screen.area_split(direction="VERTICAL", factor=0.5)
        if new_window == "FINISHED":
            for area in context.screen.areas:
                if area.type == "TEXT_EDITOR":
                    area.spaces.active.text = text
                    break

        return {"FINISHED"}


# Modal operator for server event handling
class ModalOperator(bpy.types.Operator):
    bl_idname = "wm.modal_operator"
    bl_label = "Listener Modal Operator"
    bl_description = "Modal operator to handle server events"

    uuid: bpy.props.StringProperty()  # type: ignore

    def __init__(self):
        self._timer = None

    def modal(self, context, event):
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )

        # Check if the connection still exists
        if connection is None:
            # If the connection has been removed, cancel the modal operator
            self.cancel(context)
            return {"CANCELLED"}

        server_manager = get_server_manager(connection.connection_type, self.uuid)

        if server_manager and server_manager.is_shutdown():
            self.cancel(context)
            return {"CANCELLED"}

        if event.type == "TIMER" and connection.running:
            while not server_manager.data_queue.empty():
                try:
                    data = server_manager.data_queue.get_nowait()
                    StringHandler.handle_string(
                        data,
                        connection.data_type,
                        self.uuid,
                        connection.name,
                        connection.custom_handler,
                    )
                except queue.Empty:
                    break
        return {"PASS_THROUGH"}

    def execute(self, context):
        global MODAL_OPERATORS
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )
        self._timer = context.window_manager.event_timer_add(
            connection.event_timer, window=context.window
        )
        context.window_manager.modal_handler_add(self)

        # Store this modal operator in the global dictionary
        MODAL_OPERATORS[self.uuid] = self

        return {"RUNNING_MODAL"}

    def cancel(self, context):
        global MODAL_OPERATORS
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        self._timer = None

        # Remove the modal operator from the dictionary
        if self.uuid in MODAL_OPERATORS:
            del MODAL_OPERATORS[self.uuid]

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


# Register properties, classes, and UI panel
def register_ui():
    bpy.utils.register_class(PortalConnection)
    bpy.utils.register_class(PORTAL_OT_AddConnection)
    bpy.utils.register_class(PORTAL_OT_RemoveConnection)
    bpy.utils.register_class(PORTAL_OT_ToggleServer)
    bpy.utils.register_class(ModalOperator)
    bpy.utils.register_class(PORTAL_PT_ServerControl)
    bpy.utils.register_class(PORTAL_OT_OpenTextEditor)
    bpy.utils.register_class(PORTAL_OT_LoadFileToTextBlock)

    bpy.types.Scene.portal_connections = bpy.props.CollectionProperty(type=PortalConnection)
    bpy.types.Scene.portal_active_connection_uuid = bpy.props.StringProperty(default="")


def unregister_ui():
    bpy.utils.unregister_class(PortalConnection)
    bpy.utils.unregister_class(PORTAL_OT_AddConnection)
    bpy.utils.unregister_class(PORTAL_OT_RemoveConnection)
    bpy.utils.unregister_class(PORTAL_OT_ToggleServer)
    bpy.utils.unregister_class(ModalOperator)
    bpy.utils.unregister_class(PORTAL_PT_ServerControl)
    bpy.utils.unregister_class(PORTAL_OT_OpenTextEditor)
    bpy.utils.unregister_class(PORTAL_OT_LoadFileToTextBlock)

    del bpy.types.Scene.portal_connections
    del bpy.types.Scene.portal_active_connection_uuid
