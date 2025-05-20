from subprocess import DEVNULL, CalledProcessError, check_call, check_output
import time
import os
import csv
from json import dumps, loads
from datetime import datetime
from typing import Any
from lib.data import autoscaler_deployment

def curl(url:str, params:list[str] = [], json=True) -> Any:
    raw_response = check_output([
        "curl",
        url,
    ] + params, stderr=DEVNULL)
    print(f"curl raw response: {raw_response}")
    if json:
        return loads(raw_response)

def clone_repository(url:str, target_directory:str, branch:str = "main"):
    if target_directory in ["/", ".", ""]:
        print("lol")
        exit(1)
    os.system(f"rm -rf {target_directory}")
    print(f"Cloning Repository: {url}[{branch}] -> {target_directory}")
    try:
        check_call([
            "git",
            "clone",
            url,
            "-b",
            branch,
            target_directory
        ], stdout=DEVNULL)
    except CalledProcessError as e:
        print(f"Failed to clone repo [{e.returncode}]")
        exit(1)

def kubectl(command, args, json=False, failable=False) -> Any:
    raw_response = ""
    try:
        raw_response = check_output([
            "kubectl",
            command,
        ] + args + (["-o", "json"] if json else []), stderr=DEVNULL)
    except CalledProcessError:
        print(f"Kubectl command failed, continue? {failable}")
        if not failable:
            exit(1)
    print(f"kubernetes raw response: {raw_response}")
    if json:
        return loads(raw_response)


def logged_delay(delay):
    print(f"Current thread is waiting for {delay} seconds")
    time.sleep(delay)


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
            got_error = False
            start_send = time.time()
            try:
                curl(self.target, [
                    "-d",
                    f"'{dumps(self.size)}'"
                ], json=False)
            except CalledProcessError as e:
                print(f"Curl got error: {e.returncode}")
                got_error = True
            end_send = time.time()
            response_time = end_send - start_send
            pod_count = kubectl("get", ["deploy", self.target_deployment], json=True)["spec"]["replicas"]
            results[start_send] = {"response_time": response_time, "pod_count": pod_count, "error":got_error}
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

    def cleanup(self):
        print("Cleaning up kubernetes environment...")
        kubectl("delete", [
            "hpa",
            self.target_deployment
        ])
        data = autoscaler_deployment("autoscaler", "root", "password", 5432, 8080, 8081)
        for kubeconfig in data:
            name = kubeconfig["metadata"]["name"]
            kind = kubeconfig["kind"]
            kubectl("delete", [
                kind,
                name
            ])
