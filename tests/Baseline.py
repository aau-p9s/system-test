from json import dumps
from lib.TestCase import TestCase
from lib.Utils import kubectl

class Baseline(TestCase):
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
                f"{name}-api",
                "--patch",
                f"{dumps(data)}"
            ])
            while kubectl("get", ["deployment", name], json=True)["spec"]["replicas"] != 1:
                pass
        
