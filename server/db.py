"""Connection pool for the ticket_booking database."""
import os
from contextlib import contextmanager
from typing import Iterator

from dotenv import load_dotenv
from psycopg import Connection
from psycopg_pool import ConnectionPool

load_dotenv()


def _conninfo() -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'distributed-ticketing-system')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('shanzeiman', '')}"
    )


_pool = ConnectionPool(_conninfo(), min_size=2, max_size=10, open=True)


@contextmanager
def get_conn() -> Iterator[Connection]:
    """Borrow a connection from the pool.

    Commits on success, rolls back on any exception, and always returns
    the connection to the pool, so threads never share one connection.
    """
    with _pool.connection() as conn:
        yield conn