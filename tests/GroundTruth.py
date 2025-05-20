from json import dumps
import os
from lib.TestCase import TestCase
from lib.Data import hpa_patch
from lib.Utils import kubectl, logged_delay
from lib.Arguments import target_deployment

class GroundTruth(TestCase):
    def kubernetes_setup(self):
        kubectl("autoscale", [
            "deployment",
            target_deployment,
            "--cpu-percent=50",
            "--min=1",
            "--max=10"
        ])
        print("deployed autoscaler")
        # Patch HPA
        patch_data = hpa_patch(self.min_replicas, self.max_replicas, self.scale_down, self.scale_up)
        kubectl("patch", [
            "hpa",
            target_deployment,
            "--patch",
            f"{dumps(patch_data)}"
        ])
        logged_delay(120)
