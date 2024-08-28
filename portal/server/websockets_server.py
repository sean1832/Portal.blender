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

from ..handlers import BinaryHandler


class WebSocketServerManager:
    data_queue = queue.Queue()
    shutdown_event = threading.Event()
    _server_thread = None
    _app = None
    _runner = None
    _site = None

    @staticmethod
    async def websocket_handler(request):
        if not DEPENDENCIES_AVAILABLE:
            return

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    data = msg.data
                    data = BinaryHandler.decompress_if_gzip(data)
                    WebSocketServerManager.data_queue.put(data.decode("utf-8"))
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    raise RuntimeError(
                        f"WebSocket connection closed with exception {ws.exception()}"
                    )
                else:
                    raise ValueError(f"Unsupported message type: {msg.type}")
        except Exception as e:
            raise RuntimeError(f"Unhandled exception in websocket_handler: {e}")
        return ws

    @staticmethod
    async def run_server():
        if not DEPENDENCIES_AVAILABLE:
            return

        try:
            WebSocketServerManager._app = web.Application()
            route = bpy.context.scene.route  # blender input
            WebSocketServerManager._app.router.add_route(
                "GET", route, WebSocketServerManager.websocket_handler
            )

            WebSocketServerManager._runner = web.AppRunner(WebSocketServerManager._app)
            await WebSocketServerManager._runner.setup()

            host = "0.0.0.0" if bpy.context.scene.is_external else "localhost"
            port = bpy.context.scene.port  # blender input
            WebSocketServerManager._site = web.TCPSite(WebSocketServerManager._runner, host, port)
            await WebSocketServerManager._site.start()

            while not WebSocketServerManager.shutdown_event.is_set():
                await asyncio.sleep(1)

            await WebSocketServerManager._runner.cleanup()
        except Exception as e:
            raise RuntimeError(f"Error creating or handling WebSocket server: {e}")

    @staticmethod
    def start_server():
        if not DEPENDENCIES_AVAILABLE:
            return

        WebSocketServerManager.shutdown_event.clear()
        WebSocketServerManager._server_thread = threading.Thread(
            target=asyncio.run, args=(WebSocketServerManager.run_server(),), daemon=True
        )
        WebSocketServerManager._server_thread.start()
        print("WebSocket server started...")

    @staticmethod
    def stop_server():
        if not DEPENDENCIES_AVAILABLE:
            return

        WebSocketServerManager.shutdown_event.set()
        if WebSocketServerManager._server_thread:
            WebSocketServerManager._server_thread.join()
        print("WebSocket server stopped...")

    @staticmethod
    def is_running():
        if not DEPENDENCIES_AVAILABLE:
            return False

        return (
            WebSocketServerManager._server_thread is not None
            and WebSocketServerManager._server_thread.is_alive()
        )

    @staticmethod
    def is_shutdown():
        if not DEPENDENCIES_AVAILABLE:
            return True
        return WebSocketServerManager.shutdown_event.is_set()
