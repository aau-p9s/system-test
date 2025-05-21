from json import dumps
from lib.TestCase import TestCase
from lib.Utils import kubectl

class Baseline(TestCase):
    def __init__(self, name, size:dict[str, int] = {"x":2000, "y":2000}, period:int = 86400, delay:int = 25, tests:int = 1):
        super().__init__(name, size, period, delay, tests)

    def kubernetes_setup(self):
        super().kubernetes_setup()
        data = {
                "spec":{
                "replicas":1
            }
        }
        for name in self.workload_kubeconfigs:
            kubectl("patch", [
                "deployment",
                name,
                "--patch",
                f"{dumps(data)}"
            ])
            while kubectl("get", ["deployment", name], json=True)["spec"]["replicas"] != 1:
                pass
        
