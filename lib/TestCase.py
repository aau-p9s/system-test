from subprocess import CalledProcessError
import time
import os
import csv
from json import dumps
from typing import Any, Generic, Tuple, TypeVarTuple, Unpack
from lib.Data import autoscaler_deployment, workload_deployment_configs
from lib.Arguments import log_frequency, deployment
from lib.Metrics import measure_power_usage
from lib.Plot import plot_from_data
from lib.Utils import curl, kubectl_apply, kubectl, logged_delay, docker_compose_down

def make_log(start_time, end_time):
    duration = end_time - start_time
    save_data = {'last': -1, "response_times": [], "power": []}

    def log_progress(name, response_time, power, current_time):
        percentage = int(((current_time - start_time) / duration) * 100)
        match log_frequency:
            case -1:
                print(f"{name}:\t\t|\tProgress: {percentage}%\t\t|\tResponse time: {response_time:.5f}\t\t|\tMean Power Usage: {power:.5f}")
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
                    print(f"{name}:\t\t|\tProgress: {rounded}%\t\t|\tMean Response time: {mean:.5f}\t\t|\tMean Power Usage: {mean_power:.5f}")
                    save_data["response_times"] = []
                    save_data["power"] = []

    return log_progress

T = TypeVarTuple("T")
            

class TestCase(Generic[Unpack[T]]):
    size:dict[str, int]
    period:int
    delay:int
    scale_up:float
    scale_down:float
    min_replicas:int
    max_replicas:int

    def __init__(self, name, size: dict[str, int] = {"x":2000, "y":2000}, period: int = 86400, scale_up: float = .5, scale_down: float = .2, min_replicas: int = 1, max_replicas: int = 10, workload_configs: list[tuple[int, int, str]] = [(50, 2000, "mapped")], forecaster_remote_config: tuple[str] | None = None, deployment_settings: dict[str, str] = {}):
        self.size = size
        self.period = period
        self.scale_up = scale_up
        self.scale_down = scale_down
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.name = name
        self.forecaster_remote_config = forecaster_remote_config
        self.deployment_settings = deployment_settings
        self.kubeconfigs = autoscaler_deployment("autoscaler", "root", "password", 5432, 8080, 8081, forecaster_remote_config)
        
        self.workload_kubeconfigs = {
            f"workload-{i}": workload_deployment_configs(f"workload-{i}", 8090 + (i*2), size, config[0], config[1], config[2]) 
            for i, config in enumerate(workload_configs)
        }
        
        self.csv_name = lambda test_name: f"results/{name}-{test_name}.csv"
        self.intermediate_csv_name = lambda test_name: f"results/intermediate-{name}-{test_name}.csv"

        print(f"Initialized {self}")

    def __repr__(self) -> str:
        return f"{type(self).__name__}{{{self.size=}, {self.period=}, {self.scale_up=}, {self.scale_down=}, {self.min_replicas=}, {self.max_replicas=}}}".replace("self.", "")

    def run(self):

        results:dict[str, list[list[Any]]] = { name: [] for name in self.workload_kubeconfigs }
        logged_delay(5)

        start_time = time.time()
        end_time = start_time + self.period
        log = make_log(start_time, end_time)

        for key in self.workload_kubeconfigs:
            self.save_intermediate(key, self.column_names())

        while time.time() < end_time:
            for key in self.workload_kubeconfigs:
                result = self.measure(key, log)
                results[key].append(self.measure(key, log))
                self.save_intermediate(key, result)
        self.save(results)

    def measure(self, name:str, log):
        extra_metrics = self.extra_metrics(name)
        if deployment == "docker":
            log(self.name, time.time(), 0, time.time())
            if extra_metrics is not None:
                return [time.time(), 0.0, 1, 0, 1] + [m for m in extra_metrics]
            return [time.time(), 0.0, 1, 0, 1]
        kubeconfig = self.workload_kubeconfigs[name]
        if kubeconfig["api-service"] is None:
            raise ValueError("WTF")
        api_port = kubeconfig["api-service"]["spec"]["ports"][0]["nodePort"]
        if kubeconfig["generator-service"] is None:
            raise ValueError("WTF2")
        generator_port = kubeconfig["generator-service"]["spec"]["ports"][0]["nodePort"]
        start_send = time.time()
        try:
            curl(f"localhost:{api_port}/mm", [
                "--json",
                dumps(self.size)
            ], json=False)
        except CalledProcessError as e:
            print(f"Curl got error: {e.returncode}[{e.cmd=}, {e.args=}]")
        end_send = time.time()
        response_time = end_send - start_send
        request_count = int(curl(f"localhost:{generator_port}/api/metrics", json=False))
        pod_count = kubectl("get", ["deploy", f"{name}-api"], json=True)["spec"]["replicas"]
        power = measure_power_usage()[1]
        log(self.name, response_time, power, end_send)
        if extra_metrics is not None:
            return [start_send, response_time, pod_count, power, request_count] + [m for m in extra_metrics]
        return [start_send, response_time, pod_count, power, request_count]

    def extra_metrics(self, deployment: str) -> Tuple[Unpack[T]] | None:
        return None

    def column_names(self):
        return ["timestamp", "response", "pods", "watt", "request_count"]

    def save(self, results:dict[str, list[list[Any]]]):
        os.system("mkdir -p results")
        for name, rows in results.items():
            with open(self.csv_name(name), "w") as file:
                writer = csv.writer(file)
                writer.writerow(self.column_names())
                writer.writerows(rows)
            plot_from_data(rows, label=name)

    def save_intermediate(self, name: str, row:list[Any]):
        with open(self.intermediate_csv_name(name), "a") as file:
            writer = csv.writer(file)
            writer.writerow(row)

                
    def kubernetes_setup(self):
        kubectl("create", [
            "configmap",
            "data-config",
            "--from-file=/var/agg_minute.csv"
        ])
        for name, kubeconfigs in self.workload_kubeconfigs.items():
            if deployment == "docker":
                break
            for key, kubeconfig in kubeconfigs.items():
                print(f"Applying workloads: {name} - {key}")
                kubectl_apply(kubeconfig)

            print(f"Waiting for workload deployment: {name}")
            kubectl("wait", [
                "--for=condition=Available",
                f"deployments/{name}-api"
            ])
            kubectl("wait", [
                "--for=condition=Available",
                f"deployments/{name}-generator"
            ])
            

    def cleanup(self):
        match deployment:
            case "docker":
                docker_compose_down(self.kubeconfigs[0])
            case "kubernetes":
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
                        if kubeconfig is None:
                            raise ValueError("WTF3")
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
                kubectl("delete", [
                    "configmap",
                    "data-config"
                ], failable=True)
    
    def has_run(self) -> bool:
        return max(os.path.exists(self.csv_name(name)) for name in self.workload_kubeconfigs)
