"""The request queue and the worker threads that process it."""

import json
import logging
import queue
import threading

import fake_booking as booking

WORKER_COUNT = 4
QUEUE_SIZE = 100

REPLY_TIMEOUT = 10  # seconds a client thread waits for a worker

log = logging.getLogger("workers")

# Every client thread puts requests here; worker threads take them off
request_queue = queue.Queue(maxsize=QUEUE_SIZE)


def handle_request(command, args):
    """Carry out one valid command and return the reply text."""
    if command == "LIST_EVENTS":
        return "OK " + json.dumps(booking.list_events())

    event_id = int(args[0])

    if command == "LIST_SEATS":
        return "OK " + json.dumps(booking.list_seats(event_id))

    seat = args[1].upper()
    user = args[2]
    if command == "BOOK":
        success, reason = booking.book_seat(event_id, seat, user)
    else:
        success, reason = booking.cancel_seat(event_id, seat, user)
    return "OK" if success else f"ERROR {reason}"


def submit(command, args):
    """Queue one request and wait for its reply. Called by client threads."""
    reply_box = queue.Queue(maxsize=1)
    try:
        request_queue.put_nowait((command, args, reply_box))
    except queue.Full:
        log.warning("queue full, rejecting %s", command)
        return "ERROR SERVER_BUSY"
    try:
        return reply_box.get(timeout=REPLY_TIMEOUT)
    except queue.Empty:
        log.warning("no worker answered %s in time", command)
        return "ERROR SERVER_BUSY"


def worker_loop():
    """Take requests off the queue forever and process them."""
    while True:
        command, args, reply_box = request_queue.get()
        log.info("handling %s %s", command, args)
        try:
            reply = handle_request(command, args)
        except ValueError:
            reply = "ERROR BAD_REQUEST"
        except Exception:  # a worker must never die
            log.exception("unexpected error in %s", command)
            reply = "ERROR SERVER_ERROR"
        reply_box.put(reply)
        request_queue.task_done()


def start_workers():
    """Start the pool of worker threads."""
    for number in range(1, WORKER_COUNT + 1):
        thread = threading.Thread(
            target=worker_loop, name=f"worker-{number}", daemon=True
        )
        thread.start()