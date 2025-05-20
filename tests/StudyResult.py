from os import system
from subprocess import check_output
from time import sleep
from lib.TestCase import TestCase
from json import dumps, loads
from lib.data import autoscaler_deployment

autoscaler_port = 8080
forecaster_port = 8081
postgres_port = 5432

class StudyResult(TestCase):
    def kubernetes_setup(self):
        autoscaler_kubeconfig = autoscaler_deployment("autoscaler", "root", "password", postgres_port, autoscaler_port, forecaster_port)
        late_deployments = []
        for kubeconfig in autoscaler_kubeconfig:
            if kubeconfig["metadata"]["name"] in ["autoscaler", "forecaster"] and kubeconfig["kind"] == "Deployment":
                late_deployments.append(kubeconfig)
            else:
                system(f"echo '{dumps(kubeconfig)}' | kubectl apply -f -")

        system("""
            rm -rf /tmp/autoscaler /tmp/forecaster
            git clone https://github.com/aau-p9s/autoscaler /tmp/autoscaler
            git clone -b "feat/model_deployment_scripts" https://github.com/aau-p9s/forecaster /tmp/forecaster
            cp -r /tmp/autoscaler/Autoscaler.Api/BaselineModels /tmp/forecaster/Assets/models
            nix run path:/tmp/forecaster#reinit
            nix run path:/tmp/forecaster#deploy
        """)

        # Do the late deployments
        for kubeconfig in late_deployments:
            system(f"echo '{dumps(kubeconfig)}' | kubectl apply -f -")
        # Wait for deployments ready
        system("""
            kubectl wait --for=condition=Available deployments/autoscaler
            kubectl wait --for=condition=Available deployments/forecaster
        """)

        system(f"curl localhost:{autoscaler_port}/services/start")
        services = loads(check_output(["curl", f"localhost:{autoscaler_port}/services"]).decode())
        service_id = ""
        for i, service in enumerate(services):
            if service["name"] == self.target_deployment:
                services[i]["autoscalingEnabled"] = True
                service_id = service["id"]
                break

        settings = loads(check_output(["curl", f"localhost:{autoscaler_port}/services/{service_id}"]))
        settings["scaleUp"] = self.scale_up
        settings["scaleDown"] = self.scale_down
        settings["minReplicas"] = self.min_replicas
        settings["maxReplicas"] = self.max_replicas

        system(f"""
            curl localhost:{autoscaler_port}/services --json '{dumps(services)}'
            curl localhost:{autoscaler_port}/services/{service_id}/settings --json '{dumps(settings)}'
            curl localhost:{autoscaler_port}/services/start
        """)
