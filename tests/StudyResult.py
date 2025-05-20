from os import system
from subprocess import check_output
from time import sleep
from lib.TestCase import TestCase
from json import dumps, loads
from lib.data import autoscaler_deployment

wait_time = 10

autoscaler_port = 8080
forecaster_port = 8081
postgres_port = 5432

class StudyResult(TestCase):
    def kubernetes_setup(self):
        autoscaler_kubeconfig = autoscaler_deployment("autoscaler", "root", "password", postgres_port, autoscaler_port, forecaster_port)
        for kubeconfig in autoscaler_kubeconfig:
            system(f"echo '{dumps(kubeconfig)}' | kubectl apply -f -")
        print("Waiting for {wait_time} seconds")
        # Wait for deployments ready
        system("""
            kubectl wait --for=condition=Available deployments/autoscaler
            kubectl wait --for=condition=Available deployments/forecaster
        """)
        system("""
            rm -rf /tmp/autoscaler /tmp/forecaster
            git clone https://github.com/aau-p9s/autoscaler /tmp/autoscaler
            git clone -b "feat/model_deployment_scripts" https://github.com/aau-p9s/forecaster /tmp/forecaster
            mkdir -p /tmp/forecaster/Assets/models
            cp -r /tmp/autoscaler/Autoscaler.Api/BaselineModels/* /tmp/forecaster/Assets/models/
            nix run path:/tmp/forecaster#reinit
            dotnet run --project /tmp/autoscaler/Autoscaler.DbUp
            nix run path:/tmp/forecaster#deploy
        """)
        system("curl localhost:{autoscaler_port}/services/start")
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
