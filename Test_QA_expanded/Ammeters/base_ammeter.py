"""Shared TCP server implementation for the ammeter emulators."""

import socket
import threading
from abc import ABC, abstractmethod


class AmmeterEmulatorBase(ABC):
    """A small, stoppable TCP server exposing one measurement command."""

    def __init__(self, port: int, host: str = "127.0.0.1"):
        self.host = host
        self.port = int(port)
        self._stop_event = threading.Event()
        self._server_socket = None

    def start_server(self) -> None:
        """Serve measurement requests until :meth:`stop` is called."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            self._server_socket = server
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(8)
            server.settimeout(0.5)
            print(f"{self.__class__.__name__} listening on {self.host}:{self.port}")

            while not self._stop_event.is_set():
                try:
                    connection, address = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._stop_event.is_set():
                        break
                    raise

                with connection:
                    connection.settimeout(2.0)
                    request = b""
                    try:
                        request = connection.recv(1024).strip()
                        if request != self.get_current_command:
                            response = f"ERROR: unsupported command; expected {self.get_current_command.decode()}"
                        else:
                            response = str(float(self.measure_current()))
                    except Exception as exc:  # keep the server alive after a bad request
                        response = f"ERROR: {type(exc).__name__}: {exc}"
                    try:
                        connection.sendall(response.encode("utf-8"))
                    except OSError:
                        pass
                    print(f"Request from {address}: {request!r} -> {response}")

            self._server_socket = None

    def stop(self) -> None:
        """Request a clean shutdown; the accept loop exits within 0.5 seconds."""
        self._stop_event.set()

    @property
    @abstractmethod
    def get_current_command(self) -> bytes:
        """Exact command accepted by this emulator."""

    @abstractmethod
    def measure_current(self) -> float:
        """Return one simulated current measurement in amperes."""
