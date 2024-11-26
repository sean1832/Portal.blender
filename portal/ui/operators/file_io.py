from pathlib import Path

import bpy

from portal.ui.properties.connection_properties import PortalConnection


class PORTAL_OT_SetDirectory(bpy.types.Operator):
    bl_idname = "portal.set_directory"
    bl_label = "Set Directory"
    bl_description = "Set the directory to save or load files"

    uuid: bpy.props.StringProperty()  # type: ignore
    filepath: bpy.props.StringProperty(subtype="DIR_PATH")  # type: ignore
    directory: bpy.props.StringProperty(subtype="DIR_PATH")  # type: ignore

    def execute(self, context) -> set[str]:
        # Use directory instead of directory_path
        directory = self.directory if self.directory else Path(self.filepath).parent.as_posix()

        self.report({"INFO"}, f"Set directory to '{directory}'")
        Path(directory).mkdir(parents=True, exist_ok=True)

        # assign the directory to the connection
        connection: PortalConnection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )
        if not connection:
            self.report({"ERROR"}, f"Connection with UUID '{self.uuid}' not found!")
            return {"CANCELLED"}

        connection.directory = directory
        return {"FINISHED"}

    def invoke(self, context, event) -> set[str]:
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


def register():
    bpy.utils.register_class(PORTAL_OT_SetDirectory)


def unregister():
    bpy.utils.unregister_class(PORTAL_OT_SetDirectory)
