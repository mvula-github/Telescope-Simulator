import socket

def check_internet_connection(host = "8.8.8.8", port = 53, timeout = 3):
    try:
        socket.setdefaulttimeout(timeout)

        # Try to create a socket connection to the host
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.close()

        return True, "Internet connection is available."
    except socket.timeout:
        return False, "Connection timed out. No internet connection."
    except socket.gaierror:
        return False, "Failed to connect. Host unreachable or invalid."
    except Exception as e:
        return False, f"An error occurred: {str(e)}"


def __main__():
    is_connected, message = check_internet_connection()
    print(message)

if __name__ == '__main__':
    __main__()