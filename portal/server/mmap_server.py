import mmap
import queue
import threading
import time

import bpy  # type: ignore

from ..data_struct.packet import Packet, PacketHeader
from ..handlers.binary_handler import BinaryHandler


class MMFServerManager:
    def __init__(self, uuid):
        self.uuid = uuid
        self.connection = next(
            (conn for conn in bpy.context.scene.portal_connections if conn.uuid == self.uuid),
            None,
        )
        self.data_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        self._server_thread = None
        self._last_checksum = None
        self.mmf = None

    def handle_raw_bytes(self):
        try:
            while not self.shutdown_event.is_set():
                self.mmf.seek(0)
                if self.mmf.size() >= 10:
                    Packet.validate_magic_number(self.mmf.read(2))
                    header = BinaryHandler.parse_header(
                        self.mmf.read(PacketHeader.get_expected_size())
                    )
                    checksum = header.Checksum
                    # Only process data if checksum is different from the last one
                    if checksum != self._last_checksum:
                        print(
                            f"isCompressed: {header.IsCompressed}, isEncrypted: {header.IsEncrypted}, checksum: {checksum}, size: {header.Size}"
                        )
                        self._last_checksum = checksum
                        data = self.mmf.read(header.Size)
                        if header.IsCompressed:
                            data = BinaryHandler.decompress(data)
                        if header.IsEncrypted:
                            raise NotImplementedError("Encrypted data is not supported.")
                        try:
                            decoded_data = data.decode("utf-8")
                        except UnicodeDecodeError:
                            raise ValueError("Received data cannot be decoded as UTF-8.")
                        self.data_queue.put(decoded_data)
                    time.sleep(self.connection.event_timer)
                else:
                    raise ValueError(
                        "Not enough data to read hash & length prefix. "
                        + "Packet should follow the format: \n"
                        + "'[2b byte[] magic_num] [1b bool isCompressed] [1b bool isEncrypted] [2b int16 checksum] [4b int32 size] [payload]'"
                    )
        except ValueError as ve:
            raise RuntimeError(f"Value Error in handle_mmf_data: {ve}")
        except Exception as e:
            raise RuntimeError(f"Error in handle_mmf_data: {e}")

    def run_server(self):
        while not self.shutdown_event.is_set():
            try:
                mmf_name = self.connection.name
                buffer_size = self.connection.buffer_size * 1024  # Convert KB to bytes
                self.mmf = mmap.mmap(-1, buffer_size, tagname=mmf_name)
                self.handle_raw_bytes()
            except Exception as e:
                if self.shutdown_event.is_set():
                    break
                time.sleep(1)
                raise RuntimeError(f"Error creating or handling MMF: {e}")
            finally:
                self.close_mmf()

    def close_mmf(self):
        if self.mmf:
            self.mmf.close()
            self.mmf = None

    def start_server(self):
        self.shutdown_event.clear()
        self._server_thread = threading.Thread(target=self.run_server, daemon=True)
        self._server_thread.start()
        print(f"MMF server started for connection uuid: {self.uuid}, name: {self.connection.name}")

    def stop_server(self):
        self.shutdown_event.set()
        if self._server_thread:
            self._server_thread.join()
        self.close_mmf()
        print(f"MMF server stopped for connection uuid: {self.uuid}, name: {self.connection.name}")

    def is_running(self):
        return self._server_thread is not None and self._server_thread.is_alive()

    def is_shutdown(self):
        return self.shutdown_event.is_set()
