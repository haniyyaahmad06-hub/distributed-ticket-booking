import socket
import threading

from protocol import ProtocolError, parse_message

HOST = "127.0.0.1"
PORT = 5000


def handle_client(conn, addr):
    """Serve one client until it disconnects."""
    print(f"[+] {addr} connected")
    with conn:
        reader = conn.makefile("r", encoding="utf-8")
        for line in reader:
            try:
                command, args = parse_message(line)
                reply = f"OK parsed {command} {args}\n"
            except ProtocolError as error:
                print(f"[{addr}] bad message: {error}")
                reply = "ERROR BAD_REQUEST\n"
            conn.sendall(reply.encode("utf-8"))
    print(f"[-] {addr} disconnected")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(
                target=handle_client, args=(conn, addr), daemon=True
            )
            thread.start()


if __name__ == "__main__":
    main()