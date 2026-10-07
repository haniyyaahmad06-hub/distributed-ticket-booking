import csv

import matplotlib.pyplot as plt


clients = []
average_times = []


with open(
    "load_results.csv",
    "r"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        if row["delay_ms"] == "0":

            clients.append(
                int(row["clients"])
            )

            average_times.append(
                float(
                    row["average_seconds"]
                )
            )


plt.figure()

plt.plot(
    clients,
    average_times,
    marker="o"
)

plt.xlabel(
    "Number of Clients"
)

plt.ylabel(
    "Average Response Time (seconds)"
)

plt.title(
    "Clients vs Average Response Time"
)

plt.savefig(
    "report/average_response_time.png"
)

plt.close()

print(
    "Graph saved successfully."
)