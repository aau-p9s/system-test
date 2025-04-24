import matplotlib.pyplot as plt
import sys
import csv
import datetime
import os

if not sys.argv[-1] == "all":
    files = sys.argv [-1:]
else:
    files = [f"./results/{file}" for file in os.listdir("./results")]

for file in files:
    lines = []
    with open(file, "r") as result:
        reader = csv.reader(result)
        for line in reader:
            lines.append(line)

    timestamps = [float(timestamp) for timestamp, *_ in lines[1:]]
    fitted_timestamps = [datetime.datetime.fromtimestamp(timestamp) for timestamp in timestamps]
    responses = [float(response) for _, response, *_ in lines[1:]]
    pods = [float(pods)/10 for *_, pods in lines[1:]]
    print(f"timestamps: {timestamps}")
    print(f"responses:  {responses}")
    print(f"pods:       {pods}")

    ax = plt.plot(fitted_timestamps, responses, label=file)
    if not sys.argv[-1] == "all":
        plt.plot(fitted_timestamps, pods, label="pod count")

plt.legend()
plt.ylim(0, 1)

plt.show()
