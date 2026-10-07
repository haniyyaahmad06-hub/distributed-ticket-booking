import csv
import random
import threading
import time

from statistics import mean

from client.network import NetworkClient


SEATS = [
    "A1", "A2", "A3", "A4",
    "B1", "B2", "B3", "B4",
    "C1", "C2", "C3", "C4"
]


def run_client(
    client_number,
    event_id,
    delay,
    results
):

    start_time = time.perf_counter()

    try:

        # Artificial network delay
        if delay > 0:
            time.sleep(delay / 1000)

        client = NetworkClient()

        seat = random.choice(SEATS)

        user = f"LoadUser{client_number}"

        message = (
            f"BOOK {event_id} {seat} {user}"
        )

        response = client.send_request(
            message
        )

        end_time = time.perf_counter()

        response_time = (
            end_time - start_time
        )

        success = response == "OK"

        results.append({
            "response_time": response_time,
            "success": success,
            "response": response
        })

    except Exception as error:

        end_time = time.perf_counter()

        results.append({
            "response_time": end_time - start_time,
            "success": False,
            "response": str(error)
        })


def calculate_p95(values):

    if not values:
        return 0

    values = sorted(values)

    index = int(
        len(values) * 0.95
    ) - 1

    index = max(
        0,
        index
    )

    return values[index]


def run_test(
    number_of_clients,
    event_id=1,
    delay=0
):

    threads = []

    results = []

    start_time = time.perf_counter()

    for i in range(
        number_of_clients
    ):

        thread = threading.Thread(
            target=run_client,
            args=(
                i,
                event_id,
                delay,
                results
            )
        )

        threads.append(thread)

        thread.start()

    for thread in threads:

        thread.join()

    end_time = time.perf_counter()

    total_time = (
        end_time - start_time
    )

    response_times = [
        item["response_time"]
        for item in results
    ]

    average = (
        mean(response_times)
        if response_times
        else 0
    )

    p95 = calculate_p95(
        response_times
    )

    requests_per_second = (
        number_of_clients / total_time
        if total_time > 0
        else 0
    )

    errors = sum(
        1
        for item in results
        if not item["success"]
    )

    return {
        "clients": number_of_clients,
        "delay": delay,
        "average": average,
        "p95": p95,
        "requests_per_second":
            requests_per_second,
        "errors": errors
    }


def save_result(result):

    with open(
        "load_results.csv",
        "a",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            result["clients"],
            result["delay"],
            result["average"],
            result["p95"],
            result["requests_per_second"],
            result["errors"]
        ])


if __name__ == "__main__":

    with open(
        "load_results.csv",
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "clients",
            "delay_ms",
            "average_seconds",
            "p95_seconds",
            "requests_per_second",
            "errors"
        ])

    client_counts = [
        10,
        50,
        100,
        500,
        1000
    ]

    delays = [
        0,
        50,
        200
    ]

    for clients in client_counts:

        for delay in delays:

            print(
                f"Running {clients} clients "
                f"with {delay} ms delay..."
            )

            result = run_test(
                clients,
                event_id=1,
                delay=delay
            )

            print(result)

            save_result(result)

    print(
        "Load testing complete."
    )