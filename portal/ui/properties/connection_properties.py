# pyright: reportInvalidTypeForm=false
import uuid

import bpy


# Custom property group to hold connection properties
# See doc: https://developer.blender.org/docs/release_notes/2.80/python_api/addons/#class-property-registration
class PortalConnection(bpy.types.PropertyGroup):
    uuid: bpy.props.StringProperty(default=str(uuid.uuid4()))
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
    )
    name: bpy.props.StringProperty(name="Connection Name", default="testpipe")
    port: bpy.props.IntProperty(name="Port", default=6000)
    is_external: bpy.props.BoolProperty(name="Listen Remote", default=False)
    buffer_size: bpy.props.IntProperty(name="Buffer Size (KB)", default=1024)
    data_type: bpy.props.EnumProperty(
        name="Data Type",
        items=[
            ("Mesh", "Mesh", "Receive data as mesh"),
            ("Camera", "Camera", "Receive data as camera"),
            ("Custom", "Custom", "Handle data with custom handler"),
        ],
        default="Mesh",
    )
    event_timer: bpy.props.FloatProperty(name="Interval (sec)", default=0.01, min=0.001, max=1.0)
    running: bpy.props.BoolProperty(name="Running", default=False)
    show_details: bpy.props.BoolProperty(name="Show Details", default=True)
    custom_handler: bpy.props.StringProperty(name="Custom Handler", default="")

    direction: bpy.props.EnumProperty(
        name="Send/Receive",
        description="Choose the direction of data flow",
        items=[
            ("RECV", "recv", "Receive data from the server", "IMPORT", 0),  # Added icon 'IMPORT'
            ("SEND", "send", "Send data to the server", "EXPORT", 1),  # Added icon 'EXPORT'
        ],
        default="RECV",
    )

    send_data: bpy.props.StringProperty(name="Send Data", default="")


def register():
    bpy.utils.register_class(PortalConnection)
    bpy.types.Scene.portal_connections = bpy.props.CollectionProperty(type=PortalConnection)
    bpy.types.Scene.portal_active_connection_uuid = bpy.props.StringProperty(default="")


def unregister():
    bpy.utils.unregister_class(PortalConnection)
    del bpy.types.Scene.portal_connections
    del bpy.types.Scene.portal_active_connection_uuid
