from json import dumps
from lib.TestCase import TestCase
from lib.Utils import kubectl
from lib.Arguments import deployment

class Baseline(TestCase):
    def kubernetes_setup(self):
        if deployment == "docker":
            raise RuntimeError("Error, unsupported deployment type")
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
            while kubectl("get", ["deployment", f"{name}-api"], json=True)["spec"]["replicas"] != 1:
                pass
        
