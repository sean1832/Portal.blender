import bpy  # type: ignore

from .managers import SERVER_MANAGERS

def on_panel_update(self, context):
    unregister_connection_properties(context.scene)
    register_connection_properties(context.scene.connection_type)

def get_connection_items(self, context):
    return [
        ("NAMED_PIPE", "Named Pipe", "Local pipe stream"),
        ("MMAP", "Memory Mapped File", "Local memory-mapped file"),
        ("WEBSOCKETS", "WebSockets", "Local / Remote WebSockets"),
        ("UDP", "UDP", "Local / Remote UDP"),
    ]

# Set to keep track of registered properties
registered_properties = set()

def safe_register_property(attr_name, prop):
    if attr_name not in registered_properties:
        setattr(bpy.types.Scene, attr_name, prop)
        registered_properties.add(attr_name)

def safe_unregister_property(attr_name):
    if attr_name in registered_properties:
        delattr(bpy.types.Scene, attr_name)
        registered_properties.remove(attr_name)

safe_register_property('connection_type', bpy.props.EnumProperty(
    name="Connection Type",
    description="Choose the type of connection",
    items=get_connection_items,
    update=on_panel_update,
))

class ServerUIPanel(bpy.types.Panel):
    bl_label = "Portal Server"
    bl_idname = "PORTAL_PT_ServerControl"
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

    safe_register_property('data_type', bpy.props.EnumProperty(
        name="Data Type",
        items=[
            ("Mesh", "Mesh", "Receive data as mesh"),
            ("Text", "Text", "Receive data as text"),
        ],
        default="Mesh",
    ))

def unregister_properties():
    safe_unregister_property('data_type')

def register_connection_properties(connection_type):
    if connection_type == "NAMED_PIPE":
        safe_register_property('pipe_name', bpy.props.StringProperty(name="Name", default="testpipe"))
        safe_register_property('event_timer', bpy.props.FloatProperty(
            name="Interval (sec)", default=0.01, min=0.001, max=1.0
        ))
    elif connection_type == "MMAP":
        safe_register_property('mmf_name', bpy.props.StringProperty(name="Name", default="memory_file"))
        safe_register_property('buffer_size', bpy.props.IntProperty(name="Buffer Size (KB)", default=1024))
        safe_register_property('event_timer', bpy.props.FloatProperty(
            name="Interval (sec)", default=0.01, min=0.001, max=1.0
        ))
    elif connection_type == "WEBSOCKETS":
        safe_register_property('port', bpy.props.IntProperty(name="Port", default=8765))
        safe_register_property('route', bpy.props.StringProperty(name="route", default="/"))
        safe_register_property('event_timer', bpy.props.FloatProperty(
            name="Interval (sec)", default=0.01, min=0.001, max=1.0
        ))
    elif connection_type == "UDP":
        safe_register_property('port', bpy.props.IntProperty(name="Port", default=8765))
        safe_register_property('event_timer', bpy.props.FloatProperty(
            name="Interval (sec)", default=0.01, min=0.001, max=1.0
        ))

def unregister_connection_properties(scene):
    props_to_remove = ["pipe_name", "event_timer", "mmf_name", "port", "route"]
    for prop in props_to_remove:
        safe_unregister_property(prop)

registered_classes = set()

def safe_register_class(cls):
    if cls not in registered_classes:
        bpy.utils.register_class(cls)
        registered_classes.add(cls)

def safe_unregister_class(cls):
    if cls in registered_classes:
        bpy.utils.unregister_class(cls)
        registered_classes.remove(cls)

def register_panels():
    safe_register_class(ServerUIPanel)
    register_properties()

def unregister_panels():
    safe_unregister_class(ServerUIPanel)
    unregister_properties()
