from json import dumps
import os
from time import sleep
from lib.TestCase import TestCase
from lib.data import hpa_patch

class GroundTruth(TestCase):
    def kubernetes_setup(self):
        os.system("kubectl autoscale deployment workload-api-deployment --cpu-percent=50 --min=1 --max=10")
        print("deployed autoscaler")
        # Patch HPA
        patch_data = hpa_patch(self.min_replicas, self.max_replicas, self.scale_down, self.scale_up)
        os.system(f"kubectl patch hpa workload-api-deployment --patch '{dumps(patch_data)}'")
        sleep(120)
