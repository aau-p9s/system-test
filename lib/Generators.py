from typing import Any

def make_path(path: str, value: Any) -> dict[str, Any]:
    levels = path.split(".")
    if len(levels) == 1:
        return { levels[0]: value }
    else:
        return { levels[0]: make_path(path[len(levels[0])+1:], value) }


def make_deployment(name: str, containers: list[dict[str, Any]], service_account_name = None, volumes: list[Any] = []) -> dict[str, Any]:
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
                "spec": {
                    "containers": containers,
                    "serviceAccountName": service_account_name,
                    "volumes": volumes
                }
            }
        }
    }

def make_container(name: str, image: str, env: dict[str, str] = {}, ports: list[dict[str, int]] = [], volumeMounts: list[Any] = [], mem_req: str = "100Mi", mem_lim: str = "200Mi", cpu_req: str|None = "500m", cpu_lim: str|None = "1000m") -> dict[str, Any]:
    return {
        "name": name,
        "image": image,
        "env": [
            { "name": name, "value": str(value) } 
            for name, value in env.items()
        ],
        "ports": ports,
        "volumeMounts": volumeMounts,
        "resources": {
            "requests": {
                "memory": mem_req,
                "cpu": cpu_req
            } if cpu_req is not None else {
                "memory": mem_req
            },
            "limits": {
                "memory": mem_lim,
                "cpu": cpu_lim
            } if cpu_lim is not None else {
                "memory": mem_lim
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
