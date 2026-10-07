"""Concurrency tests: many clients at once must never corrupt the seat data."""

import json
import threading

from conftest import send


def run_in_threads(messages):
    """Send every message from its own thread at the same moment."""
    replies = [None] * len(messages)
    start = threading.Barrier(len(messages))

    def client(index):
        start.wait()  # hold every thread here until all are ready
        replies[index] = send(messages[index])

    threads = [
        threading.Thread(target=client, args=(index,))
        for index in range(len(messages))
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    return replies, threads


def test_one_seat_one_winner():
    """100 clients book the same seat: exactly one may succeed."""
    messages = [f"BOOK 1 A1 user{number}" for number in range(100)]

    replies, _ = run_in_threads(messages)

    assert replies.count("OK") == 1
    assert replies.count("ERROR SEAT_TAKEN") == 99


def test_different_seats_all_succeed():
    """Clients booking different seats must not block each other out."""
    seats = ["B1", "B2", "B3", "B4", "B5"]
    messages = [f"BOOK 1 {seat} user{seat}" for seat in seats]

    replies, _ = run_in_threads(messages)

    assert replies == ["OK"] * len(seats)


def test_no_deadlock_under_mixed_load():
    """Books and cancels across two events must all finish in time."""
    messages = []
    for number in range(50):
        event = 1 + number % 2
        messages.append(f"BOOK {event} A2 mixed{number}")
        messages.append(f"CANCEL {event} A2 mixed{number}")
        messages.append(f"LIST_SEATS {event}")

    replies, threads = run_in_threads(messages)

    assert not any(thread.is_alive() for thread in threads), "a client hung"
    assert all(reply.startswith(("OK", "ERROR")) for reply in replies)


def test_seat_map_stays_consistent():
    """After the load above, every seat is still either free or booked."""
    for event in (1, 2):
        reply = send(f"LIST_SEATS {event}")
        seats = json.loads(reply.removeprefix("OK "))

        assert len(seats) == 10
        assert all(seat["status"] in ("free", "booked") for seat in seats)