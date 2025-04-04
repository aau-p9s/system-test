from json import dumps
import os
from lib.TestCase import TestCase

class GroundTruth(TestCase):
    def setup_kubernetes(self):
        os.system("kubectl autoscale deployment workload-api-deployment --cpu-percent=50 --min=2 --max=10")
        data = {
            "spec":{
                "maxReplicas":self.max_replicas,
                "minReplicas":self.min_replicas,
                "behavior": {
                    "scaleUp": {
                        "policies": [
                            {
                                "type": "Percent",
                                "value": int(self.scale_up*100),
                                "periodSeconds": 60
                            }
                        ],
                        "stabilizationWindowSeconds": 300
                    },
                    "scaleDown": {
                        "policies": [
                            {
                                "type": "Percent",
                                "value": int(self.scale_up*100),
                                "periodSeconds": 60
                            }
                        ],
                        "stabilizationWindowSeconds": 300
                    }
                }
            },
        }
        os.system(f"kubectl patch hpa workload-api-deployment --patch '{dumps(data)}'")

