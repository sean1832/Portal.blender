import queue

import bpy  # type: ignore

from .handlers import StringHandler
from .managers import SERVER_MANAGERS


class StartServerOperator(bpy.types.Operator):
    bl_idname = "portal.start_server"
    bl_label = "Start Server"

    def execute(self, context):
        connection_type = context.scene.connection_type
        server_manager = SERVER_MANAGERS.get(connection_type)

        if server_manager and not server_manager.is_running():
            server_manager.start_server()
            bpy.ops.wm.modal_operator("INVOKE_DEFAULT")
        return {"FINISHED"}


class StopServerOperator(bpy.types.Operator):
    bl_idname = "portal.stop_server"
    bl_label = "Stop Server"

    def execute(self, context):
        connection_type = context.scene.connection_type
        server_manager = SERVER_MANAGERS.get(connection_type)

        if server_manager and server_manager.is_running():
            server_manager.stop_server()
        return {"FINISHED"}


class ModalOperator(bpy.types.Operator):
    bl_idname = "wm.modal_operator"
    bl_label = "Listener Modal Operator"

    def __init__(self):
        self._timer = None

    def modal(self, context, event):
        connection_type = context.scene.connection_type
        server_manager = SERVER_MANAGERS.get(connection_type)

        if server_manager and server_manager.is_shutdown():
            self.cancel(context)
            return {"CANCELLED"}

        if event.type == "TIMER":
            while not server_manager.data_queue.empty():
                try:
                    data = server_manager.data_queue.get_nowait()
                    StringHandler.handle_str_data(data, context.scene.data_type)
                except queue.Empty:
                    break
        return {"PASS_THROUGH"}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(
            context.scene.event_timer, window=context.window
        )
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)


registered_classes = set()


def safe_register_class(cls):
    if cls not in registered_classes:
        bpy.utils.register_class(cls)
        registered_classes.add(cls)


def safe_unregister_class(cls):
    if cls in registered_classes:
        bpy.utils.unregister_class(cls)
        registered_classes.remove(cls)


def register_operators():
    safe_register_class(StartServerOperator)
    safe_register_class(StopServerOperator)
    safe_register_class(ModalOperator)


def unregister_operators():
    safe_unregister_class(StartServerOperator)
    safe_unregister_class(StopServerOperator)
    safe_unregister_class(ModalOperator)
