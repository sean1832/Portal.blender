import mmap
import queue
import struct
import threading
import time

import bpy  # type: ignore

from ..handlers import BinaryHandler


class MMFServerManager:
    data_queue = queue.Queue()
    shutdown_event = threading.Event()
    _server_thread = None
    _last_hash = None
    mmf = None

    @staticmethod
    def handle_raw_bytes(mmf):
        try:
            while not MMFServerManager.shutdown_event.is_set():
                mmf.seek(0)
                if mmf.size() >= 20:
                    hash_prefix = mmf.read(16)  # md5 hash is 16 bytes

                    # Check if the data is the same as the last read
                    if hash_prefix != MMFServerManager._last_hash:
                        MMFServerManager._last_hash = hash_prefix
                        length_prefix = mmf.read(4)
                        data_length = struct.unpack("I", length_prefix)[0]
                        print(f"Data length: {data_length}")

                        if data_length > 0 and mmf.size() >= 4 + data_length:
                            data = mmf.read(data_length)
                            data = BinaryHandler.decompress_if_gzip(data)
                            MMFServerManager.data_queue.put(data.decode("utf-8"))
                        else:
                            print("Data length exceeds the current readable size.")
                    else:
                        # print("Data is the same as the last read.")
                        pass
                else:
                    print(
                        "Data Struct Error: Not enough data to read hash & length prefix."
                        + "\nData should follows the format: '[16b byte[] hash] [4b int32 length] [data]'"
                    )
                time.sleep(bpy.context.scene.event_timer)  # Adjust as needed
        except Exception as e:
            print(f"Error in handle_mmf_data: {e}")

    @staticmethod
    def run_server():
        while not MMFServerManager.shutdown_event.is_set():
            try:
                mmf_name = bpy.context.scene.mmf_name
                buffer_size = bpy.context.scene.buffer_size * 1024  # Convert KB to bytes
                MMFServerManager.mmf = mmap.mmap(-1, buffer_size, tagname=mmf_name)
                MMFServerManager.handle_raw_bytes(MMFServerManager.mmf)
            except Exception as e:
                print(f"Error creating or handling MMF: {e}")
                if MMFServerManager.shutdown_event.is_set():
                    break
                time.sleep(1)
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
        return MMFServerManager.shutdown_event.is_set()
