import queue
import threading
import traceback

import bpy  # type: ignore

from ..data_struct.packet import Packet, PacketHeader
from ..handlers.binary_handler import BinaryHandler

# Attempt to import the pywin32 modules safely
try:
    import pywintypes  # type: ignore
    import win32event  # type: ignore
    import win32file  # type: ignore
    import win32pipe  # type: ignore

    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False


class PipeServerManager:
    def __init__(self, uuid):
        self.uuid = uuid
        self.connection = next(
            (conn for conn in bpy.context.scene.portal_connections if conn.uuid == self.uuid),
            None,
        )
        self.data_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        self.pipe_handle = None
        self.pipe_event = None
        self._server_thread = None
        self.error = None
        self.traceback = None
        self.error_lock = threading.Lock()

    def _handle_raw_bytes(self, pipe):
        if not PYWIN32_AVAILABLE:
            return
        try:
            while not self.shutdown_event.is_set():
                try:
                    signature = win32file.ReadFile(pipe, 2, None)[1]
                    Packet.validate_magic_number(signature)
                    header_bytes = win32file.ReadFile(pipe, PacketHeader.get_expected_size(), None)[
                        1
                    ]
                    header = BinaryHandler.parse_header(header_bytes)
                    data = win32file.ReadFile(pipe, header.size, None)[1]
                    if header.is_compressed:
                        data = BinaryHandler.decompress(data)
                    if header.is_encrypted:
                        raise NotImplementedError("Encrypted data is not supported.")
                    self.data_queue.put(data.decode("utf-8"))
                except pywintypes.error as e:
                    if e.winerror == 109:  # ERROR_BROKEN_PIPE
                        break
                    raise
        except Exception as e:
            with self.error_lock:
                self.traceback = traceback.format_exc()
                self.error = e

    def _run_server(self):
        if not PYWIN32_AVAILABLE:
            return
        while not self.shutdown_event.is_set():
            try:
                pipe_name = rf"\\.\pipe\{self.connection.name}"
                print(f"Creating pipe: {pipe_name}")
                self.pipe_handle = win32pipe.CreateNamedPipe(
                    pipe_name,
                    win32pipe.PIPE_ACCESS_INBOUND | win32file.FILE_FLAG_OVERLAPPED,
                    win32pipe.PIPE_TYPE_MESSAGE
                    | win32pipe.PIPE_READMODE_MESSAGE
                    | win32pipe.PIPE_WAIT,
                    1,
                    65536,
                    65536,
                    0,
                    None,
                )
                self.pipe_event = win32event.CreateEvent(None, True, False, None)
                overlapped = pywintypes.OVERLAPPED()
                overlapped.hEvent = self.pipe_event
                win32pipe.ConnectNamedPipe(self.pipe_handle, overlapped)
                while not self.shutdown_event.is_set():
                    rc = win32event.WaitForSingleObject(self.pipe_event, 100)
                    if rc == win32event.WAIT_OBJECT_0:
                        self._handle_raw_bytes(self.pipe_handle)
                        win32pipe.DisconnectNamedPipe(self.pipe_handle)
                        win32pipe.ConnectNamedPipe(self.pipe_handle, overlapped)

            except pywintypes.error as e:
                if e.winerror != 233:  # Not DisconnectedNamedPipe
                    with self.error_lock:
                        self.traceback = traceback.format_exc()
                        self.error = e
                if self.shutdown_event.is_set():
                    break
            except Exception as e:
                with self.error_lock:
                    self.error = e
            finally:
                self.close_handles()

    def close_handles(self):
        if self.pipe_handle:
            try:
                # Disconnect the named pipe
                win32pipe.DisconnectNamedPipe(self.pipe_handle)
            except pywintypes.error as e:
                if e.winerror == 233:  # no process is on the other end of the pipe
                    pass
                else:
                    raise (f"Error disconnecting pipe: {e}")

            # Close the pipe handle
            win32file.CloseHandle(self.pipe_handle)
            self.pipe_handle = None

        if self.pipe_event:
            # Close the event handle
            win32file.CloseHandle(self.pipe_event)
            self.pipe_event = None

        # Clear the data queue
        with self.data_queue.mutex:
            self.data_queue.queue.clear()

    def start_server(self):
        self.shutdown_event.clear()
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()
        print(f"Pipe listener started for connection uuid: {self.uuid}, name: {self.connection.name}")

    def stop_server(self):
        self.shutdown_event.set()
        if self.pipe_handle:
            try:
                win32pipe.DisconnectNamedPipe(self.pipe_handle)
            except pywintypes.error:
                pass
        if self.pipe_event:
            win32event.SetEvent(self.pipe_event)
        if self._server_thread:
            self._server_thread.join()
        self.close_handles()
        print(f"Pipe listener stopped for connection uuid: {self.uuid}, name: {self.connection.name}")

    def is_running(self):
        if not PYWIN32_AVAILABLE:
            return False
        return self._server_thread is not None and self._server_thread.is_alive()

    def is_shutdown(self):
        if not PYWIN32_AVAILABLE:
            return True
        return self.shutdown_event.is_set()
