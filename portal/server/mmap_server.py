import mmap
import queue
import struct
import threading
import time

import bpy  # type: ignore


class MMFServerManager:
    data_queue = queue.Queue()
    shutdown_event = threading.Event()
    _server_thread = None
    mmf = None

    @staticmethod
    def handle_raw_bytes(mmf):
        try:
            while not MMFServerManager.shutdown_event.is_set():
                mmf.seek(0)
                if mmf.size() >= 4:
                    length_prefix = mmf.read(4)
                    data_length = struct.unpack("I", length_prefix)[0]

                    if data_length > 0 and mmf.size() >= 4 + data_length:
                        data = mmf.read(data_length).decode("utf-8")
                        MMFServerManager.data_queue.put(data)
                    else:
                        print("Data length exceeds the current readable size.")
                else:
                    print("Not enough data to read length prefix.")
                time.sleep(0.1)  # Adjust as needed
        except Exception as e:
            print(f"Error in handle_mmf_data: {e}")

    @staticmethod
    def run_server():
        while not MMFServerManager.shutdown_event.is_set():
            try:
                mmf_name = bpy.context.scene.mmf_filename
                buffer_size = bpy.context.scene.mmf_buffer_size * 1024  # Convert KB to bytes
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
