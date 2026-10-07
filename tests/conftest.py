"""Shared test setup: starts a fresh server before the tests and stops it after."""

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

HOST = "127.0.0.1"
PORT = 5000
SERVER_FILE = Path(__file__).parent.parent / "server" / "server.py"


def send(message):
    """Open a connection, send one message, and return the reply."""
    with socket.create_connection((HOST, PORT), timeout=10) as conn:
        conn.sendall((message + "\n").encode("utf-8"))
        return conn.makefile("r", encoding="utf-8").readline().strip()


@pytest.fixture(scope="session", autouse=True)
def server():
    """Run the real server as a separate process for the whole test run."""
    process = subprocess.Popen([sys.executable, str(SERVER_FILE)])
    for _ in range(50):  # wait up to 5 seconds for it to start listening
        try:
            socket.create_connection((HOST, PORT), timeout=0.1).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        process.kill()
        pytest.fail("server did not start")
    yield
    process.terminate()
    process.wait(timeout=5)