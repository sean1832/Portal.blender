# https://github.com/sean1832/portal.blender/blob/main/templates/custom_data_handler.py
import bpy

# ============================================================
# User Defined Custom Logic
# ============================================================


# Implement your custom logic here
def custom_data_handler(data):
    print(f"Processed data: {data}")


# ============================================================
# Function to Monitor Text Block Changes
# ============================================================

# This will store the last known hash of the text data
last_text_hash = None


def monitor_text_block():
    global last_text_hash

    # Get values from the properties defined in the UI
    text_block_name = bpy.context.scene.text_block_name
    check_interval = bpy.context.scene.check_interval

    if text_block_name in bpy.data.texts:
        text_block = bpy.data.texts[text_block_name]
        new_text = text_block.as_string()
        new_hash = hash(new_text)

        # If the text has changed, handle the new data
        if new_hash != last_text_hash:
            last_text_hash = new_hash
            custom_data_handler(new_text) # Call the custom data handler function

    return check_interval  # Return the interval to keep monitoring


# ============================================================
# 3D View Panel to Start/Stop Monitoring and Input Fields
# ============================================================


class TEXTBLOCK_PT_monitor(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport to control text block monitoring"""

    bl_label = "Portal Custom Data Handler"
    bl_idname = "TEXTBLOCK_PT_monitor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Portal.Custom"

    def draw(self, context):
        layout = self.layout

        # Grouping Text Block Name and Interval in separate rows for clarity
        split = layout.split(factor=0.4)
        col_left = split.column()
        col_right = split.column()
        col_left.label(text="Block Name")
        col_right.prop(context.scene, "text_block_name", text="")
        layout.prop(context.scene, "check_interval", text="Check Interval (sec)")

        # Separator for better UI clarity
        layout.separator()

        # Toggle Button in its own row for better visibility
        if context.scene.is_monitoring:
            layout.operator(
                "textblock.toggle_monitoring", text="Stop Monitoring", icon="PAUSE", depress=True
            )
        else:
            layout.operator(
                "textblock.toggle_monitoring", text="Start Monitoring", icon="PLAY", depress=False
            )


class TEXTBLOCK_OT_toggle_monitoring(bpy.types.Operator):
    """Operator to toggle text block monitoring (Start/Stop)"""

    bl_idname = "textblock.toggle_monitoring"
    bl_label = "Toggle Monitoring"

    def execute(self, context):
        if context.scene.is_monitoring:
            # Stop monitoring
            bpy.app.timers.unregister(monitor_text_block)
            context.scene.is_monitoring = False
            self.report({"INFO"}, "Stopped text block monitoring")
        else:
            # Start monitoring
            bpy.app.timers.register(monitor_text_block)
            context.scene.is_monitoring = True
            self.report({"INFO"}, "Started text block monitoring")
        return {"FINISHED"}


# ============================================================
# Register/Unregister Classes
# ============================================================

classes = (
    TEXTBLOCK_PT_monitor,
    TEXTBLOCK_OT_toggle_monitoring,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Add properties to the scene for user input
    bpy.types.Scene.text_block_name = bpy.props.StringProperty(
        name="Text Block Name", default="portal-data-0"
    )
    bpy.types.Scene.check_interval = bpy.props.FloatProperty(
        name="Check Interval", default=0.01, min=0.01, max=2.0
    )
    bpy.types.Scene.is_monitoring = bpy.props.BoolProperty(default=False)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # Remove properties from the scene
    del bpy.types.Scene.text_block_name
    del bpy.types.Scene.check_interval
    del bpy.types.Scene.is_monitoring


if __name__ == "__main__":
    register()
