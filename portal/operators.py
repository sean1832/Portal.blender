import queue

import bpy

from .pipe_server import PipeServerManager


class StartPipeServerOperator(bpy.types.Operator):
    bl_idname = "pipe.start_server"
    bl_label = "Start Pipe Server"

    def execute(self, context):
        if not PipeServerManager.is_running():
            PipeServerManager.start_server()
            bpy.ops.wm.modal_operator("INVOKE_DEFAULT")
        return {"FINISHED"}


class StopPipeServerOperator(bpy.types.Operator):
    bl_idname = "pipe.stop_server"
    bl_label = "Stop Pipe Server"

    def execute(self, context):
        if PipeServerManager.is_running():
            PipeServerManager.stop_server()
        return {"FINISHED"}


class ModalOperator(bpy.types.Operator):
    bl_idname = "wm.modal_operator"
    bl_label = "Pipe Listener Modal Operator"

    def __init__(self):
        self._timer = None

    def modal(self, context, event):
        if PipeServerManager.is_shutdown():
            self.cancel(context)
            return {"CANCELLED"}

        if event.type == "TIMER":
            while not PipeServerManager.data_queue.empty():
                try:
                    data = PipeServerManager.data_queue.get_nowait()
                    from .handlers import DataHandler

                    DataHandler.handle_data(data, context.scene.data_type)
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


def register_operators():
    bpy.utils.register_class(StartPipeServerOperator)
    bpy.utils.register_class(StopPipeServerOperator)
    bpy.utils.register_class(ModalOperator)


def unregister_operators():
    bpy.utils.unregister_class(StartPipeServerOperator)
    bpy.utils.unregister_class(StopPipeServerOperator)
    bpy.utils.unregister_class(ModalOperator)
