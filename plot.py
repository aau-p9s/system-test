import matplotlib.pyplot as plt
import sys
import csv

file = sys.argv[-1]

print(file)

lines = []
with open(file, "r") as result:
    reader = csv.reader(result)
    for line in reader:
        lines.append(line)

timestamps = [float(timestamp) for timestamp, *_ in lines[1:]]
responses = [float(response) for _, response, *_ in lines[1:]]
pods = [int(pods) for *_, pods in lines[1:]]
print(f"timestamps: {timestamps}")
print(f"responses:  {responses}")
print(f"pods:       {pods}")

ax = plt.plot(timestamps, responses)

plt.show()
