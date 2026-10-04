"""Turns one line of text from a client into a command and its arguments."""

# Each command and how many arguments it must have
COMMANDS = {
    "LIST_EVENTS": 0,
    "LIST_SEATS": 1,
    "BOOK": 3,
    "CANCEL": 3,
}


class ProtocolError(Exception):
    """Raised when a message does not follow the protocol."""


def parse_message(line):
    """Return (command, args) for a valid line, or raise ProtocolError."""
    parts = line.strip().split()
    if not parts:
        raise ProtocolError("empty message")

    command = parts[0].upper()
    args = parts[1:]

    if command not in COMMANDS:
        raise ProtocolError(f"unknown command: {command}")
    if len(args) != COMMANDS[command]:
        raise ProtocolError(
            f"{command} needs {COMMANDS[command]} arguments, got {len(args)}"
        )
    return command, args