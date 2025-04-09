from json import dumps
import os
from time import sleep
from lib.TestCase import TestCase
from lib.data import hpa_patch

class GroundTruth(TestCase):
    def kubernetes_setup(self):
        #print("Cleaning kubernetes autoscalers and deployments")
        #os.system("""
        #    kubectl delete hpa workload-api-deployment
        #    kubectl delete deployment workload-api-deployment
        #""")
        #print("Deploying workload")
        #os.system(f"echo '{dumps(workload_api_data)}' | kubectl apply -f -")
        #print("deployed workflow api")
        #os.system("kubectl autoscale deployment workload-api-deployment --cpu-percent=50 --min=1 --max=10")
        #print("deployed autoscaler")
        ## Patch HPA
        patch_data = hpa_patch(self.max_replicas, self.min_replicas, self.scale_up, self.scale_down)
        os.system(f"kubectl patch hpa workload-api-deployment --patch '{dumps(patch_data)}'")
        sleep(120)
