from json import dumps
import os
from lib.TestCase import TestCase
from lib.data import hpa_patch

class GroundTruth(TestCase):
    def kubernetes_setup(self):
        self.kubectl("autoscale", [
            "deployment",
            self.target_deployment,
            "--cpu-percent=50",
            "--min=1",
            "--max=10"
        ])
        print("deployed autoscaler")
        # Patch HPA
        patch_data = hpa_patch(self.min_replicas, self.max_replicas, self.scale_down, self.scale_up)
        self.kubectl("patch", [
            "hpa",
            self.target_deployment,
            "--patch",
            f"'{dumps(patch_data)}'"
        ])
        os.system(f"kubectl patch hpa {self.target_deployment} --patch '{dumps(patch_data)}'")
        self.logged_delay(120)
