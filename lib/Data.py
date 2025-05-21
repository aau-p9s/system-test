workload_deployment_configs = lambda name, port, size: {
    "api": {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f"{name}-api"
        },
        "spec": {
            "selector": {
                "matchLabels": {
                    "app": f"{name}-api"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": f"{name}-api"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": f"{name}-api",
                            "image": "ghcr.io/aau-p9s/workload-api:latest",
                            "env": [
                                { "name": name, "value": value }
                                for name, value in {
                                    "WORKLOAD_PORT": str(port)
                                }.items()
                            ],
                            "ports": [{ "containerPort": port }]
                        }
                    ]
                }
            }
        }
    },
    "generator": {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f"{name}-generator"
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": f"{name}-generator"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": f"{name}-generator"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": f"{name}-generator",
                            "image": "ghcr.io/aau-p9s/workload-generator:latest",
                            "env": [
                                { "name": name, "value": value }
                                for name, value in {
                                    "GENERATOR_API_ADDR": f"{name}-api",
                                    "GENERATOR_API_PORT": str(port),
                                    "GENERATOR_PORT": str(port+1),
                                    "GENERATOR_X": str(size["x"]),
                                    "GENERATOR_Y": str(size["y"])
                                }.items()
                            ],
                        }
                    ]
                }
            }
        }
    },
    "api-service": {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-api"
        },
        "spec": {
            "type": "NodePort",
            "selector": {
                "app": f"{name}-api"
            },
            "ports": [
                {
                    "protocol": "TCP",
                    "port": port,
                    "targetPort": port,
                    "nodePort": 30000 + (port % 1000)
                }
            ]
        }
    },
    "generator-service": {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-generator"
        },
        "spec": {
            "type": "NodePort",
            "selector": {
                "app": f"{name}-generator"
            },
            "ports": [
                {
                    "protocol": "TCP",
                    "port": port+1,
                    "targetPort": port+1,
                    "nodePort": 30000 + ((port+1) % 1000)
                }
            ]
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

autoscaler_deployment = lambda db_name, db_user, db_password, db_port, autoscaler_port, forecaster_port: [
    {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": "autoscaler",
            "namespace": "default"
        }
    },
    {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {
            "name": "autoscaler-role"
        },
        "rules": [
            {
                "apiGroups": [ "apps", "" ],
                "resources": [ "services", "deployments", "namespaces", "deployments/scale", "pods" ],
                "verbs": [ "get", "list", "watch", "patch" ]
            }
        ]
    },
    {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {
            "name": "autoscaler-rolebinding"
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": "autoscaler-role",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": "autoscaler",
                "namespace": "default"
            }
        ]
    },
    {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "autoscaler"
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "autoscaler"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "autoscaler"
                    }
                },
                "spec": {
                    "serviceAccountName": "autoscaler",
                    "containers": [
                        {
                            "name": "autoscaler",
                            "image": "ghcr.io/aau-p9s/autoscaler:latest",
                            "env": [
                                { "name": name, "value": value }
                                for name, value in {
                                    "AUTOSCALER__APIS__FORECASTER": f"http://forecaster:{forecaster_port}",
                                    "AUTOSCALER__APIS__KUBERNETES": "https://kubernetes",
                                    "AUTOSCALER__APIS__PROMETHEUS": "http://10.43.26.12:80",
                                    "AUTOSCALER__DEVELOPMENTMODE": "false",
                                    "AUTOSCALER__PGSQL__DATABASE": db_name,
                                    "AUTOSCALER__PGSQL__USER": db_user,
                                    "AUTOSCALER__PGSQL__PASSWORD": db_password,
                                    "AUTOSCALER__PGSQL__ADDR": "postgres",
                                    "AUTOSCALER__PGSQL__PORT": str(db_port),
                                    "AUTOSCALER__ADDR": "0.0.0.0",
                                    "AUTOSCALER__PORT": str(autoscaler_port),
                                    "AUTOSCALER__STARTRUNNER": "false",
                                    "Logging__LogLevel__Autoscaler": "Debug"
                                }.items()
                            ],
                            "ports": [{ "containerPort": autoscaler_port }]
                        }
                    ]
                }
            }
        }
    },
    {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "autoscaler"
        },
        "spec": {
            "type": "NodePort",
            "selector": {
                "app": "autoscaler"
            },
            "ports": [
                {
                    "protocol": "TCP",
                    "port": autoscaler_port,
                    "targetPort": autoscaler_port,
                    "nodePort": 30000 + (autoscaler_port % 1000)
                }
            ]
        }
    },
    {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "forecaster"
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": "forecaster"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "forecaster"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "forecaster",
                            "image": "ghcr.io/aau-p9s/forecaster:latest",
                            "env": [
                                { "name": name, "value": value }
                                for name, value in {
                                    "FORECASTER__PGSQL__DATABASE": db_name,
                                    "FORECASTER__PGSQL__USER": db_user,
                                    "FORECASTER__PGSQL__PASSWORD": db_password,
                                    "FORECASTER__PGSQL__ADDR": "postgres",
                                    "FORECASTER__PGSQL__PORT": str(db_port),
                                    "FORECASTER__ADDR": "0.0.0.0",
                                    "FORECASTER__PORT": str(forecaster_port)
                                }.items()
                            ]
                        }
                    ]
                }
            }
        }
    },
    {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "forecaster"
        },
        "spec": {
            "type": "NodePort",
            "selector": {
                "app": "forecaster"
            },
            "ports": [
                {
                    "protocol": "TCP",
                    "port": forecaster_port,
                    "targetPort": forecaster_port,
                    "nodePort": 30000 + (forecaster_port % 1000)
                }
            ]
        }
    }
]
