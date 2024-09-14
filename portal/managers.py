from .server.mmap_server import MMFServerManager
from .server.pipe_server import PipeServerManager
from .server.udp_server import UDPServerManager
from .server.websockets_server import WebSocketServerManager

# Dictionary to store instances of server managers for each connection
SERVER_MANAGERS = {}

def get_server_manager(connection_type, index):
    """
    Retrieves or creates a new server manager instance for the given connection type and index.
    If a different connection type was previously used, it removes the old one and creates a new instance.
    """
    # Check if the server manager already exists for this index
    if index in SERVER_MANAGERS:
        existing_manager, existing_type = SERVER_MANAGERS[index]
        
        # If the existing server manager is of a different type, remove it and create a new one
        if existing_type != connection_type:
            existing_manager.stop_server()  # Stop the current server if running
            remove_server_manager(index)  # Remove the current manager from the dictionary

    # If no server manager exists for this index or it was removed, create a new one
    if index not in SERVER_MANAGERS:
        # Create a new server manager based on the connection type
        if connection_type == "NAMED_PIPE":
            manager = PipeServerManager(index)
        elif connection_type == "MMAP":
            manager = MMFServerManager(index)
        elif connection_type == "WEBSOCKETS":
            manager = WebSocketServerManager(index)
        elif connection_type == "UDP":
            manager = UDPServerManager(index)
        else:
            raise ValueError(f"Unknown connection type: {connection_type}")
        
        SERVER_MANAGERS[index] = (manager, connection_type)
    
    return SERVER_MANAGERS[index][0]  # Return the manager instance

def remove_server_manager(index):
    """
    Removes the server manager instance for the given index from SERVER_MANAGERS and ensures it is properly shut down.
    """
    if index in SERVER_MANAGERS:
        server_manager, _ = SERVER_MANAGERS[index]
        if server_manager.is_running():
            server_manager.stop_server()  # Ensure the server is stopped before removing
        del SERVER_MANAGERS[index]
