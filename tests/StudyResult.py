from os import system
import os
from lib.TestCase import TestCase
from json import dumps
from lib.Data import autoscaler_deployment
from lib.Utils import copy_directory, curl, kubectl, logged_delay, clone_repository, nix
from lib.Arguments import target_deployment

autoscaler_port = 8080
forecaster_port = 8081
postgres_port = 5432

autoscaler_exposed_port = 30000 + (autoscaler_port % 1000)


class StudyResult(TestCase):
    def kubernetes_setup(self):
        autoscaler_kubeconfig = autoscaler_deployment("autoscaler", "root", "password", postgres_port, autoscaler_port, forecaster_port)
        late_deployments = []
        for kubeconfig in autoscaler_kubeconfig:
            if kubeconfig["metadata"]["name"] in ["autoscaler", "forecaster"] and kubeconfig["kind"] == "Deployment":
                late_deployments.append(kubeconfig)
            else:
                system(f"echo '{dumps(kubeconfig)}' | kubectl apply -f -")

        # wait for db to be ready
        kubectl("wait", [
            "--for=condition=Available",
            "deployments/postgres"
        ])
        # a little extra just to be sure
        logged_delay(10)

        # reinit and deploy db
        clone_repository("https://github.com/aau-p9s/autoscaler", "/tmp/autoscaler", "main")
        clone_repository("https://github.com/aau-p9s/forecaster", "/tmp/forecaster", "feat/model_deployment_scripts")
        copy_directory("/tmp/autoscaler/Autoscaler.Api/BaselineModels/", "/tmp/forecaster/Assets/models")
        nix("run", "path:/tmp/forecaster#reinit", working_directory="/tmp/forecaster")
        nix("run", "path:/tmp/forecaster#deploy", working_directory="/tmp/forecaster")

        # Do the late deployments
        for kubeconfig in late_deployments:
            system(f"echo '{dumps(kubeconfig)}' | kubectl apply -f -")
        # Wait for deployments to be ready
        kubectl("wait", [
            "--for=condition=Available",
            "deployments/autoscaler"
        ])
        kubectl("wait", [
            "--for=condition=Available",
            "deployments/forecaster"
        ])
        # a little extra just to be sure
        logged_delay(20)

        print("Discovering services")
        curl(f"localhost:{autoscaler_exposed_port}/services/start", json=False)
        # let shit run
        logged_delay(5)

        services = curl(f"localhost:{autoscaler_exposed_port}/services")
        service = [service for service in services if service["name"] == target_deployment][0]
        service_id = service["id"]
        service["autoscalingEnabled"] = True

        settings = curl(f"localhost:{autoscaler_exposed_port}/services/{service_id}/settings")
        settings["scaleUp"] = self.scale_up
        settings["scaleDown"] = self.scale_down
        settings["minReplicas"] = self.min_replicas
        settings["maxReplicas"] = self.max_replicas
        
        curl(f"localhost:{autoscaler_exposed_port}/services",  [
            "--json",
            f"'{dumps(service)}'"
        ], json=False)
        curl(f"localhost:{autoscaler_exposed_port}/services/{service_id}/settings", [
            "--json",
            f"'{dumps(settings)}'"
        ], json=False)
        print("Rediscovering services")
        curl(f"localhost:{autoscaler_exposed_port}/services/start", json=False)
