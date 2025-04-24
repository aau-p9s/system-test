workload_api_deployment = lambda memory_req, cpu_req, memory_lim, cpu_lim: {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "workload-api-deployment"
    },
    "spec": {
        "selector": {
            "matchLabels": {
                "app": "workload-api"
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app": "workload-api"
                }
            },
            "spec": {
                "containers": [
                    {
                        "name": "workload-api",
                        "image": "ghcr.io/aau-p9s/workload-api:latest",
                        "environment": {
                            "WORKLOAD_PORT": 8123
                        },
                        "ports": [
                            {
                                "containerPort": 8123
                            }
                        ],
                        "resources": {
                            "requests": {
                                "memory": memory_req,
                                "cpu": cpu_req
                            },
                            "limits": {
                                "memory": memory_lim,
                                "cpu": cpu_lim
                            }
                        }
                    }
                ]
            }
        }
    }
}
hpa_patch = lambda min, max, scale_down, scale_up: {
    "spec":{
        "maxReplicas":max,
        "minReplicas":min,
        "behavior": {
            "scaleUp": {
                "policies": [
                    {
                        "type": "Percent",
                        "value": int(scale_up*100),
                        "periodSeconds": 60
                    }
                ],
                "stabilizationWindowSeconds": 300
            },
            "scaleDown": {
                "policies": [
                    {
                        "type": "Percent",
                        "value": int(scale_down*100),
                        "periodSeconds": 60
                    }
                ],
                "stabilizationWindowSeconds": 300
            }
        }
    },
}
