"""Booking logic: the four functions the server calls.

Every function returns (ok, payload). On failure payload is an error code.
"""
import logging
import re
import threading
from typing import Any, Union

import psycopg

from db import get_conn

log = logging.getLogger(__name__)

SEAT_PATTERN = re.compile(r"^[A-Z][0-9]{1,2}$")
MAX_NAME_LEN = 50

_guard = threading.Lock()  # protects the dict only; never held with an event lock
_event_locks: dict[int, threading.Lock] = {}


def _lock_for(event_id: int) -> threading.Lock:
    with _guard:
        return _event_locks.setdefault(event_id, threading.Lock())


def _valid_event_id(value: Any) -> Union[int, None]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.isascii() and value.isdigit():
        return int(value) or None
    return None


def _valid_seat(value: Any) -> Union[str, None]:
    if isinstance(value, str) and SEAT_PATTERN.fullmatch(value):
        return value
    return None


def _valid_name(value: Any) -> Union[str, None]:
    if isinstance(value, str):
        name = value.strip()
        if 0 < len(name) <= MAX_NAME_LEN:
            return name
    return None


def list_events() -> tuple[bool, Any]:
    """Return all events as a list of dicts."""
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, name, event_date FROM events ORDER BY id"
            ).fetchall()
        return True, [
            {"id": r[0], "name": r[1], "date": r[2].isoformat()} for r in rows
        ]
    except psycopg.Error:
        log.exception("list_events failed")
        return False, "SERVER_ERROR"


def get_seats(event_id: Any) -> tuple[bool, Any]:
    """Return the seats of one event as a list of dicts."""
    eid = _valid_event_id(event_id)
    if eid is None:
        return False, "INVALID_EVENT"
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT seat_label, status, booked_by FROM seats "
                "WHERE event_id = %s ORDER BY id",
                (eid,),
            ).fetchall()
        if not rows:
            return False, "EVENT_NOT_FOUND"
        return True, [
            {"seat": r[0], "status": r[1], "booked_by": r[2]} for r in rows
        ]
    except psycopg.Error:
        log.exception("get_seats failed")
        return False, "SERVER_ERROR"


def book_seat(event_id: Any, seat_label: Any, user_name: Any) -> tuple[bool, str]:
    """Book a free seat for a user."""
    eid = _valid_event_id(event_id)
    seat = _valid_seat(seat_label)
    name = _valid_name(user_name)
    if eid is None:
        return False, "INVALID_EVENT"
    if seat is None:
        return False, "INVALID_SEAT"
    if name is None:
        return False, "INVALID_NAME"

    try:
        with _lock_for(eid), get_conn() as conn:
            cur = conn.execute(
                "UPDATE seats SET status = 'booked', booked_by = %s "
                "WHERE event_id = %s AND seat_label = %s AND status = 'free' "
                "RETURNING id",
                (name, eid, seat),
            )
            row = cur.fetchone()
            if cur.rowcount != 1 or row is None:
                exists = conn.execute(
                    "SELECT 1 FROM seats WHERE event_id = %s AND seat_label = %s",
                    (eid, seat),
                ).fetchone()
                return False, "SEAT_TAKEN" if exists else "SEAT_NOT_FOUND"
            conn.execute(
                "INSERT INTO bookings (seat_id, user_name) VALUES (%s, %s)",
                (row[0], name),
            )
        return True, "BOOKED"
    except psycopg.Error:
        log.exception("book_seat failed")
        return False, "SERVER_ERROR"


def cancel_booking(
    event_id: Any, seat_label: Any, user_name: Any
) -> tuple[bool, str]:
    """Cancel a booking, only if it belongs to this user."""
    eid = _valid_event_id(event_id)
    seat = _valid_seat(seat_label)
    name = _valid_name(user_name)
    if eid is None:
        return False, "INVALID_EVENT"
    if seat is None:
        return False, "INVALID_SEAT"
    if name is None:
        return False, "INVALID_NAME"

    try:
        with _lock_for(eid), get_conn() as conn:
            cur = conn.execute(
                "UPDATE seats SET status = 'free', booked_by = NULL "
                "WHERE event_id = %s AND seat_label = %s "
                "AND status = 'booked' AND booked_by = %s RETURNING id",
                (eid, seat, name),
            )
            row = cur.fetchone()
            if cur.rowcount != 1 or row is None:
                found = conn.execute(
                    "SELECT status FROM seats WHERE event_id = %s AND seat_label = %s",
                    (eid, seat),
                ).fetchone()
                if found is None:
                    return False, "SEAT_NOT_FOUND"
                if found[0] == "free":
                    return False, "NOT_BOOKED"
                return False, "NOT_YOUR_BOOKING"
            conn.execute("DELETE FROM bookings WHERE seat_id = %s", (row[0],))
        return True, "CANCELLED"
    except psycopg.Error:
        log.exception("cancel_booking failed")
        return False, "SERVER_ERROR"