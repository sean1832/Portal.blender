import bpy


# Add operator to load a local file into a Blender text block
class PORTAL_OT_LoadFileToTextBlock(bpy.types.Operator):
    bl_idname = "portal.load_file_to_text_block"
    bl_label = "Load File to Text Block"
    bl_description = "Load a file from your local system into a Blender text block"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore
    uuid: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        # Check if the file exists and can be read
        try:
            with open(self.filepath, "r") as file:
                content = file.read()
        except FileNotFoundError:
            self.report({"ERROR"}, "File not found!")
            return {"CANCELLED"}
        except IOError:
            self.report({"ERROR"}, "Cannot read the file!")
            return {"CANCELLED"}

        # Create or update a Blender text block
        text_name = bpy.path.basename(self.filepath)
        if text_name in bpy.data.texts:
            text_block = bpy.data.texts[text_name]
            text_block.clear()  # Clear existing content
        else:
            text_block = bpy.data.texts.new(text_name)

        text_block.from_string(content)

        # Set the connection's custom_handler property to reference the loaded text block
        connection = next(
            (conn for conn in context.scene.portal_connections if conn.uuid == self.uuid), None
        )
        if connection:
            connection.custom_handler = text_name

        self.report({"INFO"}, f"Loaded '{text_name}' into Blender Text Editor.")
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)  # Open file browser
        return {"RUNNING_MODAL"}


class PORTAL_OT_OpenTextEditor(bpy.types.Operator):
    bl_idname = "portal.open_text_editor"
    bl_label = "Open Text in Editor"
    bl_description = "Open the selected text block in Blender's text editor"

    text_name: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        text = bpy.data.texts.get(self.text_name)
        if not text:
            self.report({"WARNING"}, f"Text block '{self.text_name}' not found!")
            return {"CANCELLED"}

        # Try to find an existing Text Editor area
        for area in context.screen.areas:
            if area.type == "TEXT_EDITOR":
                area.spaces.active.text = text
                return {"FINISHED"}

        # Open a new window with a TEXT_EDITOR if no suitable area exists
        bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
        new_area = None
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                new_area = area
                break

        if new_area:
            new_area.type = 'TEXT_EDITOR'
            new_area.spaces.active.text = text

        return {"FINISHED"}

def register():
    bpy.utils.register_class(PORTAL_OT_LoadFileToTextBlock)
    bpy.utils.register_class(PORTAL_OT_OpenTextEditor)

def unregister():
    bpy.utils.unregister_class(PORTAL_OT_LoadFileToTextBlock)
    bpy.utils.unregister_class(PORTAL_OT_OpenTextEditor)
