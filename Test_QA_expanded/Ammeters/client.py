"""TCP client helpers for requesting ammeter measurements."""

import socket
from typing import Union


class AmmeterCommunicationError(RuntimeError):
    """Raised when an ammeter cannot provide a valid numeric measurement."""


def request_current_from_ammeter(
    port: int,
    command: Union[bytes, str],
    host: str = "127.0.0.1",
    timeout: float = 3.0,
) -> float:
    """Request one measurement and return it as a float (amperes)."""
    payload = command.encode("utf-8") if isinstance(command, str) else command
    try:
        with socket.create_connection((host, int(port)), timeout=timeout) as client:
            client.sendall(payload)
            response = client.recv(1024).decode("utf-8").strip()
    except OSError as exc:
        raise AmmeterCommunicationError(
            f"Could not communicate with ammeter at {host}:{port}: {exc}"
        ) from exc

    if not response:
        raise AmmeterCommunicationError(f"Ammeter at {host}:{port} returned an empty response")
    if response.startswith("ERROR:"):
        raise AmmeterCommunicationError(response)
    try:
        value = float(response)
    except ValueError as exc:
        raise AmmeterCommunicationError(f"Invalid numeric response: {response!r}") from exc
    if value != value or value in (float("inf"), float("-inf")):
        raise AmmeterCommunicationError(f"Non-finite measurement received: {response!r}")
    return value
