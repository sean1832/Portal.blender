# Portal.blender: v0.2.0
# https://github.com/sean1832/portal.blender/blob/main/templates/send_handler.py

# This is a template for sending custom data on a specific event trigger.
# Attach this script to the 'Custom Handler' field in the 'Portal Server' panel 
# after selecting 'Send' as the direction and 'Custom' as the event trigger type.

import bpy
import json
import uuid

class MySendEventHandler:
    def __init__(self, server_manager):
        """Constructor. (Do not modify this part)"""
        self.scene_update_handler = None
        self.server_manager = server_manager
    
    def _send_data_on_event(self, scene):
        """Send data when the event is triggered. (Do not modify this part)"""
        message_to_send = self._construct_data()
        if message_to_send:
            self.server_manager.data_queue.put(message_to_send)
    
    def _construct_data(self) -> str:
        """Construct the custom data to be sent. Modify this part with your custom logic."""
        return json.dumps({
            "Key": "Insert your custom data to send here. This is just a placeholder.",
            "Nested": {
                "Array": [1, 2, 3, 4, 5],
            },
            "UUID": str(uuid.uuid4())
        })

    def register(self):
        """Register the event handler. Update the trigger event as needed."""
        self.scene_update_handler = lambda scene: self._send_data_on_event(scene)
        
        # Modify this line to set your desired event trigger:
        # see doc: https://docs.blender.org/api/current/bpy.app.handlers.html#bpy.app.handlers.depsgraph_update_post
        bpy.app.handlers.depsgraph_update_post.append(self.scene_update_handler)  # On scene update

        # Other trigger event examples (uncomment if needed):
        # ---------------------------
        # bpy.app.handlers.render_init.append(self.scene_update_handler)  # On render start
        # bpy.app.handlers.render_complete.append(self.scene_update_handler)  # On render completion
        # bpy.app.handlers.render_write.append(self.scene_update_handler)  # On render frame write
        # bpy.app.handlers.save_post.append(self.scene_update_handler)  # After saving the file

    def unregister(self):
        """Unregister the event handler. Be sure to remove the specific event."""
        if self.scene_update_handler:
            # Remove the active event trigger:
            bpy.app.handlers.depsgraph_update_post.remove(self.scene_update_handler)

            # Remove other events if previously registered (uncomment if used):
            # ---------------------------
            # bpy.app.handlers.render_init.remove(self.scene_update_handler)
            # bpy.app.handlers.render_complete.remove(self.scene_update_handler)
            # bpy.app.handlers.render_write.remove(self.scene_update_handler)
            # bpy.app.handlers.save_post.remove(self.scene_update_handler)

            self.scene_update_handler = None
