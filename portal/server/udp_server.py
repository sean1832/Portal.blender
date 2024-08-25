import queue
import socket
import threading

import bpy  # type: ignore


class UDPServerManager:
    data_queue = queue.Queue()
    shutdown_event = threading.Event()
    _server_thread = None
    _sock = None

    @staticmethod
    def udp_handler():
        while not UDPServerManager.shutdown_event.is_set():
            try:
                # 1472 is the max size of a UDP packet
                data, addr = UDPServerManager._sock.recvfrom(1472)
                UDPServerManager.data_queue.put(data.decode("utf-8"))
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error in udp_handler: {e}")

    @staticmethod
    def run_server():
        try:
            host = "localhost"
            port = bpy.context.scene.port  # blender input
            UDPServerManager._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            UDPServerManager._sock.bind((host, port))
            UDPServerManager._sock.settimeout(1)

            UDPServerManager.udp_handler()
        except Exception as e:
            print(f"Error creating or handling UDP server: {e}")
        finally:
            UDPServerManager._sock.close()

    @staticmethod
    def start_server():
        UDPServerManager.shutdown_event.clear()
        UDPServerManager._server_thread = threading.Thread(
            target=UDPServerManager.run_server, daemon=True
        )
        UDPServerManager._server_thread.start()
        print("UDP server started...")

    @staticmethod
    def stop_server():
        UDPServerManager.shutdown_event.set()
        if UDPServerManager._server_thread:
            UDPServerManager._server_thread.join()
        print("UDP server stopped...")

    @staticmethod
    def is_running():
        return (
            UDPServerManager._server_thread is not None
            and UDPServerManager._server_thread.is_alive()
        )

    @staticmethod
    def is_shutdown():
        return UDPServerManager.shutdown_event.is_set()
