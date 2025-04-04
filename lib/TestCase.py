import time
import os
import csv
from json import dumps

class TestCase:
    target:str
    size:dict[str, int]
    period:int
    delay:int
    tests:int
    scale_up:float
    scale_down:float
    min_replicas:int
    max_replicas:int

    def __init__(self, size:dict[str, int] = {"x":4000, "y":4000}, period:int = 86400, delay:int = 300, tests:int = 3, scale_up:float = .5, scale_down:float = .2, min_replicas:int = 1, max_replicas:int = 10):
        self.size = size
        self.period = period
        self.delay = delay
        self.tests = tests
        self.scale_up = scale_up
        self.scale_down = scale_down
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.response_data:list[dict[float, float]] = []

        print(f"Initialized {self}\n")

    def __repr__(self) -> str:
        return f"{type(self).__name__}{{{self.size=}, {self.period=}, {self.delay=}, {self.tests=}, {self.scale_up=}, {self.scale_down=}, {self.min_replicas=}, {self.max_replicas=}}}".replace("self.", "")

    def run(self):
        self.setup_HPA()
        results:dict[float, float] = {}
        start_time = time.time()
        end_time = start_time + self.period
        while time.time() < end_time:
            start_send = time.time()
            cmd = f"curl {self.target} -d '{dumps(self.size)}'"
            os.system(cmd)
            end_send = time.time()
            response_time = end_send - start_send
            results[start_send] = response_time
            wait_time = self.delay - response_time
            print(f"{wait_time=}")
            if wait_time > 0:
                time.sleep(wait_time)
        self.response_data.append(results)

    def save(self):
        os.system("mkdir -p results")
        for index, result in enumerate(self.response_data):
            timestamp = int(time.time())
            with open(f"results/{type(self).__name__}-{timestamp}-{index}.csv", "w") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "response"])
                writer.writerows(result.items())
                
    def setup_HPA(self):
        print("Setup unsupported")
