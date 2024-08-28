import queue
import struct
import threading
import time

import bpy  # type: ignore

from ..handlers import BinaryHandler

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
    data_queue = queue.Queue()
    shutdown_event = threading.Event()
    pipe_handle = None
    pipe_event = None
    _server_thread = None

    @staticmethod
    def handle_raw_bytes(pipe):
        if not PYWIN32_AVAILABLE:
            return
        try:
            while not PipeServerManager.shutdown_event.is_set():
                try:
                    size_prefix = win32file.ReadFile(pipe, 4, None)[1]
                    (size,) = struct.unpack("I", size_prefix)
                    if size == 0:
                        break

                    data = win32file.ReadFile(pipe, size, None)[1]
                    data = BinaryHandler.decompress_if_gzip(data).decode("utf-8")
                    PipeServerManager.data_queue.put(data)
                except pywintypes.error as e:
                    if e.winerror == 109:  # ERROR_BROKEN_PIPE
                        break
                    raise
        except Exception as e:
            raise RuntimeError(f"Error in handle_raw_bytes: {e}")

    @staticmethod
    def run_server():
        if not PYWIN32_AVAILABLE:
            return
        while not PipeServerManager.shutdown_event.is_set():
            try:
                pipe_name = rf"\\.\pipe\{bpy.context.scene.pipe_name}"
                PipeServerManager.pipe_handle = win32pipe.CreateNamedPipe(
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
                PipeServerManager.pipe_event = win32event.CreateEvent(None, True, False, None)
                overlapped = pywintypes.OVERLAPPED()
                overlapped.hEvent = PipeServerManager.pipe_event

                win32pipe.ConnectNamedPipe(PipeServerManager.pipe_handle, overlapped)

                while not PipeServerManager.shutdown_event.is_set():
                    rc = win32event.WaitForSingleObject(PipeServerManager.pipe_event, 100)
                    if rc == win32event.WAIT_OBJECT_0:
                        PipeServerManager.handle_raw_bytes(PipeServerManager.pipe_handle)
                        win32pipe.DisconnectNamedPipe(PipeServerManager.pipe_handle)
                        win32pipe.ConnectNamedPipe(PipeServerManager.pipe_handle, overlapped)

            except pywintypes.error as e:
                if e.winerror != 233:  # Not DisconnectedNamedPipe
                    print(f"Error creating or handling pipe: {e}")
                if PipeServerManager.shutdown_event.is_set():
                    break
                time.sleep(1)
            finally:
                PipeServerManager.close_handles()

    @staticmethod
    def close_handles():
        if PipeServerManager.pipe_handle:
            try:
                # Disconnect the named pipe
                win32pipe.DisconnectNamedPipe(PipeServerManager.pipe_handle)
            except pywintypes.error as e:
                if e.winerror == 233:  # no process is on the other end of the pipe
                    pass
                else:
                    raise (f"Error disconnecting pipe: {e}")

            # Close the pipe handle
            win32file.CloseHandle(PipeServerManager.pipe_handle)
            PipeServerManager.pipe_handle = None

        if PipeServerManager.pipe_event:
            # Close the event handle
            win32file.CloseHandle(PipeServerManager.pipe_event)
            PipeServerManager.pipe_event = None

        # Clear the data queue
        with PipeServerManager.data_queue.mutex:
            PipeServerManager.data_queue.queue.clear()

    @staticmethod
    def start_server():
        PipeServerManager.shutdown_event.clear()
        PipeServerManager._server_thread = threading.Thread(
            target=PipeServerManager.run_server, daemon=True
        )
        PipeServerManager._server_thread.start()
        print("Pipe server started...")

    @staticmethod
    def stop_server():
        PipeServerManager.shutdown_event.set()
        if PipeServerManager.pipe_handle:
            try:
                win32pipe.DisconnectNamedPipe(PipeServerManager.pipe_handle)
            except pywintypes.error:
                pass
        if PipeServerManager.pipe_event:
            win32event.SetEvent(PipeServerManager.pipe_event)
        if PipeServerManager._server_thread:
            PipeServerManager._server_thread.join()
        PipeServerManager.close_handles()
        print("Pipe server stopped...")

    @staticmethod
    def is_running():
        if not PYWIN32_AVAILABLE:
            return False
        return (
            PipeServerManager._server_thread is not None
            and PipeServerManager._server_thread.is_alive()
        )

    @staticmethod
    def is_shutdown():
        if not PYWIN32_AVAILABLE:
            return True
        return PipeServerManager.shutdown_event.is_set()
