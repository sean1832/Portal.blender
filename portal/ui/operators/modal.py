import json
import queue
import time
import traceback
from typing import Optional

import bpy
from bpy.types import Context, Event, Scene, Timer

from ...data_struct.mesh import Mesh
from ...data_struct.payload import Payload
from ...handlers.custom_handler import CustomHandler
from ...handlers.string_handler import StringHandler
from ...server.interface import Server
from ..globals import MODAL_OPERATORS, SERVER_MANAGER
from ..properties.connection_properties import PortalConnection


class ModalOperator(bpy.types.Operator):
    bl_idname = "wm.modal_operator"
    bl_label = "Listener Modal Operator"
    bl_description = "Modal operator to handle server events"

    uuid: bpy.props.StringProperty()  # type: ignore

    def __init__(self):
        self._timer: Timer = None
        self.render_complete_handler = None
        self.frame_change_handler = None
        self.scene_update_handler = None
        self.custom_event_handler = None
        self.last_update_time = 0  # Track the last update time for the delay

    def modal(self, context: Context, event: Event):
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

    def execute(self, context: Context) -> set[str]:
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

        if connection.direction == "SEND":
            # send initial data
            self._handle_send_event(context, connection, self._get_server_manager(connection))

        return {"RUNNING_MODAL"}

    def cancel(self, context: Context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)

        MODAL_OPERATORS.pop(self.uuid, None)
        self._unregister_event_handlers()

        return None

    def _handle_send_event(
        self, context: Context, connection: PortalConnection, server_manager: Server
    ):
        try:
            message_to_send = self._construct_packet_dict(connection.dict_items)
            if not message_to_send or message_to_send == "{}" or message_to_send == "[]":
                return
            server_manager.data_queue.put(message_to_send)
        except Exception as e:
            self._report_error(
                context,
                f"Error sending data: {e}",
                server_manager,
                connection,
                traceback=traceback.format_exc(),
            )

    def _construct_packet_dict(self, data_items: dict) -> str:
        """Helper function to construct a dictionary from a collection of dictionary items"""
        payload = Payload()
        meta = {}
        contains_mesh = False
        for item in data_items:
            if item.value_type == "STRING":
                meta[item.key] = item.value_string
            elif item.value_type == "INT":
                meta[item.key] = item.value_int
            elif item.value_type == "FLOAT":
                meta[item.key] = item.value_float
            elif item.value_type == "BOOL":
                meta[item.key] = item.value_bool
            elif item.value_type == "TIMESTAMP":
                meta[item.key] = int(time.time() * 1000)
            elif item.value_type == "SCENE_OBJECT":
                contains_mesh = True
                scene_obj = item.value_scene_object
                if scene_obj.type == "MESH":
                    payload.add_items(Mesh.from_obj(scene_obj).to_dict())
                elif scene_obj.type == "CAMERA":
                    raise NotImplementedError("Camera object type is not supported yet")
                elif scene_obj.type == "LIGHT":
                    raise NotImplementedError("Light object type is not supported yet")
                else:
                    raise ValueError(f"Unsupported object type: {scene_obj.type}")
            elif item.value_type == "PROPERTY_PATH":
                meta[item.key] = self._get_property_from_path(item.value_property_path)
            elif item.value_type == "UUID":
                meta[item.key] = item.value_uuid

        if contains_mesh:
            payload.set_meta(meta)
            return payload.to_json_str()
        return json.dumps(meta)

    @staticmethod
    def _get_property_from_path(path: str):
        # Use eval to resolve the path
        value = eval(path)
        return value

    def _handle_recv_event(
        self, context: Context, connection: PortalConnection, server_manager: Server
    ):
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

    def _handle_server_errors(
        self, context: Context, server_manager: Server, connection: PortalConnection
    ) -> bool:
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

    def _report_error(
        self,
        context: Context,
        message: str,
        server_manager: Server,
        connection: PortalConnection,
        traceback: Optional[str] = None,
    ):
        self.report({"ERROR"}, message)
        if traceback:
            print(traceback)
        else:
            print(message)
        if server_manager.is_running():
            server_manager.stop_server()
        connection.running = False
        SERVER_MANAGER.remove(self.uuid)
        self.cancel(context)
        return {"CANCELLED"}

    def _send_data_on_event(self, scene: Scene, connection: PortalConnection):
        current_time = time.time()
        if current_time - self.last_update_time < connection.event_timer:
            return  # Skip sending if within the delay threshold

        self.last_update_time = current_time  # Update the last event time

        server_manager = self._get_server_manager(connection)
        if not server_manager:
            return
        self._handle_send_event(bpy.context, connection, server_manager)

    def _get_connection(self, context: Context):
        return next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )

    def _get_connection_by_uuid(self, uuid: str):
        return next(
            (conn for conn in bpy.context.scene.portal_connections if conn.uuid == uuid), None
        )

    def _get_server_manager(self, connection: PortalConnection) -> Server:
        return SERVER_MANAGER.get(connection.connection_type, self.uuid, connection.direction)

    def _is_server_shutdown(self, server_manager: Server) -> bool:
        if server_manager.is_shutdown():
            self.cancel(bpy.context)
            return True
        return False

    def _register_event_handlers(self, connection: PortalConnection):
        if "RENDER_COMPLETE" in connection.event_types:
            self.render_complete_handler = lambda scene: self._send_data_on_event(scene, connection)
            bpy.app.handlers.render_complete.append(self.render_complete_handler)

        if "FRAME_CHANGE" in connection.event_types:
            self.frame_change_handler = lambda scene: self._send_data_on_event(scene, connection)
            bpy.app.handlers.frame_change_post.append(self.frame_change_handler)

        if "SCENE_UPDATE" in connection.event_types:
            self.scene_update_handler = lambda scene: self._send_data_on_event(scene, connection)
            bpy.app.handlers.depsgraph_update_post.append(self.scene_update_handler)

        if "CUSTOM" in connection.event_types:
            try:
                handler = CustomHandler.load(
                    connection.custom_handler,
                    "MySendEventHandler",
                    "https://github.com/sean1832/Portal.blender/blob/main/templates/send_handler.py",
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
