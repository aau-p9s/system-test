from lib.TestCase import TestCase

class Baseline(TestCase):
    def __init__(self, size:dict[str, int] = {"x":4000, "y":4000}, period:int = 86400, delay:int = 25, tests:int = 3):
        super().__init__(size, period, delay, tests)

    def setup_HPA(self):
        print("baseline does not use HPA, skipping...")
