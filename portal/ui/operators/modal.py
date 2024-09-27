import queue
import traceback

import bpy

from ...handlers.string_handler import StringHandler
from ..globals import MODAL_OPERATORS, RECV_MANAGER


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

        server_manager = RECV_MANAGER.get(connection.connection_type, self.uuid)

        if server_manager and server_manager.is_shutdown():
            self.cancel(context)
            return {"CANCELLED"}

        if event.type == "TIMER" and connection.running:
            with server_manager.error_lock:
                error = server_manager.error
                server_traceback = server_manager.traceback
            if error:
                return self.report_error(
                    context,
                    f"Error in server: {error}",
                    server_manager,
                    connection,
                    server_traceback,
                )
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
                except Exception as e:
                    return self.report_error(
                        context,
                        f"Error handling string: {e}",
                        server_manager,
                        connection,
                        traceback=traceback.format_exc(),
                    )
        return {"PASS_THROUGH"}

    def execute(self, context):
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
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        self._timer = None

        # Remove the modal operator from the dictionary
        if self.uuid in MODAL_OPERATORS:
            del MODAL_OPERATORS[self.uuid]

        #return {"CANCELLED"}
        return None

    def report_error(self, context, message, server_manager, connection, traceback=None):
        self.report({"ERROR"}, message)
        print(traceback) if traceback else print(message)
        if server_manager.is_running():
            server_manager.stop_server()
        connection.running = False
        RECV_MANAGER.remove(self.uuid)
        self.cancel(context)
        return {"CANCELLED"}


def register():
    bpy.utils.register_class(ModalOperator)


def unregister():
    bpy.utils.unregister_class(ModalOperator)
