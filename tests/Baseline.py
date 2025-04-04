from json import dumps, loads
import os
from lib.TestCase import TestCase
from subprocess import check_output

class Baseline(TestCase):
    def __init__(self, size:dict[str, int] = {"x":4000, "y":4000}, period:int = 86400, delay:int = 25, tests:int = 3):
        super().__init__(size, period, delay, tests)

    def kubernetes_setup(self):
        os.system("kubectl delete hpa workload-api-deployment")
        data = {
                "spec":{
                "replicas":1
            }
        }
        os.system(f"kubectl patch deployment workload-api-deployment --patch '{dumps(data)}'")
        while loads(check_output(["kubectl", "get", "deploy", "workload-api-deployment", "-o", "json"]).decode())["spec"]["replicas"] != 1:
            pass
        
