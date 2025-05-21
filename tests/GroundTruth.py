from json import dumps
from lib.TestCase import TestCase
from lib.Data import hpa_patch
from lib.Utils import kubectl, logged_delay

class GroundTruth(TestCase):
    def kubernetes_setup(self):
        super().kubernetes_setup()
        for name in self.workload_kubeconfigs:
            kubectl("autoscale", [
                "deployment",
                name,
                "--cpu-percent=50",
                "--min=1",
                "--max=10"
            ])
            print("deployed autoscaler")
            # Patch HPA
            patch_data = hpa_patch(self.min_replicas, self.max_replicas, self.scale_down, self.scale_up)
            kubectl("patch", [
                "hpa",
                name,
                "--patch",
                f"{dumps(patch_data)}"
            ])
            logged_delay(120)
