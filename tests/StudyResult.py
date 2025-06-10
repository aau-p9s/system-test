import os
from lib.TestCase import TestCase
from json import dumps
from lib.Utils import curl, deploy, kubectl, logged_delay, clone_repository, postgresql_execute, postgresql_execute_get, reinit
from lib.Arguments import reinit_db, deployment

autoscaler_port = 8080
forecaster_port = 8081
postgres_port = 5432

autoscaler_exposed_port = 30000 + (autoscaler_port % 1000)


class StudyResult(TestCase[float|None, str|None]):
    def kubernetes_setup(self):
        super().kubernetes_setup()
        print("Applying kubeconfigs")
        deploy(self.kubeconfigs, ["autoscaler", "forecaster"])

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
            for name, value in self.deployment_settings.items():
                postgresql_execute(f"update settings set {name} = {value}")

        print("Applying late kubeconfigs")
        deploy(self.kubeconfigs)
        # Wait for deployments to be ready
        kubectl("wait", [
            "--for=condition=Available",
            "deployments/autoscaler"
        ])
        if self.forecaster_remote_config is None:
            kubectl("wait", [
                "--for=condition=Available",
                "deployments/forecaster"
            ])
        # a little extra just to be sure
        logged_delay(20)

        print("Discovering services")
        self.discover()


    def discover(self):
        curl(f"localhost:{autoscaler_exposed_port}/services/start", json=False)
        match deployment:
            case "docker":
                logged_delay(20)
                services = curl(f"localhost:{autoscaler_exposed_port}/services")
                print(services)
            case "kubernetes":
                # let shit run
                logged_delay(120 if reinit_db else 5)
        
                raw_services = curl(f"localhost:{autoscaler_exposed_port}/services")
                services = [service for service in raw_services if service["name"] == [f"{name}-api" for name in self.workload_kubeconfigs]]

            case _:
                raise ValueError(f"invalid deployment type {deployment}")

        for service in services:
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
                raise RuntimeError(f"Failed to set service data: {dumps(service)}")
            if not curl(f"localhost:{autoscaler_exposed_port}/services/{service_id}/settings", [
                "--json",
                dumps(settings)
            ], json=False) == "true":
                raise RuntimeError(f"Failed to set settings data: {dumps(settings)}")

        print("Rediscovering services/starting autoscaling")
        curl(f"localhost:{autoscaler_exposed_port}/services/start", json=False)


    def reinit(self):
        reinit()
        clone_repository("https://github.com/aau-p9s/autoscaler", "/tmp/autoscaler")
        for file_name in os.listdir("/tmp/autoscaler/Autoscaler.DbUp/Scripts"):
            if not "SeedData" in file_name:
                with open(f"/tmp/autoscaler/Autoscaler.DbUp/Scripts/{file_name}", "r") as file:
                    sql = file.read()
                postgresql_execute(sql)

    def extra_metrics(self, deployment):
        service_id = postgresql_execute_get(f"SELECT id FROM services WHERE name = '{deployment}-api'")[0][0]
        forecasts = postgresql_execute_get(f"SELECT modelid, forecast FROM forecasts WHERE serviceid = '{service_id}'")
        if len(forecasts) == 0:
            return (0, "")
        model_id, forecast = forecasts[0]
        error = forecast["rmse"] if "rmse" in forecast else None
        model_name = postgresql_execute_get(f"SELECT name FROM models WHERE id = '{model_id}'")[0][0]
        return error, model_name

    def column_names(self):
        return super().column_names() + ["error", "model"]
