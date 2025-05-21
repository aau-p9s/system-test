from typing import Any

def make_path(path: str, value: Any) -> dict[str, Any]:
    levels = path.split(".")
    if len(levels) == 1:
        return { levels[0]: value }
    else:
        return { levels[0]: make_path(path[len(levels[0]):], value) }


def make_deployment(name: str, containers: list[dict[str, Any]], service_account_name = None) -> dict[str, Any]:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name
        },
        "spec": {
            "selector": make_path("matchLabels.app", name),
            "template": {
                "metadata": make_path("labels.app", name),
                "spec": make_path("containers", containers) if service_account_name is None else {
                    "containers": containers,
                    "serviceAccountName": service_account_name
                }
            }
        }
    }

def make_container(name: str, image: str, env: dict[str, str] = {}, ports: list[dict[str, int]] = [], mem_req: str = "100Mi", mem_lim: str = "200Mi", cpu_req: str = "500m", cpu_lim: str = "1000m") -> dict[str, Any]:
    return {
        "name": name,
        "image": image,
        "env": [
            { "name": name, "value": str(value) } 
            for name, value in env.items()
        ],
        "ports": ports,
        "resources": {
            "requests": {
                "memory": mem_req,
                "cpu": cpu_req
            },
            "limits": {
                "memory": mem_lim,
                "cpu": cpu_lim
            }
        }
    }

def make_service(name: str, port: int) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name
        },
        "spec": {
            "type": "NodePort",
            "selector": {
                "app": name
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
    }
