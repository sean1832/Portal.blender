import queue
import threading
import time
import traceback

import bpy

from ...data_struct.packet import Packet
from ...handlers.binary_handler import BinaryHandler
from ...utils.crypto import Crc16

try:
    import pywintypes  # type: ignore
    import win32event  # type: ignore
    import win32file  # type: ignore
    import win32pipe  # type: ignore

    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False


class PipeSenderManager:
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
        self._pipe_handle = None

    def _connect_to_pipe(self):
        """Attempt to connect to the named pipe server."""
        pipe_name = rf"\\.\pipe\{self._connection.name}"
        while not self._shutdown_event.is_set():
            try:
                # Try to open the named pipe in overlapped mode
                self._pipe_handle = win32file.CreateFile(
                    pipe_name,
                    win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    win32file.FILE_FLAG_OVERLAPPED,
                    None,
                )
                print(f"Connected to pipe: {pipe_name}")
                break  # Exit loop on successful connection
            except pywintypes.error as e:
                if e.winerror == 2:  # ERROR_FILE_NOT_FOUND
                    # Pipe not available yet, wait and retry
                    time.sleep(0.1)
                elif e.winerror == 231:  # ERROR_PIPE_BUSY
                    # All pipe instances are busy, wait for availability
                    if not win32pipe.WaitNamedPipe(pipe_name, 2000):
                        print("Pipe is busy, retrying...")
                        time.sleep(0.1)
                else:
                    with self.error_lock:
                        self.error = e
                        self.traceback = traceback.format_exc()
                    break

    def _send_loop(self):
        if not PYWIN32_AVAILABLE:
            return
        print(f"Starting send loop for pipe: {self._connection.name}")

        self._connect_to_pipe()

        if self._pipe_handle is None:
            print("Failed to connect to pipe.")
            return

        try:
            while not self._shutdown_event.is_set():
                try:
                    data = self.data_queue.get(timeout=0.1)
                    self._send(data, compress=True)
                    self.data_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    with self.error_lock:
                        self.error = e
                        self.traceback = traceback.format_exc()
                    break
        finally:
            self._close_handles()

    def _send(self, data: str, compress: bool = False):
        """Send data to the named pipe."""
        try:
            data_bytes = data.encode("utf-8")
            checksum = Crc16().compute_checksum(data_bytes)

            # Skip sending if checksum matches previous data
            if self._last_checksum == checksum:
                return

            if compress:
                data_bytes = BinaryHandler.compress(data_bytes)

            packet = Packet(
                data_bytes,
                is_encrypted=False,
                is_compressed=compress,
                size=len(data_bytes),
                checksum=checksum,
            )

            overlapped = pywintypes.OVERLAPPED()
            overlapped.hEvent = win32event.CreateEvent(None, True, False, None)

            # Write data to the pipe asynchronously
            win32file.WriteFile(self._pipe_handle, packet.serialize(), overlapped)
            # Wait for the write operation to complete
            win32event.WaitForSingleObject(overlapped.hEvent, win32event.INFINITE)
            win32file.CloseHandle(overlapped.hEvent)

            self._last_checksum = checksum
        except pywintypes.error as e:
            with self.error_lock:
                self.error = e
                self.traceback = traceback.format_exc()

    def _close_handles(self):
        """Close the pipe handle."""
        if self._pipe_handle:
            try:
                win32file.CloseHandle(self._pipe_handle)
            except pywintypes.error:
                pass
            self._pipe_handle = None

    def start_server(self):
        self._shutdown_event.clear()
        self._client_thread = threading.Thread(target=self._send_loop, daemon=True)
        self._client_thread.start()
        print(
            f"Pipe sender started for connection uuid: {self.uuid}, name: {self._connection.name}"
        )

    def stop_server(self):
        """Gracefully stop the sender."""
        self._shutdown_event.set()
        if self._client_thread:
            self._client_thread.join()
        self._close_handles()
        print(
            f"Pipe sender stopped for connection uuid: {self.uuid}, name: {self._connection.name}"
        )

    def is_running(self):
        return self._client_thread is not None and self._client_thread.is_alive()

    def is_shutdown(self):
        return self._shutdown_event.is_set()
