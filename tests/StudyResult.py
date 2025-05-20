from os import system
from lib.TestCase import TestCase
from json import dumps
from lib.data import autoscaler_deployment

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
        self.kubectl("wait", [
            "--for=condition=Available",
            "deployments/postgres"
        ])
        # a little extra just to be sure
        self.logged_delay(10)

        # reinit and deploy db
        self.clone_repository("https://github.com/aau-p9s/autoscaler", "/tmp/autoscaler", "main")
        self.clone_repository("https://github.com/aau-p9s/forecaster", "/tmp/forecaster", "feat/model_deployment_scripts")
        system("""
            cp -r /tmp/autoscaler/Autoscaler.Api/BaselineModels /tmp/forecaster/Assets/models
            cd /tmp/forecaster
            nix run path:/tmp/forecaster#reinit
            nix run path:/tmp/forecaster#deploy
            cd -
        """)

        # Do the late deployments
        for kubeconfig in late_deployments:
            system(f"echo '{dumps(kubeconfig)}' | kubectl apply -f -")
        # Wait for deployments ready
        self.kubectl("wait", [
            "--for=condition=Available",
            "deployments/autoscaler"
        ])
        self.kubectl("wait", [
            "--for=condition=Available",
            "deployments/forecaster"
        ])
        # a little extra just to be sure
        self.logged_delay(20)

        self.curl(f"localhost:{autoscaler_exposed_port}/services/start", json=False)
        # let shit run
        self.logged_delay(5)

        services = self.curl(f"localhost:{autoscaler_exposed_port}/services")
        service = [service for service in services if service["name"] == self.target_deployment][0]
        service_id = service["id"]
        service["autoscalingEnabled"] = True

        settings = self.curl(f"localhost:{autoscaler_exposed_port}/services/{service_id}/settings")
        settings["scaleUp"] = self.scale_up
        settings["scaleDown"] = self.scale_down
        settings["minReplicas"] = self.min_replicas
        settings["maxReplicas"] = self.max_replicas
        
        self.curl(f"localhost:{autoscaler_exposed_port}/services",  [
            "--json",
            f"'{dumps(service)}'"
        ], json=False)
        self.curl(f"localhost:{autoscaler_exposed_port}/services/{service_id}/settings", [
            "--json",
            f"'{dumps(settings)}'"
        ], json=False)
        self.curl(f"localhost:{autoscaler_exposed_port}/services/start", json=False)
