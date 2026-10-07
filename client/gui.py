import tkinter as tk
import threading
import queue
import json

from client.network import NetworkClient


class TicketBookingGUI:

    def __init__(self, root):

        self.root = root

        self.root.title("Distributed Ticket Booking")
        self.root.geometry("700x650")

        # Network client
        self.network = NetworkClient()

        # Queue for communication between
        # background thread and GUI thread
        self.result_queue = queue.Queue()

        # Current selected event
        self.selected_event_id = None

        # Current selected seat
        self.selected_seat = None

        # Store seat buttons
        self.seat_buttons = {}

        # Create GUI
        self.create_gui()

        # Start checking the result queue
        self.check_queue()

        # Start loading events
        self.load_events()

    # -------------------------------------------------
    # CREATE GUI
    # -------------------------------------------------

    def create_gui(self):

        title = tk.Label(
            self.root,
            text="Distributed Ticket Booking",
            font=("Arial", 20)
        )

        title.pack(pady=20)

        # Event label
        event_label = tk.Label(
            self.root,
            text="Select Event"
        )

        event_label.pack()

        # Event list
        self.event_box = tk.Listbox(
            self.root,
            height=4,
            width=30
        )

        self.event_box.pack(pady=10)

        # When user selects an event
        self.event_box.bind(
            "<<ListboxSelect>>",
            self.event_selected
        )

        # Seat label
        seat_label = tk.Label(
            self.root,
            text="Select Seat"
        )

        seat_label.pack(pady=10)

        # Seat frame
        self.seat_frame = tk.Frame(
            self.root
        )

        self.seat_frame.pack()

        # Create initial seats
        self.create_seats()

        # Name label
        name_label = tk.Label(
            self.root,
            text="Your Name"
        )

        name_label.pack(pady=15)

        # Name input
        self.name_entry = tk.Entry(
            self.root,
            width=30
        )

        self.name_entry.pack()

        # Button frame
        button_frame = tk.Frame(
            self.root
        )

        button_frame.pack(pady=20)

        # Book button
        book_button = tk.Button(
            button_frame,
            text="Book",
            width=12,
            command=self.book_seat
        )

        book_button.grid(
            row=0,
            column=0,
            padx=10
        )

        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            width=12,
            command=self.cancel_seat
        )

        cancel_button.grid(
            row=0,
            column=1,
            padx=10
        )

        # Refresh button
        refresh_button = tk.Button(
            button_frame,
            text="Refresh",
            width=12,
            command=self.refresh_seats
        )

        refresh_button.grid(
            row=0,
            column=2,
            padx=10
        )

        # Status
        self.status_label = tk.Label(
            self.root,
            text="Status: Ready"
        )

        self.status_label.pack(pady=10)

    # -------------------------------------------------
    # CREATE SEATS
    # -------------------------------------------------

    def create_seats(self):

        seats = [
            "A1", "A2", "A3", "A4",
            "B1", "B2", "B3", "B4",
            "C1", "C2", "C3", "C4"
        ]

        for index, seat in enumerate(seats):

            button = tk.Button(
                self.seat_frame,
                text=seat,
                width=8,
                bg="green",
                fg="white",
                command=lambda s=seat: self.select_seat(s)
            )

            button.grid(
                row=index // 4,
                column=index % 4,
                padx=5,
                pady=5
            )

            self.seat_buttons[seat] = button

    # -------------------------------------------------
    # SELECT SEAT
    # -------------------------------------------------

    def select_seat(self, seat):

        self.selected_seat = seat

        self.status_label.config(
            text=f"Selected seat: {seat}"
        )

    # -------------------------------------------------
    # SELECT EVENT
    # -------------------------------------------------

    def event_selected(self, event):

        selection = self.event_box.curselection()

        if not selection:
            return

        index = selection[0]

        event_data = self.event_box.get(index)

        try:
            self.selected_event_id = int(
                event_data.split(" - ")[0]
            )

        except ValueError:
            self.status_label.config(
                text="Invalid event."
            )
            return

        self.refresh_seats()

    # -------------------------------------------------
    # LOAD EVENTS
    # -------------------------------------------------

    def load_events(self):

        self.status_label.config(
            text="Loading events..."
        )

        threading.Thread(
            target=self.request_events,
            daemon=True
        ).start()

    def request_events(self):

        response = self.network.send_request(
            "LIST_EVENTS"
        )

        self.result_queue.put(
            ("events", response)
        )

    # -------------------------------------------------
    # REFRESH SEATS
    # -------------------------------------------------

    def refresh_seats(self):

        if self.selected_event_id is None:
            self.status_label.config(
                text="Please select an event."
            )
            return

        self.status_label.config(
            text="Loading seats..."
        )

        threading.Thread(
            target=self.request_seats,
            daemon=True
        ).start()

    def request_seats(self):

        message = (
            f"LIST_SEATS {self.selected_event_id}"
        )

        response = self.network.send_request(
            message
        )

        self.result_queue.put(
            ("seats", response)
        )

    # -------------------------------------------------
    # BOOK SEAT
    # -------------------------------------------------

    def book_seat(self):

        if self.selected_event_id is None:

            self.status_label.config(
                text="Please select an event."
            )

            return

        if self.selected_seat is None:

            self.status_label.config(
                text="Please select a seat."
            )

            return

        name = self.name_entry.get().strip()

        if name == "":

            self.status_label.config(
                text="Please enter your name."
            )

            return

        if " " in name:

            self.status_label.config(
                text="Please use one name without spaces."
            )

            return

        self.status_label.config(
            text="Booking seat..."
        )

        threading.Thread(
            target=self.request_booking,
            args=(
                self.selected_event_id,
                self.selected_seat,
                name
            ),
            daemon=True
        ).start()

    def request_booking(
        self,
        event_id,
        seat,
        name
    ):

        message = (
            f"BOOK {event_id} {seat} {name}"
        )

        response = self.network.send_request(
            message
        )

        self.result_queue.put(
            ("booking", response)
        )

    # -------------------------------------------------
    # CANCEL SEAT
    # -------------------------------------------------

    def cancel_seat(self):

        if self.selected_event_id is None:

            self.status_label.config(
                text="Please select an event."
            )

            return

        if self.selected_seat is None:

            self.status_label.config(
                text="Please select a seat."
            )

            return

        name = self.name_entry.get().strip()

        if name == "":

            self.status_label.config(
                text="Please enter your name."
            )

            return

        if " " in name:

            self.status_label.config(
                text="Please use one name without spaces."
            )

            return

        self.status_label.config(
            text="Canceling seat..."
        )

        threading.Thread(
            target=self.request_cancel,
            args=(
                self.selected_event_id,
                self.selected_seat,
                name
            ),
            daemon=True
        ).start()

    def request_cancel(
        self,
        event_id,
        seat,
        name
    ):

        message = (
            f"CANCEL {event_id} {seat} {name}"
        )

        response = self.network.send_request(
            message
        )

        self.result_queue.put(
            ("cancel", response)
        )

    # -------------------------------------------------
    # CHECK QUEUE
    # -------------------------------------------------

    def check_queue(self):

        try:

            while True:

                action, response = (
                    self.result_queue.get_nowait()
                )

                if action == "events":

                    self.handle_events(
                        response
                    )

                elif action == "seats":

                    self.handle_seats(
                        response
                    )

                elif action == "booking":

                    self.handle_booking(
                        response
                    )

                elif action == "cancel":

                    self.handle_cancel(
                        response
                    )

        except queue.Empty:

            pass

        self.root.after(
            100,
            self.check_queue
        )

    # -------------------------------------------------
    # HANDLE EVENTS RESPONSE
    # -------------------------------------------------

    def handle_events(self, response):

        if response.startswith("ERROR"):

            self.show_error(response)

            return

        if not response.startswith("OK"):

            self.status_label.config(
                text="Invalid server response."
            )

            return

        json_data = response[2:].strip()

        try:

            events = json.loads(
                json_data
            )

        except json.JSONDecodeError:

            self.status_label.config(
                text="Could not read event data."
            )

            return

        self.event_box.delete(
            0,
            tk.END
        )

        for event in events:

            event_id = event.get(
                "id"
            )

            event_name = event.get(
                "name"
            )

            self.event_box.insert(
                tk.END,
                f"{event_id} - {event_name}"
            )

        self.status_label.config(
            text="Events loaded."
        )

    # -------------------------------------------------
    # HANDLE SEATS RESPONSE
    # -------------------------------------------------

    def handle_seats(self, response):

        if response.startswith("ERROR"):

            self.show_error(response)

            return

        if not response.startswith("OK"):

            self.status_label.config(
                text="Invalid server response."
            )

            return

        json_data = response[2:].strip()

        try:

            seats = json.loads(
                json_data
            )

        except json.JSONDecodeError:

            self.status_label.config(
                text="Could not read seat data."
            )

            return

        for seat_data in seats:

            seat = seat_data.get(
                "seat"
            )

            status = seat_data.get(
                "status"
            )

            if seat not in self.seat_buttons:
                continue

            button = self.seat_buttons[seat]

            if status == "free":

                button.config(
                    bg="green",
                    fg="white",
                    state=tk.NORMAL
                )

            elif status == "booked":

                button.config(
                    bg="red",
                    fg="white",
                    state=tk.NORMAL
                )

        self.status_label.config(
            text="Seats refreshed."
        )

    # -------------------------------------------------
    # HANDLE BOOKING
    # -------------------------------------------------

    def handle_booking(self, response):

        if response == "OK":

            self.status_label.config(
                text="Booking successful."
            )

            self.refresh_seats()

        elif "SEAT_TAKEN" in response:

            self.status_label.config(
                text="This seat is already booked."
            )

            self.refresh_seats()

        elif "NO_SUCH_SEAT" in response:

            self.status_label.config(
                text="This seat does not exist."
            )

        else:

            self.show_error(response)

    # -------------------------------------------------
    # HANDLE CANCEL
    # -------------------------------------------------

    def handle_cancel(self, response):

        if response == "OK":

            self.status_label.config(
                text="Cancellation successful."
            )

            self.refresh_seats()

        elif "NOT_YOURS" in response:

            self.status_label.config(
                text="You cannot cancel this seat."
            )

        elif "NOT_BOOKED" in response:

            self.status_label.config(
                text="This seat is not booked."
            )

        else:

            self.show_error(response)

    # -------------------------------------------------
    # ERROR HANDLING
    # -------------------------------------------------

    def show_error(self, response):

        if response == "ERROR SERVER_DOWN":

            self.status_label.config(
                text="Server is unavailable."
            )

        elif response == "ERROR TIMEOUT":

            self.status_label.config(
                text="Server timeout. Please try again."
            )

        elif "SERVER_BUSY" in response:

            self.status_label.config(
                text="Server is busy. Please try again."
            )

        elif "SERVER_ERROR" in response:

            self.status_label.config(
                text="Server error occurred."
            )

        else:

            self.status_label.config(
                text=response
            )


# -------------------------------------------------
# START APPLICATION
# -------------------------------------------------

root = tk.Tk()

app = TicketBookingGUI(root)

root.mainloop()