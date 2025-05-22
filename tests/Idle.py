
from time import time
from lib.Metrics import measure_power_usage
from lib.TestCase import TestCase


class Idle(TestCase):
    def __init__(self, name: str, period: int = 86400):
        super().__init__(name, period = period)
        self.csv_name = lambda _: f"{name}-main.csv"

    def kubernetes_setup(self):
        pass

    def run(self):
        results = { "main": [] }


        start_time = time()
        end_time = start_time + self.period
        
        while time() < end_time:
            results["main"].append(["", "", "", measure_power_usage()[1]])

        self.save(results)
