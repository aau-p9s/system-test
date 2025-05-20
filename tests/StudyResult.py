from os import system
from time import sleep
from lib.TestCase import TestCase
from lib.data import autoscaler_deployment

wait_time = 10

class StudyResult(TestCase):
    def kubernetes_setup(self):
        autoscaler_kubeconfig = autoscaler_deployment("autoscaler", "root", "password", "5432", "8080", "8081")
        for kubeconfig in autoscaler_kubeconfig:
            system(f"echo '{kubeconfig}' | kubectl apply -f -")
        print("Waiting for {wait_time} seconds")
        sleep(wait_time)
        system("rm -rf /tmp/autoscaler /tmp/forecaster")
        system("git clone https://github.com/aau-p9s/autoscaler /tmp/autoscaler")
        system('git clone -b "feat/model_deployment_scripts" https://github.com/aau-p9s/forecaster /tmp/forecaster')
        system("mkdir -p /tmp/forecaster/Assets/models")
        system("cp -r /tmp/autoscaler/Autoscaler.Api/BaselineModels/* /tmp/forecaster/Assets/models/")
        system("dotnet run --project /tmp/autoscaler/Autoscaler.DbUp")
        system("nix run path:/tmp/forecaster#reinit")
        system("nix run path:/tmp/forecaster#deploy")
