from subprocess import check_output
import time
import os
import csv
from json import dumps, loads
from datetime import datetime

class TestCase:
    target:str
    target_deployment:str
    size:dict[str, int]
    period:int
    delay:int
    tests:int
    scale_up:float
    scale_down:float
    min_replicas:int
    max_replicas:int

    def __init__(self, name, size:dict[str, int] = {"x":2000, "y":2000}, period:int = 86400, delay:int = 25, tests:int = 1, scale_up:float = .5, scale_down:float = .2, min_replicas:int = 1, max_replicas:int = 10):
        self.size = size
        self.period = period
        self.delay = delay
        self.tests = tests
        self.scale_up = scale_up
        self.scale_down = scale_down
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.response_data:list[dict[float, dict[str, float | int]]] = []
        self.name = name

        print(f"Initialized {self}\n")

    def __repr__(self) -> str:
        return f"{type(self).__name__}{{{self.size=}, {self.period=}, {self.delay=}, {self.tests=}, {self.scale_up=}, {self.scale_down=}, {self.min_replicas=}, {self.max_replicas=}}}".replace("self.", "")

    def run(self):
        results:dict[float, dict[str, float | int]] = {}
        start_time = time.time()
        end_time = start_time + self.period
        while time.time() < end_time:
            start_send = time.time()
            cmd = f"curl {self.target} -d '{dumps(self.size)}'"
            os.system(cmd)
            end_send = time.time()
            response_time = end_send - start_send
            pod_count = loads(check_output(["kubectl", "get", "deploy", self.target_deployment, "-o", "json"]).decode())["spec"]["replicas"]
            results[start_send] = {"response_time": response_time, "pod_count": pod_count}
            wait_time = self.delay - response_time
            print(f"{wait_time=}")
        self.response_data.append(results)

    def save(self):
        os.system("mkdir -p results")
        for index, result in enumerate(self.response_data):
            timestamp = int(time.time())
            with open(f"results/{self.name}-{datetime.fromtimestamp(timestamp)}-{index}.csv", "w") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "response"])
                for timestamp1, data in result.items():
                    writer.writerow([timestamp1, data["response_time"], data["pod_count"]])
                
    def kubernetes_setup(self):
        print("Setup unsupported")
