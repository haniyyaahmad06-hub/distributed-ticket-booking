"""In-memory booking functions. Stands in for the real database version."""

import threading

# One lock guards all the seat data below
_lock = threading.Lock()

_events = [
    {"id": 1, "name": "Tech Conference"},
    {"id": 2, "name": "Music Night"},
]

# _seats[event_id][seat_label] is None when free, or the user who booked it
_seats = {
    event["id"]: {f"{row}{number}": None for row in "AB" for number in range(1, 6)}
    for event in _events
}


def list_events():
    """Return every event as a list of dicts."""
    return list(_events)


def list_seats(event_id):
    """Return the seats of one event with their status."""
    with _lock:
        seats = _seats.get(event_id, {})
        return [
            {"seat": label, "status": "free" if user is None else "booked"}
            for label, user in seats.items()
        ]


def book_seat(event_id, seat, user):
    """Book a seat. Return (True, "OK") or (False, reason)."""
    with _lock:
        seats = _seats.get(event_id)
        if seats is None or seat not in seats:
            return False, "NO_SUCH_SEAT"
        if seats[seat] is not None:
            return False, "SEAT_TAKEN"
        seats[seat] = user
        return True, "OK"


def cancel_seat(event_id, seat, user):
    """Cancel a booking. Return (True, "OK") or (False, reason)."""
    with _lock:
        seats = _seats.get(event_id)
        if seats is None or seat not in seats:
            return False, "NO_SUCH_SEAT"
        if seats[seat] is None:
            return False, "NOT_BOOKED"
        if seats[seat] != user:
            return False, "NOT_YOURS"
        seats[seat] = None
        return True, "OK"