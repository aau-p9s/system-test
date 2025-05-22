from lib.Utils import kubectl

TDP = 168 # mean from https://en.wikipedia.org/wiki/Epyc

def measure_power_usage():
    usage_raw: str = kubectl("top", [
        "nodes",
        "--no-headers=true"
    ])
    cpu_map = {
        name: int(usage[:-1])
        for name, usage, *_ in [list(filter(lambda e: not e == "", [content for content in line.split(" ")])) for line in usage_raw.split("\n")[:-1]]
    }
    total_cores = 4
    usage_map = { name: usage / (total_cores * 1000) * 100 for name, usage in cpu_map.items()}
    power_map = { name: usage / 100 * TDP for name, usage in usage_map.items()}
    return sum(usage_map.values()) // len(usage_map.values()), sum(power_map.values()) // len(power_map.values())
