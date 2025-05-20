from json import dumps, loads
import os
from lib.TestCase import TestCase
from subprocess import check_output

class Baseline(TestCase):
    def __init__(self, name, size:dict[str, int] = {"x":2000, "y":2000}, period:int = 86400, delay:int = 25, tests:int = 1):
        super().__init__(name, size, period, delay, tests)

    def kubernetes_setup(self):
        os.system(f"""
            kubectl delete hpa {self.target_deployment}
            kubectl delete deployment autoscaler forecaster
        """)
        data = {
                "spec":{
                "replicas":1
            }
        }
        os.system(f"kubectl patch deployment {self.target_deployment} --patch '{dumps(data)}'")
        while loads(check_output(["kubectl", "get", "deploy", self.target_deployment, "-o", "json"]).decode())["spec"]["replicas"] != 1:
            pass
        
