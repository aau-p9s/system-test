from json import dumps
from lib.TestCase import TestCase
from lib.Utils import kubectl
from lib.Arguments import target_deployment

class Baseline(TestCase):
    def __init__(self, name, size:dict[str, int] = {"x":2000, "y":2000}, period:int = 86400, delay:int = 25, tests:int = 1):
        super().__init__(name, size, period, delay, tests)

    def kubernetes_setup(self):
        data = {
                "spec":{
                "replicas":1
            }
        }
        kubectl("patch", [
            "deployment",
            target_deployment,
            "--patch",
            f"{dumps(data)}"
        ])
        while kubectl("get", ["deployment", target_deployment], json=True)["spec"]["replicas"] != 1:
            pass
        
