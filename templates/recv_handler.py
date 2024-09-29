# Portal.blender: v0.2.0
# https://github.com/sean1832/portal.blender/blob/main/templates/recv_handler.py

# This is a template for handling custom data received.
# Attach this script to the 'Custom Handler' field in the 'Portal Server' panel
# after selecting 'Receive' as the direction and 'Custom' as the data type.

class MyRecvHandler:
    def __init__(self, payload, channel_name, channel_uuid):
        """Constructor. (Do not modify this part)"""
        self.data = payload
        self.channel_name = channel_name
        self.channel_uuid = channel_uuid

    def handle(self) -> None:
        """Handle received message."""
        print(f"Received custom data: {self.data} \nfrom channel: {self.channel_uuid}")
