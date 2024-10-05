import uuid

import bpy

from ..globals import CONNECTION_MANAGER, MODAL_OPERATORS
from ..properties.connection_properties import PortalConnection
from ..ui_utils.helper import is_connection_duplicated


# Operator to add new connection
class PORTAL_OT_AddConnection(bpy.types.Operator):
    bl_idname = "portal.add_connection"
    bl_label = "Add New Connection"
    bl_description = "Add a new connection"

    def execute(self, context):
        # Check if there are any existing connections
        connections = context.scene.portal_connections
        channel_num = len(connections) + 1
        new_name = f"channel-{channel_num}"

        while is_connection_duplicated(connections, new_name):
            new_name = f"channel-{channel_num + 1}"

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
        # Find the connection with the given UUID
        connection: PortalConnection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )

        if connection:
            index = context.scene.portal_connections.find(connection.name)
            server_manager = CONNECTION_MANAGER.get(
                connection.connection_type, self.uuid, connection.direction
            )

            # Stop the server if it's running
            if connection.running:
                if server_manager and server_manager.is_running():
                    server_manager.stop_server()
                    connection.running = False
                    CONNECTION_MANAGER.remove(self.uuid)

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
        connection: PortalConnection = next(
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

        server_manager = CONNECTION_MANAGER.get(
            connection.connection_type, self.uuid, connection.direction
        )

        if connection.running or (server_manager and server_manager.is_running()):
            # Stop the server if it's running
            if server_manager and server_manager.is_running():
                server_manager.stop_server()
                connection.running = False
                CONNECTION_MANAGER.remove(self.uuid)  # Remove the manager from SERVER_MANAGERS
                # Cancel the modal operator if it is running and unregister the event handlers
                if self.uuid in MODAL_OPERATORS:
                    modal_operator = MODAL_OPERATORS[self.uuid]
                    modal_operator.cancel(context)  # This will trigger _unregister_event_handlers
                    modal_operator._unregister_event_handlers()  # Ensuring handlers are unregistered
        else:
            # Start the server if it's not running
            if server_manager and not server_manager.is_running():
                server_manager.start_server()
                bpy.ops.wm.modal_operator("INVOKE_DEFAULT", uuid=self.uuid)
                connection.running = True

        return {"FINISHED"}


def register():
    bpy.utils.register_class(PORTAL_OT_AddConnection)
    bpy.utils.register_class(PORTAL_OT_RemoveConnection)
    bpy.utils.register_class(PORTAL_OT_ToggleServer)


def unregister():
    bpy.utils.unregister_class(PORTAL_OT_AddConnection)
    bpy.utils.unregister_class(PORTAL_OT_RemoveConnection)
    bpy.utils.unregister_class(PORTAL_OT_ToggleServer)
