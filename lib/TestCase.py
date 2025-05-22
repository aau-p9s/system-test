from subprocess import CalledProcessError
import sys
import time
import os
import csv
from json import dumps
from datetime import datetime
from typing import Any
from lib.Data import autoscaler_deployment, workload_deployment_configs
from lib.Arguments import log_frequency
from lib.Metrics import measure_power_usage
from lib.Utils import curl, kubectl, kubectl_apply, logged_delay

def make_log(start_time, end_time):
    duration = end_time - start_time
    save_data = {'last': -1, "response_times": [], "power": []}

    def log_progress(name, response_time, power, current_time):
        percentage = int(((current_time - start_time) / duration) * 100)
        match log_frequency:
            case -1:
                print(f"{name}:\t\t|\tProgress: {percentage}%\t\t|\tResponse time: {response_time}")
            case _:
                rounded = (percentage // log_frequency) * log_frequency
                save_data["response_times"].append(response_time)
                save_data["power"].append(power)
                if current_time < start_time or current_time > end_time:
                    return
                if rounded > save_data['last']:
                    save_data['last'] = rounded
                    mean = sum(save_data["response_times"]) / len(save_data["response_times"])
                    mean_power = sum(save_data["power"]) / len(save_data["power"])
                    print(f"{name}:\t\t|\tProgress: {rounded}%\t\t|\tMean Response time: {round(mean, 5)}\t\t|\tMean Power Usage: {round(mean_power, 5)}")
                    save_data["response_times"] = []
                    save_data["power"] = []

    return log_progress
            

class TestCase:
    size:dict[str, int]
    period:int
    delay:int
    scale_up:float
    scale_down:float
    min_replicas:int
    max_replicas:int

    def __init__(self, name, size: dict[str, int] = {"x":2000, "y":2000}, period: int = 86400, delay: int = 25, scale_up: float = .5, scale_down: float = .2, min_replicas: int = 1, max_replicas: int = 10, workload_configs: list[tuple[int, int]] = [(50, 2000)]):
        self.size = size
        self.period = period
        self.delay = delay
        self.scale_up = scale_up
        self.scale_down = scale_down
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.name = name
        self.kubeconfigs = autoscaler_deployment("autoscaler", "root", "password", 5432, 8080, 8081)
        
        self.workload_kubeconfigs = {
            f"workload-{i}": workload_deployment_configs(f"workload-{i}", 8090 + (i*2), size, workload_configs[i][0], workload_configs[i][1]) 
            for i in range(len(workload_configs))
        }
        
        self.csv_name = lambda test_name: f"{name}-{test_name}-csv"

        print(f"Initialized {self}")

    def __repr__(self) -> str:
        return f"{type(self).__name__}{{{self.size=}, {self.period=}, {self.delay=}, {self.scale_up=}, {self.scale_down=}, {self.min_replicas=}, {self.max_replicas=}}}".replace("self.", "")

    def run(self):
        if max(os.path.exists(self.csv_name(name)) for name in self.workload_kubeconfigs):
            print("Skipping, test already done")
            return

        results:dict[str, list[list[Any]]] = { name: [] for name in self.workload_kubeconfigs }
        logged_delay(5)

        start_time = time.time()
        end_time = start_time + self.period
        log = make_log(start_time, end_time)

        while time.time() < end_time:
            for key in self.workload_kubeconfigs:
                results[key].append(self.measure(key, log))
        self.save(results)

    def measure(self, name:str, log):
        start_send = time.time()
        target_port = self.workload_kubeconfigs[name]["api-service"]["spec"]["ports"][0]["nodePort"]
        try:
            curl(f"localhost:{target_port}/mm", [
                "--json",
                dumps(self.size)
            ], json=False)
        except CalledProcessError as e:
            print(f"Curl got error: {e.returncode}[{e.cmd=}, {e.args=}]")
        end_send = time.time()
        response_time = end_send - start_send
        pod_count = kubectl("get", ["deploy", f"{name}-api"], json=True)["spec"]["replicas"]
        power = measure_power_usage()[1]
        log(self.name, response_time, power, end_send)
        return [start_send, response_time, pod_count, power]

    def save(self, results:dict[str, list[list[Any]]]):
        os.system("mkdir -p results")
        for name, rows in results.items():
            with open(self.csv_name(name), "w") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "response", "pods", "watt"])
                writer.writerows(rows)
                
    def kubernetes_setup(self):
        for name, kubeconfigs in self.workload_kubeconfigs.items():
            for key, kubeconfig in kubeconfigs.items():
                print(f"Applying workload: {name} - {key}")
                kubectl_apply(kubeconfig)

    def workload_setup(self):
        print("Initializing workloads...")
        for api, generator in self.workload_kubeconfigs:
            kubectl_apply(api)
            kubectl_apply(generator)

    def cleanup(self):
        print("Cleaning up kubernetes environment...")
        for kubeconfig in self.kubeconfigs:
            name = kubeconfig["metadata"]["name"]
            kind = kubeconfig["kind"]
            kubectl("delete", [
                kind,
                name
            ], failable=True)

        # Workload Deployments
        for workload_name, kubeconfigs in self.workload_kubeconfigs.items():
            for key, kubeconfig in kubeconfigs.items():
                print(f"Cleaning {workload_name} - {key}")
                name = kubeconfig["metadata"]["name"]
                kind = kubeconfig["kind"]
                kubectl("delete", [
                    kind,
                    name
                ], failable=True)
                kubectl("delete", [
                    "hpa",
                    name
                ], failable=True)
