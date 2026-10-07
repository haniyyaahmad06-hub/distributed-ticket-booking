import socket


class NetworkClient:

    def __init__(self, host="127.0.0.1", port=5000, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout

    def send_request(self, message):

        try:
            with socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout
            ) as client:

                client.sendall((message + "\n").encode("utf-8"))

                response = client.recv(4096).decode("utf-8").strip()

                return response

        except socket.timeout:
            return "ERROR TIMEOUT"

        except ConnectionRefusedError:
            return "ERROR SERVER_DOWN"

        except OSError as error:
            return f"ERROR {error}"