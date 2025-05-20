from subprocess import CalledProcessError
import time
import os
import csv
from json import dumps
from datetime import datetime
from lib.Data import autoscaler_deployment
from lib.Arguments import target, target_deployment, log_frequency
from lib.Utils import curl, kubectl

last_log = 0

def log(name:str, response_time:float, progress_percentage:int):
    global last_log
    match log_frequency:
        case -1:
            print(f"{name}:\t\t|\tProgress: {progress_percentage}%\t\t|\tResponse time: {response_time}")
        case _:
            if progress_percentage >= (last_log + log_frequency):
                print(f"{name}:\t\t|\tProgress: {progress_percentage}%\t\t|\tResponse time: {response_time}")
                last_log += log_frequency



class TestCase:
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
        start_time = time.perf_counter()
        end_time = start_time + self.period
        while time.perf_counter() < end_time:
            got_error = False
            start_send = time.perf_counter()
            try:
                curl(target, [
                    "--json",
                    f"{dumps(self.size)}"
                ], json=False)
            except CalledProcessError as e:
                print(f"Curl got error: {e.returncode}[{e.cmd=}, {e.args=}]")
                got_error = True
            end_send = time.perf_counter()
            response_time = end_send - start_send
            pod_count = kubectl("get", ["deploy", target_deployment], json=True)["spec"]["replicas"]
            results[start_send] = {"response_time": response_time, "pod_count": pod_count, "error":got_error}
            log(self.name, response_time, int(((end_send - start_time) / end_time) * 100))
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

    def cleanup(self):
        print("Cleaning up kubernetes environment...")
        kubectl("delete", [
            "hpa",
            target_deployment
        ], failable=True)
        data = autoscaler_deployment("autoscaler", "root", "password", 5432, 8080, 8081)
        for kubeconfig in data:
            name = kubeconfig["metadata"]["name"]
            kind = kubeconfig["kind"]
            kubectl("delete", [
                kind,
                name
            ], failable=True)


