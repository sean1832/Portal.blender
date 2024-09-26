# https://github.com/sean1832/portal.blender/blob/main/templates/custom_data_handler.py


class CustomHandler:
    def __init__(self):
        self.data = None
        self.channel_name = None
        self.channel_uuid = None

    def update(self, payload, channel_name, channel_uuid):
        """(Do not change) Update the data and channel UUID."""
        self.data = payload
        self.channel_name = channel_name
        self.channel_uuid = channel_uuid

    def handle(self):
        """This is where you implement the logic to handle the custom data."""
        print(f"Received custom data: {self.data} \nfrom channel: {self.channel_uuid}")
