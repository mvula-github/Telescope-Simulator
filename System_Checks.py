import socket
from dataclasses import dataclass

@dataclass
class NetworkStatus:
    ok: bool
    message: str

def check_internet_connection(host="8.8.8.8", port=53, timeout=3) -> NetworkStatus:
    """
    Checks for an active internet connection by attempting to connect to a known host.
    Returns NetworkStatus(ok, message).
    """
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
        return NetworkStatus(True, "Internet connection is available.")
    except socket.timeout:
        return NetworkStatus(False, "Connection timed out. No internet connection.")
    except socket.gaierror:
        return NetworkStatus(False, "Failed to connect. Host unreachable or invalid.")
    except Exception as e:
        return NetworkStatus(False, f"An error occurred: {str(e)}")

def connection_message(status: NetworkStatus) -> str:
    return status.message