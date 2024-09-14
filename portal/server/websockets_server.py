import asyncio
import queue
import threading

import bpy  # type: ignore

try:
    import aiohttp  # type: ignore
    from aiohttp import web  # type: ignore

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

from ..data_struct.packet import Packet
from ..handlers import BinaryHandler


class WebSocketServerManager:
    def __init__(self, index):
        self.index = index
        self.data_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        self._server_thread = None
        self._app = None
        self._runner = None
        self._site = None

    async def websocket_handler(self, request):
        if not DEPENDENCIES_AVAILABLE:
            return

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    raw_data = msg.data
                    Packet.validate_magic_number(raw_data[:2])
                    header = BinaryHandler.parse_header(raw_data[2:])
                    payload = raw_data[header.get_expected_size() + 2 :]
                    if header.is_compressed:
                        payload = BinaryHandler.decompress(payload)
                    if header.is_encrypted:
                        raise NotImplementedError("Encrypted data is not supported.")
                    self.data_queue.put(payload.decode("utf-8"))
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    raise RuntimeError(
                        f"WebSocket connection closed with exception {ws.exception()}"
                    )
                else:
                    raise ValueError(f"Unsupported message type: {msg.type}")
        except Exception as e:
            raise RuntimeError(f"Unhandled exception in websocket_handler: {e}")
        return ws

    async def run_server(self):
        if not DEPENDENCIES_AVAILABLE:
            return

        try:
            self._app = web.Application()
            connection = bpy.context.scene.portal_connections[self.index]
            route = "/"  # root route
            self._app.router.add_route("GET", route, self.websocket_handler)

            self._runner = web.AppRunner(self._app)
            await self._runner.setup()

            host = "0.0.0.0" if connection.is_external else "localhost"
            port = connection.port  # port specific to the connection
            self._site = web.TCPSite(self._runner, host, port)
            await self._site.start()

            while not self.shutdown_event.is_set():
                await asyncio.sleep(1)

            await self._runner.cleanup()
        except Exception as e:
            raise RuntimeError(f"Error creating or handling WebSocket server: {e}")

    def start_server(self):
        if not DEPENDENCIES_AVAILABLE:
            return

        self.shutdown_event.clear()
        self._server_thread = threading.Thread(
            target=asyncio.run, args=(self.run_server(),), daemon=True
        )
        self._server_thread.start()
        print(f"WebSocket server started for connection index: {self.index}")

    def stop_server(self):
        if not DEPENDENCIES_AVAILABLE:
            return

        self.shutdown_event.set()
        if self._server_thread:
            self._server_thread.join()
        print(f"WebSocket server stopped for connection index: {self.index}")

    def is_running(self):
        if not DEPENDENCIES_AVAILABLE:
            return False

        return self._server_thread is not None and self._server_thread.is_alive()

    def is_shutdown(self):
        if not DEPENDENCIES_AVAILABLE:
            return True
        return self.shutdown_event.is_set()
