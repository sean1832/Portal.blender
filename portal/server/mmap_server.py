import mmap
import queue
import threading
import time

import bpy  # type: ignore

from ..data_struct.packet import Packet, PacketHeader
from ..handlers import BinaryHandler


class MMFServerManager:
    data_queue = queue.Queue()
    shutdown_event = threading.Event()
    _server_thread = None
    _last_checksum = None
    mmf = None

    @staticmethod
    def handle_raw_bytes(mmf):
        try:
            while not MMFServerManager.shutdown_event.is_set():
                mmf.seek(0)
                if mmf.size() >= 10:
                    Packet.validate_magic_number(mmf.read(2))
                    header = BinaryHandler.parse_header(mmf.read(PacketHeader.get_expected_size()))
                    checksum = header.Checksum
                    # Only process data if checksum is different from the last one
                    if checksum != MMFServerManager._last_checksum:
                        print(
                            f"isCompressed: {header.IsCompressed}, isEncrypted: {header.IsEncrypted}, checksum: {checksum}, size: {header.Size}"
                        )
                        MMFServerManager._last_checksum = checksum
                        data = mmf.read(header.Size)
                        if header.IsCompressed:
                            data = BinaryHandler.decompress(data)
                        try:
                            decoded_data = data.decode("utf-8")
                        except UnicodeDecodeError:
                            raise ValueError("Received data cannot be decoded as UTF-8.")
                        MMFServerManager.data_queue.put(decoded_data)
                    time.sleep(bpy.context.scene.event_timer)
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

    @staticmethod
    def run_server():
        while not MMFServerManager.shutdown_event.is_set():
            try:
                mmf_name = bpy.context.scene.mmf_name
                buffer_size = bpy.context.scene.buffer_size * 1024  # Convert KB to bytes
                MMFServerManager.mmf = mmap.mmap(-1, buffer_size, tagname=mmf_name)
                MMFServerManager.handle_raw_bytes(MMFServerManager.mmf)
            except Exception as e:
                if MMFServerManager.shutdown_event.is_set():
                    break
                time.sleep(1)
                raise RuntimeError(f"Error creating or handling MMF: {e}")
            finally:
                MMFServerManager.close_mmf()

    @staticmethod
    def close_mmf():
        if MMFServerManager.mmf:
            MMFServerManager.mmf.close()
            MMFServerManager.mmf = None

    @staticmethod
    def start_server():
        MMFServerManager.shutdown_event.clear()
        MMFServerManager._server_thread = threading.Thread(
            target=MMFServerManager.run_server, daemon=True
        )
        MMFServerManager._server_thread.start()
        print("MMF server started...")

    @staticmethod
    def stop_server():
        MMFServerManager.shutdown_event.set()
        if MMFServerManager._server_thread:
            MMFServerManager._server_thread.join()
        print("MMF server stopped...")

    @staticmethod
    def is_running():
        return (
            MMFServerManager._server_thread is not None
            and MMFServerManager._server_thread.is_alive()
        )

    @staticmethod
    def is_shutdown():
        return MMFServerManager.shutdown_event.is_set()
