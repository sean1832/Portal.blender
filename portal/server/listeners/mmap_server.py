import mmap
import queue
import threading
import time
import traceback

import bpy  # type: ignore

from ...data_struct.packet import Packet, PacketHeader
from ...handlers.binary_handler import BinaryHandler


class MMFListenerManager:
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
        self._last_checksum = None
        self._mmf = None

    def _handle_raw_bytes(self):
        try:
            while not self._shutdown_event.is_set():
                self._mmf.seek(0)
                if self._mmf.size() >= 10:
                    Packet.validate_magic_number(self._mmf.read(2))
                    header = BinaryHandler.parse_header(
                        self._mmf.read(PacketHeader.get_expected_size())
                    )
                    checksum = header.Checksum
                    # Only process data if checksum is different from the last one
                    if checksum != self._last_checksum:
                        print(
                            f"isCompressed: {header.IsCompressed}, isEncrypted: {header.IsEncrypted}, checksum: {checksum}, size: {header.Size}"
                        )
                        self._last_checksum = checksum
                        data = self._mmf.read(header.Size)
                        if header.IsCompressed:
                            data = BinaryHandler.decompress(data)
                        if header.IsEncrypted:
                            raise NotImplementedError("Encrypted data is not supported.")
                        try:
                            decoded_data = data.decode("utf-8")
                        except UnicodeDecodeError:
                            raise ValueError("Received data cannot be decoded as UTF-8.")
                        self.data_queue.put(decoded_data)
                    time.sleep(self._connection.event_timer)
                else:
                    raise ValueError(
                        "Not enough data to read hash & length prefix. "
                        + "Packet should follow the format: \n"
                        + "'[2b byte[] magic_num] [1b bool isCompressed] [1b bool isEncrypted] [2b int16 checksum] [4b int32 size] [payload]'"
                    )
        except ValueError as ve:
            with self.error_lock:
                self.traceback = traceback.format_exc()
                self.error = ve
            print
        except Exception as e:
            with self.error_lock:
                self.traceback = traceback.format_exc()
                self.error = e

    def _run_server(self):
        while not self._shutdown_event.is_set():
            try:
                mmf_name = self._connection.name
                buffer_size = self._connection.buffer_size * 1024  # Convert KB to bytes
                self._mmf = mmap.mmap(-1, buffer_size, tagname=mmf_name)
                self._handle_raw_bytes()
            except Exception as e:
                with self.error_lock:
                    self.traceback = traceback.format_exc()
                    self.error = e
                if self._shutdown_event.is_set():
                    break
            finally:
                self._close_mmf()

    def _close_mmf(self):
        if self._mmf:
            self._mmf.close()
            self._mmf = None

    def start_server(self):
        self._shutdown_event.clear()
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()
        print(f"MMF server started for connection uuid: {self.uuid}, name: {self._connection.name}")

    def stop_server(self):
        self._shutdown_event.set()
        if self._server_thread:
            self._server_thread.join()
        self._close_mmf()
        print(f"MMF server stopped for connection uuid: {self.uuid}, name: {self._connection.name}")

    def is_running(self):
        return self._server_thread is not None and self._server_thread.is_alive()

    def is_shutdown(self):
        return self._shutdown_event.is_set()
