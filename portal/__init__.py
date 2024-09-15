import importlib
import os
import subprocess
import sys
from collections import namedtuple

import bpy  # type: ignore

from .ui.panel import register_ui, unregister_ui

bl_info = {
    "name": "Portal",
    "author": "Zeke Zhang",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "category": "System",
    "location": "View3D > Sidebar > Portal",
    "description": "Data communication via IPC ",
    "tracker_url": "https://github.com/sean1832/portal.blender/issues",
    "doc_url": "https://github.com/sean1832/portal.blender",
    "support": "COMMUNITY",
}

# *************************************
# Install Dependencies
# *************************************

Dependency = namedtuple("Dependency", ["module", "package", "name"])

dependencies = (
    Dependency(module="pywintypes", package="pywin32==306", name=None),
    Dependency(module="aiohttp", package="aiohttp==3.10.5", name=None),
)


class DependencyManager:
    dependencies_installed = False

    @staticmethod
    def import_module(module_name, global_name=None, reload=True):
        if global_name is None:
            global_name = module_name
        if global_name in globals():
            importlib.reload(globals()[global_name])
        else:
            globals()[global_name] = importlib.import_module(module_name)

    @staticmethod
    def install_pip():
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
        except subprocess.CalledProcessError:
            import ensurepip

            ensurepip.bootstrap()
            os.environ.pop("PIP_REQ_TRACKER", None)

    @staticmethod
    def install_and_import_module(module_name, package_name=None, global_name=None):
        if package_name is None:
            package_name = module_name
        if global_name is None:
            global_name = module_name

        environ_copy = dict(os.environ)
        environ_copy["PYTHONNOUSERSITE"] = "1"

        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name], check=True, env=environ_copy
        )
        # DependencyManager.import_module(module_name, global_name)

    @staticmethod
    def are_dependencies_installed():
        return DependencyManager.dependencies_installed


class RestartBlenderOperator(bpy.types.Operator):
    bl_idname = "wm.restart_blender_dialog"
    bl_label = "Restart Blender"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        self.layout.label(text="Restart Blender to complete the installation?", icon="QUESTION")

    def execute(self, context):
        # Assuming the user pressed 'OK' to restart
        bpy.ops.wm.quit_blender()
        return {"FINISHED"}


class InstallDependenciesOperator(bpy.types.Operator):
    bl_idname = "pipe.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = (
        "Installs the required Python packages for this add-on. Internet connection is required."
    )
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return not DependencyManager.are_dependencies_installed()

    def execute(self, context):
        try:
            DependencyManager.install_pip()
            for dependency in dependencies:
                DependencyManager.install_and_import_module(
                    module_name=dependency.module,
                    package_name=dependency.package,
                    global_name=dependency.name,
                )
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        DependencyManager.dependencies_installed = True

        bpy.utils.register_class(RestartBlenderOperator)
        bpy.ops.wm.restart_blender_dialog("INVOKE_DEFAULT")

        return {"FINISHED"}


class DependencyWarningPanel(bpy.types.Panel):
    bl_label = "Dependencies Warning"
    bl_category = "Portal"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_idname = "PORTAL_PT_DependencyWarningPanel"

    @classmethod
    def poll(cls, context):
        return not DependencyManager.are_dependencies_installed()

    def draw(self, context):
        layout = self.layout
        lines = [
            "Please install the missing dependencies.",
            "1. Open the preferences (Edit > Preferences > Add-ons).",
            "2. Search for the 'Portal' add-on.",
            "3. Open the details section of the add-on.",
            "4. Click on the 'Install dependencies' button.",
        ]
        for line in lines:
            layout.label(text=line)


class PortalPipePreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.operator(InstallDependenciesOperator.bl_idname, icon="CONSOLE")


def register_dependencies():
    safe_register_class(DependencyWarningPanel)
    safe_register_class(InstallDependenciesOperator)
    safe_register_class(PortalPipePreferences)

    try:
        for dependency in dependencies:
            DependencyManager.import_module(
                module_name=dependency.module, global_name=dependency.name
            )
        DependencyManager.dependencies_installed = True
    except ModuleNotFoundError:
        return


def unregister_dependencies():
    safe_unregister_class(DependencyWarningPanel)
    safe_unregister_class(InstallDependenciesOperator)
    safe_unregister_class(PortalPipePreferences)


# *************************************
# Install Dependencies
# *************************************

registered_classes = set()


def safe_register_class(cls):
    if cls not in registered_classes:
        bpy.utils.register_class(cls)
        registered_classes.add(cls)


def safe_unregister_class(cls):
    if cls in registered_classes:
        bpy.utils.unregister_class(cls)
        registered_classes.remove(cls)


def register():
    register_dependencies()
    if DependencyManager.are_dependencies_installed():
        register_ui()


def unregister():
    safe_unregister_class(RestartBlenderOperator)
    if DependencyManager.are_dependencies_installed():
        unregister_ui()
    unregister_dependencies()


if __name__ == "__main__":
    register()
