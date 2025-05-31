import os
from lib.TestCase import TestCase
from json import dumps
from uuid import uuid4
import cloudpickle
from datetime import datetime
from lib.Utils import createdb, curl, dropdb, kubectl, kubectl_apply, logged_delay, clone_repository, nix, postgresql_execute
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
        if reinit_db:
            self.reinit()
        else:
            postgresql_execute("delete from historicdata")
            postgresql_execute("delete from forecasts")
            postgresql_execute("update services set autoscalingEnabled = false")

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
            service = [service for service in services if service["name"] == f"{name}-api"][0]
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


    def reinit(self):
        dropdb()
        createdb()
        clone_repository("https://github.com/aau-p9s/autoscaler", "/tmp/autoscaler")
        for file_name in os.listdir("/tmp/autoscaler/Autoscaler.DbUp/Scripts"):
            if not "SeedData" in file_name:
                with open(f"/tmp/autoscaler/Autoscaler.DbUp/Scripts/{file_name}", "r") as file:
                    sql = file.read()
                postgresql_execute(sql)

        for model_name in os.listdir("./models"):
            with open(f"./models/{model_name}/{model_name}.pth", "rb") as file:
                try:
                    model = cloudpickle.load(file)
                    print(f"Loaded {model_name}")
                except Exception:
                    print(f"Failed to load {model_name}")
                    continue
                binary = cloudpickle.dumps(model)
                postgresql_execute("insert into models (id, name, bin, trainedat, serviceid) select %s, %s, %s, %s, id from services", [
                    str(uuid4()), model_name, binary, datetime.now()
                ])


        nix("run", "path:/tmp/forecaster#deploy", working_directory="/tmp/forecaster")
