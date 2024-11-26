import queue
import threading
from typing import Optional, Protocol


class Server(Protocol):
    uuid: str
    data_queue: queue.Queue
    error: Optional[Exception]
    error_lock: threading.Lock
    traceback: Optional[str]

    def start_server(self) -> None:
        """
        Start the server in a separate thread.
        """
        ...

    def stop_server(self) -> None:
        """
        Stop the server and close the connections.
        """
        ...

    def is_running(self) -> bool:
        """
        Check if the server is running.
        """
        ...

    def is_shutdown(self) -> bool:
        """
        Check if the server is shutdown.
        """
        ...
