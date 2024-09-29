import queue
import traceback

import bpy

from ...handlers.custom_handler import CustomHandler
from ...handlers.string_handler import StringHandler
from ..globals import CONNECTION_MANAGER, MODAL_OPERATORS
from ..ui_utils.helper import construct_packet_dict


class ModalOperator(bpy.types.Operator):
    bl_idname = "wm.modal_operator"
    bl_label = "Listener Modal Operator"
    bl_description = "Modal operator to handle server events"

    uuid: bpy.props.StringProperty()  # type: ignore

    def __init__(self):
        self._timer = None
        self.render_complete_handler = None
        self.frame_change_handler = None
        self.scene_update_handler = None
        self.custom_event_handler = None

    def modal(self, context, event):
        connection = self._get_connection(context)
        if not connection:
            self.report({"ERROR"}, "Connection not found.")
            return {"CANCELLED"}

        server_manager = self._get_server_manager(connection)
        if not server_manager:
            self.report({"ERROR"}, "Server manager not found.")
            return {"CANCELLED"}

        if self._is_server_shutdown(server_manager):
            self.report({"ERROR"}, "Server has been shut down.")
            return {"CANCELLED"}

        # Handle server errors and tracebacks
        if self._handle_server_errors(context, server_manager, connection):
            return {"CANCELLED"}

        # Handle sending and receiving based on connection direction
        if connection.direction == "SEND" and event.type in connection.event_types:
            self._handle_send_event(context, connection, server_manager)
        elif connection.direction == "RECV" and event.type == "TIMER":
            self._handle_recv_event(context, connection, server_manager)

        return {"PASS_THROUGH"}

    def execute(self, context):
        connection = self._get_connection(context)
        if not connection:
            self.report({"ERROR"}, "Connection not found.")
            return {"CANCELLED"}

        # Set up the timer and register modal handler
        self._timer = context.window_manager.event_timer_add(
            connection.event_timer, window=context.window
        )
        context.window_manager.modal_handler_add(self)

        MODAL_OPERATORS[self.uuid] = self
        self._register_event_handlers(connection)

        return {"RUNNING_MODAL"}

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)

        MODAL_OPERATORS.pop(self.uuid, None)
        self._unregister_event_handlers()

        return None

    def _handle_send_event(self, context, connection, server_manager):
        try:
            message_to_send = construct_packet_dict(connection.dict_items, connection.precision)
            if message_to_send:
                server_manager.data_queue.put(message_to_send)
        except Exception as e:
            self._report_error(
                context,
                f"Error sending data: {e}",
                server_manager,
                connection,
                traceback=traceback.format_exc(),
            )

    def _handle_recv_event(self, context, connection, server_manager):
        while not server_manager.data_queue.empty():
            try:
                data = server_manager.data_queue.get_nowait()
                if not data or data == "{}" or data == "[]":  # Empty data
                    break
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
                self._report_error(
                    context,
                    f"Error handling received data: {e}",
                    server_manager,
                    connection,
                    traceback=traceback.format_exc(),
                )

    def _handle_server_errors(self, context, server_manager, connection):
        with server_manager.error_lock:
            error = server_manager.error
            server_traceback = server_manager.traceback
        if error:
            return self._report_error(
                context,
                f"Error in server: {error}",
                server_manager,
                connection,
                server_traceback,
            )
        return False

    def _report_error(self, context, message, server_manager, connection, traceback=None):
        self.report({"ERROR"}, message)
        if traceback:
            print(traceback)
        else:
            print(message)
        if server_manager.is_running():
            server_manager.stop_server()
        connection.running = False
        CONNECTION_MANAGER.remove(self.uuid)
        self.cancel(context)
        return {"CANCELLED"}

    def _send_data_on_event(self, scene, connection):
        server_manager = self._get_server_manager(connection)
        if not server_manager:
            return
        self._handle_send_event(bpy.context, connection, server_manager)

    def _get_connection(self, context):
        return next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )

    def _get_connection_by_uuid(self, uuid):
        return next(
            (conn for conn in bpy.context.scene.portal_connections if conn.uuid == uuid), None
        )

    def _get_server_manager(self, connection):
        return CONNECTION_MANAGER.get(connection.connection_type, self.uuid, connection.direction)

    def _is_server_shutdown(self, server_manager):
        if server_manager.is_shutdown():
            self.cancel(bpy.context)
            return True
        return False

    def _register_event_handlers(self, connection):
        if "RENDER_COMPLETE" in connection.event_types:
            # https://docs.blender.org/api/current/bpy.app.handlers.html#bpy.app.handlers.render_complete
            self.render_complete_handler = lambda scene: self._send_data_on_event(scene, connection)
            bpy.app.handlers.render_complete.append(self.render_complete_handler)

        if "FRAME_CHANGE" in connection.event_types:
            # https://docs.blender.org/api/current/bpy.app.handlers.html#bpy.app.handlers.frame_change_post
            self.frame_change_handler = lambda scene: self._send_data_on_event(scene, connection)
            bpy.app.handlers.frame_change_post.append(self.frame_change_handler)

        if "SCENE_UPDATE" in connection.event_types:
            # on any scene event
            # https://docs.blender.org/api/current/bpy.app.handlers.html#bpy.app.handlers.depsgraph_update_post
            self.scene_update_handler = lambda scene: self._send_data_on_event(scene, connection)
            bpy.app.handlers.depsgraph_update_post.append(self.scene_update_handler)

        if "CUSTOM" in connection.event_types:
            # Custom event
            try:
                handler = CustomHandler.load(
                    connection.custom_handler,
                    "MySendEventHandler",
                    "https://github.com/sean1832/portal.blender/blob/main/templates/sender_handler.py",
                )
                self.custom_event_handler = handler(self._get_server_manager(connection))
                self.custom_event_handler.register()
            except Exception as e:
                self.report({"ERROR"}, f"Error loading custom event handler: {e}")
                return {"CANCELLED"}

    def _unregister_event_handlers(self):
        if self.render_complete_handler:
            bpy.app.handlers.render_complete.remove(self.render_complete_handler)
            self.render_complete_handler = None

        if self.frame_change_handler:
            bpy.app.handlers.frame_change_post.remove(self.frame_change_handler)
            self.frame_change_handler = None

        if self.scene_update_handler:
            bpy.app.handlers.depsgraph_update_post.remove(self.scene_update_handler)
            self.scene_update_handler = None

        if self.custom_event_handler:
            self.custom_event_handler.unregister()
            self.custom_event_handler = None


def register():
    bpy.utils.register_class(ModalOperator)


def unregister():
    bpy.utils.unregister_class(ModalOperator)
