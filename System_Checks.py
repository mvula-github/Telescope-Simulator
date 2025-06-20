# network_utils.py
import socket

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    Checks for an active internet connection by attempting to connect to a known host.
    Returns (True, message) if successful, (False, error_message) otherwise.
    """
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
        return True, "Internet connection is available."
    except socket.timeout:
        return False, "Connection timed out. No internet connection."
    except socket.gaierror:
        return False, "Failed to connect. Host unreachable or invalid."
    except Exception as e:
        return False, f"An error occurred: {str(e)}"