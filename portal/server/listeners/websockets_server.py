import asyncio
import queue
import threading
import traceback

import bpy  # type: ignore

try:
    import aiohttp  # type: ignore
    from aiohttp import web  # type: ignore

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

from ...data_struct.packet import Packet
from ...handlers.binary_handler import BinaryHandler


class WebSocketListenerManager:
    def __init__(self, uuid):
        self.uuid = uuid
        self.error = None
        self.error_lock = threading.Lock()
        self.traceback = None
        self.data_queue = queue.Queue()

        # private
        self._connection = next(
            (conn for conn in bpy.context.scene.portal_connections if conn.uuid == self.uuid),
            None,
        )
        self._shutdown_event = threading.Event()
        self._server_thread = None
        self._app = None
        self._runner = None
        self._site = None
        self._loop = None  # asyncio loop reference

    async def _websocket_handler(self, request):
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
            with self.error_lock:
                self.traceback = traceback.format_exc()
                self.error = RuntimeError(f"Error handling WebSocket message: {e}")
        finally:
            await ws.close()
        return ws

    async def _run_server(self):
        if not DEPENDENCIES_AVAILABLE:
            return

        try:
            self._app = web.Application()
            route = "/"  # root route
            self._app.router.add_route("GET", route, self._websocket_handler)

            self._runner = web.AppRunner(self._app)
            await self._runner.setup()

            host = "0.0.0.0" if self._connection.is_external else "localhost"
            port = self._connection.port  # port specific to the connection
            self._site = web.TCPSite(self._runner, host, port)
            await self._site.start()

            while not self._shutdown_event.is_set():
                try:
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    break  # Properly exit the loop when the task is cancelled

            await self._runner.cleanup()
        except Exception as e:
            with self.error_lock:
                self.traceback = traceback.format_exc()
                self.error = RuntimeError(f"Error creating or handling WebSocket server: {e}")

    def start_server(self):
        if not DEPENDENCIES_AVAILABLE:
            return

        self._shutdown_event.clear()
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._server_thread = threading.Thread(target=self._run_loop_in_thread, daemon=True)
        self._server_thread.start()

        print(
            f"WebSocket server started for connection uuid: {self.uuid}, name: {self._connection.name}"
        )

    def _run_loop_in_thread(self):
        self._loop.run_until_complete(self._run_server())
        self._loop.run_forever()

    async def _shutdown_server(self):
        if self._runner:
            # Get the current task (the one running shutdown_server)
            current_task = asyncio.current_task(loop=self._loop)

            # Cancel all other tasks except the current one
            tasks = [
                task
                for task in asyncio.all_tasks(self._loop)
                if task is not current_task and not task.done()
            ]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

            # Clean up the site and runner
            await self._runner.cleanup()

        # Stop the loop
        self._loop.stop()

    def stop_server(self):
        if not DEPENDENCIES_AVAILABLE:
            return

        self._shutdown_event.set()
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._shutdown_server(), self._loop)

        if self._server_thread:
            self._server_thread.join(1)

        print(
            f"WebSocket server stopped for connection uuid: {self.uuid}, name: {self._connection.name}"
        )

    def is_running(self):
        if not DEPENDENCIES_AVAILABLE:
            return False

        return self._server_thread is not None and self._server_thread.is_alive()

    def is_shutdown(self):
        if not DEPENDENCIES_AVAILABLE:
            return True
        return self._shutdown_event.is_set()
