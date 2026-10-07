import logging
import socket
import threading

import workers
from protocol import ProtocolError, parse_message

HOST = "127.0.0.1"
PORT = 5000
IDLE_TIMEOUT = 60      # seconds a client may stay silent before being dropped
MAX_LINE_LENGTH = 200  # longest message we accept, in characters

log = logging.getLogger("server")


def serve_client(conn, addr):
    """Read requests from one client and answer them until it leaves."""
    conn.settimeout(IDLE_TIMEOUT)
    reader = conn.makefile("r", encoding="utf-8", errors="replace")
    while True:
        line = reader.readline(MAX_LINE_LENGTH + 1)
        if not line:
            return  # the client closed the connection
        if len(line) > MAX_LINE_LENGTH and not line.endswith("\n"):
            log.warning("%s sent an oversized message, closing", addr)
            conn.sendall(b"ERROR BAD_REQUEST\n")
            return
        try:
            command, args = parse_message(line)
            reply = workers.submit(command, args)
        except ProtocolError as error:
            log.warning("%s bad message: %s", addr, error)
            reply = "ERROR BAD_REQUEST"
        conn.sendall((reply + "\n").encode("utf-8"))


def handle_client(conn, addr):
    """Run one client's session and make sure its errors stay contained."""
    log.info("%s connected", addr)
    try:
        with conn:
            serve_client(conn, addr)
    except TimeoutError:
        log.info("%s idle for %s seconds, closing", addr, IDLE_TIMEOUT)
    except OSError as error:
        log.info("%s connection lost: %s", addr, error)
    except Exception:
        log.exception("%s unexpected error", addr)
    log.info("%s disconnected", addr)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s [%(threadName)s] %(message)s",
    )
    workers.start_workers()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        server.settimeout(1.0)  # wake up every second so Ctrl+C is noticed
        log.info("Server listening on %s:%s", HOST, PORT)
        try:
            while True:
                try:
                    conn, addr = server.accept()
                except TimeoutError:
                    continue
                thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr),
                    name=f"client-{addr[1]}",
                    daemon=True,
                )
                thread.start()
        except KeyboardInterrupt:
            log.info("Ctrl+C received, shutting down")


if __name__ == "__main__":
    main()