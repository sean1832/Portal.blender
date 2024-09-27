import mmap
import threading
import traceback

import bpy  # type: ignore

from ...data_struct.packet import Packet
from ...handlers.binary_handler import BinaryHandler
from ...utils.crypto import Crc16


class MMFSenderManager:
    def __init__(self, uuid):
        self.uuid = uuid
        self.connection = next(
            (conn for conn in bpy.context.scene.portal_connections if conn.uuid == self.uuid),
            None,
        )
        self.shutdown_event = threading.Event()
        self.mmf = None
        self._server_thread = None
        self.error = None
        self.traceback = None
        self.error_lock = threading.Lock()
        self._last_checksum = None

    def _send_data(self, data: str, is_compressed=False):
        if not self.mmf:
            return
        try:
            self.mmf.seek(0)
            data_bytes = data.encode("utf-8")
            checksum = Crc16().compute_checksum(data_bytes)
            if checksum == self._last_checksum:
                return

            if is_compressed:
                data_bytes = BinaryHandler.compress(data_bytes)

            # Create the packet header
            packet = Packet(
                data=data_bytes,
                size=len(data_bytes),
                checksum=checksum,
                is_compressed=is_compressed,
                is_encrypted=False,
            )

            # Write data to the mmap buffer
            self.mmf.write(packet.serialize())  # Write actual data
            self._last_checksum = checksum

        except Exception as e:
            with self.error_lock:
                self.traceback = traceback.format_exc()
                self.error = e

    def _run_sender(self, data: str):
        try:
            mmf_name = self.connection.name
            buffer_size = self.connection.buffer_size * 1024  # Convert KB to bytes
            self.mmf = mmap.mmap(-1, buffer_size, tagname=mmf_name)
            self._send_data(data)
        except Exception as e:
            with self.error_lock:
                self.traceback = traceback.format_exc()
                self.error = e
        finally:
            self._close_mmf()

    def _close_mmf(self):
        if self.mmf:
            self.mmf.close()
            self.mmf = None

    def start_server(self, data: str):
        self.shutdown_event.clear()
        self._server_thread = threading.Thread(target=self._run_sender, args=(data,), daemon=True)
        self._server_thread.start()
        print(f"MMF sender started for connection uuid: {self.uuid}, name: {self.connection.name}")

    def stop_server(self):
        self.shutdown_event.set()
        if self._server_thread:
            self._server_thread.join()
        self._close_mmf()
        print(f"MMF sender stopped for connection uuid: {self.uuid}, name: {self.connection.name}")

    def is_running(self):
        return self._server_thread is not None and self._server_thread.is_alive()

    def is_shutdown(self):
        return self.shutdown_event.is_set()
