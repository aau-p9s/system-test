from os import system
from time import sleep
from lib.TestCase import TestCase
from json import dumps
from lib.data import autoscaler_deployment

wait_time = 10

class StudyResult(TestCase):
    def kubernetes_setup(self):
        autoscaler_kubeconfig = autoscaler_deployment("autoscaler", "root", "password", "5432", "8080", "8081")
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
