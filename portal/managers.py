from .server.mmap_server import MMFServerManager
from .server.pipe_server import PipeServerManager
from .server.udp_server import UDPServerManager
from .server.websockets_server import WebSocketServerManager

SERVER_MANAGERS = {
    "NAMED_PIPE": PipeServerManager,
    "MMAP": MMFServerManager,
    "WEBSOCKETS": WebSocketServerManager,
    "UDP": UDPServerManager,
}
