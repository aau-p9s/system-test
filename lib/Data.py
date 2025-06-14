from lib.Generators import make_container, make_deployment, make_service
from lib.Arguments import deployment

def workload_deployment_configs(name, port, size, min_requests, max_requests, workload_type, startup_delay):
    if deployment == "docker":
        return {"api":None, "generator":None}
    return {
        "api": make_deployment(f"{name}-api", [make_container(
            f"{name}-api",
            "ghcr.io/aau-p9s/workload-api:latest",
            {
                "WORKLOAD_PORT": port,
                "WORKLOAD_STARTUP_DELAY": startup_delay
            },
            [{
                "containerPort": port
            }]
        )]),
        "generator": make_deployment(f"{name}-generator", [make_container(
            f"{name}-generator",
            "ghcr.io/aau-p9s/workload-generator:latest",
            {
                "GENERATOR_API_ADDR": f"{name}-api",
                "GENERATOR_API_PORT": port,
                "GENERATOR_PORT": port+1,
                "GENERATOR_X": size["x"],
                "GENERATOR_Y": size["y"],
                "GENERATOR_MIN": min_requests,
                "GENERATOR_MAX": max_requests,
                "GENERATOR_SHAPE": workload_type
            },
            volumeMounts=[{
                "name": "data-volume",
                "mountPath": "/var/agg_minute.csv",
                "subPath": "agg_minute.csv",
            }],
            mem_req="1000Mi",
            mem_lim="2000Mi"
        )], volumes=[{
            "name": "data-volume",
            "configMap": {
                "name": "data-config"
            }
        }]),
        "api-service": make_service(f"{name}-api", port),
        "generator-service": make_service(f"{name}-generator", port+1)
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

def autoscaler_deployment(db_name, db_user, db_password, db_port, autoscaler_port, forecaster_port, remote_forecaster_config): 
    match deployment:
        case "docker":
            return [{
                "services": {
                    "forecaster": {
                        "build": {
                            "context": "modules/Forecaster"
                        },
                        "hostname":"forecaster",
                        "environment": {
                            "FORECASTER__PGSQL__DATABASE": db_name,
                            "FORECASTER__PGSQL__USER": db_user,
                            "FORECASTER__PGSQL__PASSWORD": db_password,
                            "FORECASTER__PGSQL__ADDR": "postgres",
                            "FORECASTER__PGSQL__PORT": 5432,
                            "FORECASTER__PORT": forecaster_port,
                            "FORECASTER__ENABLE__GPU": "0"
                        },
                        "ports": [
                            f"{30000 + (forecaster_port % 1000)}:{forecaster_port}"
                        ]
                    },
                    "autoscaler": {
                        "build": {
                            "context": "modules/Autoscaler"
                        },
                        "environment": {
                            "Autoscaler__Apis__Forecaster__Url": f"http://forecaster:{forecaster_port}",
                            "Autoscaler__Apis__Forecaster__Mock": False,
                            "Autoscaler__Apis__Kubernetes__Mock": True,
                            "Autoscaler__Apis__Prometheus__Mock": True,
                            "Autoscaler__Database__Database": db_name,
                            "Autoscaler__Database__User": db_user,
                            "Autoscaler__Database__Password": db_password,
                            "Autoscaler__Database__Hostname": "postgres",
                            "Autoscaler__Database__Port": db_port,
                            "Autoscaler__Addr": "0.0.0.0",
                            "Autoscaler__Port": autoscaler_port,
                            "Autoscaler__Runner__Start": False,
                            "Logging__LogLevel__Autoscaler": "Information"
                        },
                        "ports": [
                            f"{30000 + (autoscaler_port % 1000)}:{autoscaler_port}"
                        ]
                    },
                    "postgres": {
                        "image": "postgres:latest",
                        "shm_size": "128mb",
                        "hostname": "postgres",
                        "environment": {
                            "POSTGRES_PASSWORD": db_password,
                            "POSTGRES_USER": db_user,
                            "POSTGRES_DB": db_name
                        },
                        "ports": [
                            f"{30000 + (db_port % 1000)}:{db_port}"
                        ],
                        "volumes": [
                            "/var/p10_postgres:/var/lib/postgresql/data"
                        ]
                    }
                }
            }]
        case "kubernetes":
            return [
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
                make_deployment("autoscaler", [make_container(
                    "autoscaler",
                    "ghcr.io/aau-p9s/autoscaler:latest",
                    {
                        "Autoscaler__Apis__Forecaster__Url": "http://forecaster" if remote_forecaster_config is None else remote_forecaster_config[0],
                        "Autoscaler__Apis__Forecaster__Mock": "false",
                        "Autoscaler__Apis__Kubernetes__Url": "https://kubernetes",
                        "Autoscaler__Apis__Kubernetes__Mock": "false",
                        "Autoscaler__Apis__Prometheus__Url": "http://10.43.26.12:80",
                        "Autoscaler__Apis__Prometheus__Mock": "false",
                        "Autoscaler__Database__Database": db_name,
                        "Autoscaler__Database__User": db_user,
                        "Autoscaler__Database__Password": db_password,
                        "Autoscaler__Database__Hostname": "postgres",
                        "Autoscaler__Database__Port": str(db_port),
                        "Autoscaler__Addr": "0.0.0.0",
                        "Autoscaler__Port": str(autoscaler_port),
                        "Autoscaler__Runner__Start": "false",
                        "Logging__LogLevel__Autoscaler": "Information"
                    },
                    [{
                        "containerPort": autoscaler_port
                    }],
                    mem_req="1000Mi",
                    mem_lim="2000Mi"
                )], service_account_name = "autoscaler"),
                make_service("autoscaler", autoscaler_port)] + ([
                make_deployment("forecaster", [make_container(
                    "forecaster",
                    "ghcr.io/aau-p9s/forecaster:latest",
                    {
                        "FORECASTER__PGSQL__DATABASE": db_name,
                        "FORECASTER__PGSQL__USER": db_user,
                        "FORECASTER__PGSQL__PASSWORD": db_password,
                        "FORECASTER__PGSQL__ADDR": "postgres",
                        "FORECASTER__PGSQL__PORT": str(db_port),
                        "FORECASTER__ADDR": "0.0.0.0",
                        "FORECASTER__PORT": str(forecaster_port),
                        "FORECASTER__TRAIN__TIMEOUT":"300",
                        "FORECASTER__TEMPORARY__DIRECTORY":"/var/model_tmp",
                        "FORECASTER__ENABLE__GPU": "0"
                    },
                    [{
                        "containerPort": forecaster_port
                    }],
                    mem_req="10000Mi",
                    mem_lim="10000Mi",
                    cpu_req=None,
                    cpu_lim=None
                )]),
                make_service("forecaster", forecaster_port)
            ] if remote_forecaster_config is None else [])
        case _:
            raise ValueError("Deployment type is not allowed")
