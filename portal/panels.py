import bpy

from .pipe_server import PipeServerManager  # Adjust the import path as necessary


class PipeServerUIPanel(bpy.types.Panel):
    bl_label = "Pipe Server Control"
    bl_idname = "PT_PipeServerControl"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pipe Server"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "pipe_name")
        layout.prop(scene, "event_timer")
        layout.prop(scene, "data_type")

        row = layout.row()
        row.operator("pipe.start_pipe_server", text="Start")
        row.operator("pipe.stop_pipe_server", text="Stop")

        # Server status display
        if PipeServerManager.is_running():
            layout.label(text="Status: Listening...", icon="PLAY")
        else:
            layout.label(text="Status: Stopped", icon="PAUSE")


def register_panels():
    bpy.utils.register_class(PipeServerUIPanel)


def unregister_panels():
    bpy.utils.unregister_class(PipeServerUIPanel)
