from ..mmap_server import MMFServerManager
from ..pipe_server import PipeServerManager
from ..udp_server import UDPServerManager
from ..websockets_server import WebSocketServerManager


from ..sender.pipe_sender import PipeSenderManager
from ..sender.mmap_sender import MMFSenderManager
from ..sender.udp_sender import UDPSenderManager
from ..sender.websockets_sender import WebSocketSenderManager

class ConnectionManager:
    def __init__(self):
        self.managers = {}

    def get(self, connection_type, uuid, direction):
        """
        Retrieves or creates a new server manager instance for the given connection type and uuid.
        If a different connection type was previously used, it removes the old one and creates a new instance.
        """

        # Check if the server manager already exists for this uuid
        if uuid in self.managers:
            existing_manager, existing_type = self.managers[uuid]

            # If the existing server manager is of a different type, remove it and create a new one
            if existing_type != connection_type:
                existing_manager.stop_server()  # Stop the current server if running
                self.remove(uuid)  # Remove the current manager from the dictionary

        # If no server manager exists for this uuid or it was removed, create a new one
        if uuid not in self.managers:
            # Create a new server manager based on the connection type
            if direction == "SEND":
                if connection_type == "NAMED_PIPE":
                    manager = PipeSenderManager(uuid)
                elif connection_type == "MMAP":
                    manager = MMFSenderManager(uuid)
                elif connection_type == "WEBSOCKETS":
                    manager = WebSocketSenderManager(uuid)
                elif connection_type == "UDP":
                    manager = UDPSenderManager(uuid)
            else:
                if connection_type == "NAMED_PIPE":
                    manager = PipeServerManager(uuid)
                elif connection_type == "MMAP":
                    manager = MMFServerManager(uuid)
                elif connection_type == "WEBSOCKETS":
                    manager = WebSocketServerManager(uuid)
                elif connection_type == "UDP":
                    manager = UDPServerManager(uuid)
                else:
                    raise ValueError(f"Unknown connection type: {connection_type}")

            self.managers[uuid] = (manager, connection_type)

        return self.managers[uuid][0]  # Return the manager instance

    def remove(self, uuid):
        """
        Removes the server manager instance for the given uuid from the dictionary and ensures it is properly shut down.
        """
        if uuid in self.managers:
            server_manager, _ = self.managers[uuid]
            if server_manager.is_running():
                server_manager.stop_server()  # Ensure the server is stopped before removing
            del self.managers[uuid]
