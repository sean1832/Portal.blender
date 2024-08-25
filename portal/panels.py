import bpy  # type: ignore

from .managers import SERVER_MANAGERS


def on_panel_update(self, context):
    # This function will be called whenever the connection_type changes
    # This is where you can add logic to update other parts of the UI or behaviors based on the selection

    unregister_connection_properties(context.scene)
    register_connection_properties(context.scene.connection_type)


def get_connection_items(self, context):
    return [
        ("NAMED_PIPE", "Named Pipe", "Local pipe stream"),
        ("MMAP", "Memory Mapped File", "Local memory-mapped file"),
        ("WEBSOCKETS", "WebSockets", "Local / Remote WebSockets"),
        ("UDP", "UDP", "Local / Remote UDP"),
    ]


bpy.types.Scene.connection_type = bpy.props.EnumProperty(
    name="Connection Type",
    description="Choose the type of connection",
    items=get_connection_items,
    update=on_panel_update,
)


class ServerUIPanel(bpy.types.Panel):
    bl_label = "Portal Server"
    bl_idname = "PT_ServerControl"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Portal"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene

        # Connection Type
        layout.prop(scene, "connection_type")

        # Connection-specific properties
        box = layout.box()
        connection_type = scene.connection_type

        if connection_type == "NAMED_PIPE":
            self.draw_named_pipe(box, scene)
        elif connection_type == "MMAP":
            self.draw_mmap(box, scene)
        elif connection_type == "WEBSOCKETS":
            self.draw_websockets(box, scene)
        elif connection_type == "UDP":
            self.draw_udp(box, scene)

        # Data type selection
        layout.prop(scene, "data_type")

        # Start/Stop server buttons
        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("portal.start_server", text="Start Server", icon="PLAY")
        row.operator("portal.stop_server", text="Stop Server", icon="PAUSE")

        # Server status display
        self.draw_status(layout, connection_type)

    def draw_status(self, layout, connection_type):
        manager = SERVER_MANAGERS.get(connection_type, "NAMED_PIPE")
        status_row = layout.row()
        if manager.is_running():
            status_row.label(text="Status: Listening...", icon="RADIOBUT_ON")
        else:
            status_row.label(text="Status: Stopped", icon="RADIOBUT_OFF")

    def draw_named_pipe(self, layout, scene):
        col = layout.column()
        col.prop(scene, "pipe_name")
        col.prop(scene, "event_timer")

    def draw_mmap(self, layout, scene):
        col = layout.column()
        col.prop(scene, "mmf_name")
        col.prop(scene, "buffer_size")
        col.prop(scene, "event_timer")

    def draw_websockets(self, layout, scene):
        col = layout.column()
        col.prop(scene, "port")
        col.prop(scene, "route")
        col.prop(scene, "event_timer")

    def draw_udp(self, layout, scene):
        col = layout.column()
        col.prop(scene, "port")
        col.prop(scene, "event_timer")


def register_properties():
    # default initial connection type
    register_connection_properties("NAMED_PIPE")

    bpy.types.Scene.data_type = bpy.props.EnumProperty(
        name="Data Type",
        items=[
            ("Mesh", "Mesh", "Receive data as mesh"),
            ("Text", "Text", "Receive data as text"),
        ],
        default="Mesh",
    )


def unregister_properties():
    del bpy.types.Scene.data_type


def register_connection_properties(connection_type):
    if connection_type == "NAMED_PIPE":
        bpy.types.Scene.pipe_name = bpy.props.StringProperty(name="Name", default="testpipe")
        bpy.types.Scene.event_timer = bpy.props.FloatProperty(
            name="Interval (sec)", default=0.01, min=0.001, max=1.0
        )
    elif connection_type == "MMAP":
        bpy.types.Scene.mmf_name = bpy.props.StringProperty(name="Name", default="memory_file")
        bpy.types.Scene.buffer_size = bpy.props.IntProperty(name="Buffer Size (KB)", default=1024)
        bpy.types.Scene.event_timer = bpy.props.FloatProperty(
            name="Interval (sec)", default=0.01, min=0.001, max=1.0
        )

    elif connection_type == "WEBSOCKETS":
        bpy.types.Scene.port = bpy.props.IntProperty(name="Port", default=8765)
        bpy.types.Scene.route = bpy.props.StringProperty(name="route", default="/")
        bpy.types.Scene.event_timer = bpy.props.FloatProperty(
            name="Interval (sec)", default=0.01, min=0.001, max=1.0
        )
    elif connection_type == "UDP":
        bpy.types.Scene.port = bpy.props.IntProperty(name="Port", default=8765)
        bpy.types.Scene.event_timer = bpy.props.FloatProperty(
            name="Interval (sec)", default=0.01, min=0.001, max=1.0
        )


def unregister_connection_properties(scene):
    props_to_remove = ["pipe_name", "event_timer", "mmf_name", "port", "route"]
    for prop in props_to_remove:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)


def register_panels():
    bpy.utils.register_class(ServerUIPanel)
    register_properties()


def unregister_panels():
    bpy.utils.unregister_class(ServerUIPanel)
    unregister_properties()
