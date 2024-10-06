import asyncio
import queue
import threading
import traceback

import bpy  # type: ignore

try:
    from aiohttp import ClientSession  # type: ignore

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

from ...data_struct.packet import Packet
from ...handlers.binary_handler import BinaryHandler
from ...utils.crypto import Crc16


class WebSocketSenderManager:
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
        self._client_thread = None
        self._last_checksum = None
        self._session = None
        self._ws = None
        self._loop = None  # asyncio loop reference

    def _run_loop_in_thread(self):
        """
        Initialize and run the asyncio event loop in a separate thread.
        """
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        # Schedule the send loop as a task
        self._loop.create_task(self._send_loop())
        try:
            self._loop.run_forever()
        finally:
            # Close the loop when run_forever is exited
            self._loop.close()

    async def _send_loop(self):
        """
        The main send loop that maintains the WebSocket connection and sends data from the queue.
        """
        if not DEPENDENCIES_AVAILABLE:
            print("Dependencies not available. Exiting send loop.")
            return

        try:
            async with ClientSession() as self._session:
                ws_url = f"ws://{self._connection.host}:{self._connection.port}/"
                async with self._session.ws_connect(ws_url) as self._ws:
                    print(f"Connected to WebSocket at {ws_url}")
                    while not self._shutdown_event.is_set():
                        try:
                            # Attempt to get data with a timeout
                            data = await self._loop.run_in_executor(
                                None, self.data_queue.get, True, 0.1
                            )
                            await self._send_data(data, is_compressed=False)
                            self.data_queue.task_done()
                        except queue.Empty:
                            await asyncio.sleep(0.1)  # Prevent tight loop
                        except Exception as e:
                            with self.error_lock:
                                self.error = e
                                self.traceback = traceback.format_exc()
                            print(f"Error in send loop: {e}")
        except Exception as e:
            with self.error_lock:
                self.error = e
                self.traceback = traceback.format_exc()
            print(f"WebSocket connection error: {e}")
        finally:
            await self._shutdown_sender()

    async def _send_data(self, data: str, is_compressed: bool = False):
        """
        Serialize and send data over the WebSocket connection.
        """
        try:
            data_bytes = data.encode("utf-8")
            checksum = Crc16().compute_checksum(data_bytes)

            # Skip sending if checksum matches previous data
            if self._last_checksum == checksum:
                print("Checksum matches previous data. Skipping send.")
                return

            if is_compressed:
                data_bytes = BinaryHandler.compress(data_bytes)

            # Create the packet header
            packet = Packet(
                data=data_bytes,
                size=len(data_bytes),
                checksum=checksum,
                is_encrypted=False,
                is_compressed=is_compressed,
            )

            await self._ws.send_bytes(packet.serialize())
            print(f"Sent WebSocket packet to {self._connection.host}:{self._connection.port}")
            self._last_checksum = checksum

        except Exception as e:
            with self.error_lock:
                self.error = e
                self.traceback = traceback.format_exc()
            print(f"Error sending WebSocket data: {e}")

    async def _shutdown_sender(self):
        """
        Gracefully shut down the WebSocket connection and the event loop.
        """
        try:
            if self._ws:
                await self._ws.close()
                print("WebSocket connection closed.")
            if self._session:
                await self._session.close()
                print("Client session closed.")
        except Exception as e:
            with self.error_lock:
                self.error = e
                self.traceback = traceback.format_exc()
            print(f"Error during shutdown: {e}")
        finally:
            # Schedule loop.stop() to be called in the event loop's thread
            self._loop.call_soon_threadsafe(self._loop.stop)

    def start_server(self):
        """
        Start the WebSocket sender in a separate thread.
        """
        if not DEPENDENCIES_AVAILABLE:
            print("aiohttp is not available. Cannot start WebSocket sender.")
            return

        if self._client_thread and self._client_thread.is_alive():
            print("WebSocket sender is already running.")
            return

        self._shutdown_event.clear()
        self._client_thread = threading.Thread(target=self._run_loop_in_thread, daemon=True)
        self._client_thread.start()
        print(
            f"WebSocket sender started for connection uuid: {self.uuid}, name: {self._connection.name}"
        )

    def stop_server(self):
        """
        Gracefully stop the WebSocket sender.
        """
        if not DEPENDENCIES_AVAILABLE:
            print("aiohttp is not available. WebSocket sender was not started.")
            return

        if not self._client_thread:
            print("WebSocket sender was not started.")
            return

        self._shutdown_event.set()
        if self._loop:
            # Schedule the shutdown coroutine
            future = asyncio.run_coroutine_threadsafe(self._shutdown_sender(), self._loop)
            try:
                future.result(timeout=5)  # Wait for shutdown to complete
            except asyncio.TimeoutError:
                print("Shutdown timed out. Forcing loop stop.")
                self._loop.call_soon_threadsafe(self._loop.stop)

        if self._client_thread:
            self._client_thread.join(timeout=5)
            if self._client_thread.is_alive():
                print("Client thread is still running after shutdown attempt.")
            else:
                print(
                    f"WebSocket sender stopped for connection uuid: {self.uuid}, name: {self._connection.name}"
                )
            self._client_thread = None

    def is_running(self):
        """
        Check if the sender thread is running.
        """
        return self._client_thread is not None and self._client_thread.is_alive()

    def is_shutdown(self):
        """
        Check if the sender has been shut down.
        """
        return self._shutdown_event.is_set()
