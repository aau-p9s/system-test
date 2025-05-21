from lib.TestCase import TestCase
from json import dumps
from lib.Utils import copy_directory, curl, kubectl, kubectl_apply, logged_delay, clone_repository, nix
from lib.Arguments import reinit_db

autoscaler_port = 8080
forecaster_port = 8081
postgres_port = 5432

autoscaler_exposed_port = 30000 + (autoscaler_port % 1000)


class StudyResult(TestCase):
    def kubernetes_setup(self):
        super().kubernetes_setup()
        late_deployments = []
        print("Applying initial kubeconfigs")
        for kubeconfig in self.kubeconfigs:
            if kubeconfig["metadata"]["name"] in ["autoscaler", "forecaster"] and kubeconfig["kind"] == "Deployment":
                late_deployments.append(kubeconfig)
            else:
                kubectl_apply(kubeconfig)

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
        print("running nix init scripts")
        if reinit_db:
            nix("run", "path:/tmp/forecaster#reinit", working_directory="/tmp/forecaster")
            nix("run", "path:/tmp/forecaster#deploy", working_directory="/tmp/forecaster")

        print("Applying late kubeconfigs")
        # Do the late deployments
        for kubeconfig in late_deployments:
            kubectl_apply(kubeconfig)
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
        for name in self.workload_kubeconfigs:
            service = [service for service in services if service["name"] == name][0]
            service_id = service["id"]
            service["autoscalingEnabled"] = True

            settings = curl(f"localhost:{autoscaler_exposed_port}/services/{service_id}/settings")
            settings["scaleUp"] = int(self.scale_up*100)
            settings["scaleDown"] = int(self.scale_down*100)
            settings["minReplicas"] = self.min_replicas
            settings["maxReplicas"] = self.max_replicas
            
            if not curl(f"localhost:{autoscaler_exposed_port}/services/{service_id}",  [
                "--json",
                dumps(service)
            ], json=False) == "true":
                print(f"Failed to set service data: {dumps(service)}")
                exit(1)
            if not curl(f"localhost:{autoscaler_exposed_port}/services/{service_id}/settings", [
                "--json",
                dumps(settings)
            ], json=False) == "true":
                print(f"Failed to set settings data: {dumps(settings)}")
                exit(1)
        print("Rediscovering services/starting autoscaling")
        curl(f"localhost:{autoscaler_exposed_port}/services/start", json=False)
