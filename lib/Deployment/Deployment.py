from typing import Any


class Deployment:
    def deploy(self, data: list[dict[str, Any]]):
        raise NotImplementedError(data)
    
    def cleanup(self):
        raise NotImplementedError()

    def measure(self, deployment_name: str):
        raise NotImplementedError(deployment_name)

    def scale(self, deployment_name: str):
        raise NotImplementedError(deployment_name)
