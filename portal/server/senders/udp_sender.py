import socket
import threading
import traceback
import queue

import bpy  # type: ignore

from ...handlers.binary_handler import BinaryHandler
from ...data_struct.packet import Packet
from ...utils.crypto import Crc16


class UDPSenderManager:
    def __init__(self, uuid):
        self.uuid = uuid
        self.connection = next(
            (conn for conn in bpy.context.scene.portal_connections if conn.uuid == self.uuid),
            None,
        )
        self.shutdown_event = threading.Event()
        self._server_thread = None
        self._sock = None
        self.error = None
        self.traceback = None
        self.error_lock = threading.Lock()
        self.data_queue = queue.Queue()
        self._last_checksum = None

    def _send_data(self, data: str, is_compressed=False):
        try:
            # Resolve the connection address and port
            host = self.connection.host
            port = self.connection.port

            # Create UDP socket
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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

            # Send the data to the destination
            self._sock.sendto(packet.serialize(), (host, port))
            print(f"Sent UDP packet to {host}:{port}")
            self._last_checksum = checksum

        except Exception as e:
            with self.error_lock:
                self.traceback = traceback.format_exc()
                self.error = RuntimeError(f"Error sending UDP packet: {e}")
        finally:
            if self._sock:
                self._sock.close()

    def _run_sender(self):
        while not self.shutdown_event.is_set():
            try:
                data = self.data_queue.get(timeout=0.1)
                self._send_data(data)
            except Exception as e:
                with self.error_lock:
                    self.traceback = traceback.format_exc()
                    self.error = e
            if self.shutdown_event.is_set():
                break

    def start_server(self):
        self.shutdown_event.clear()
        self._server_thread = threading.Thread(target=self._run_sender, daemon=True)
        self._server_thread.start()
        print(f"UDP sender started for connection uuid: {self.uuid}, name: {self.connection.name}")

    def stop_server(self):
        self.shutdown_event.set()
        if self._server_thread:
            self._server_thread.join()
        print(f"UDP sender stopped for connection uuid: {self.uuid}, name: {self.connection.name}")

    def is_running(self):
        return self._server_thread is not None and self._server_thread.is_alive()

    def is_shutdown(self):
        return self.shutdown_event.is_set()
