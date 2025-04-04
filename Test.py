from lib.TestCase import TestCase
from tests.Baseline import Baseline
from tests.GroundTruth import GroundTruth
from tests.StudyResult import StudyResult

import argparse
import sys

parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument("target")

target = vars(parser.parse_args())["target"]

TestCase.target = target

tests:list[TestCase] = [
    GroundTruth("Test-GT", size={"x":2000, "y":2000}, delay=10, period=60), # test tests test
    Baseline("Test-BL", size={"x":1000, "y":1000}, delay=10, period=60), # test tests test
    Baseline("Baseline"),
    GroundTruth("GroundTruth"),
    StudyResult("Study"),
    Baseline("Baseline-10x10", size={"x":10, "y":10}),
    GroundTruth("GroundTruth-10x10", size={"x":10, "y":10}),
    StudyResult("Study-10x10", size={"x":10, "y":10}),
    Baseline("Baseline-100x100", size={"x":100, "y":100}),
    GroundTruth("GroundTruth-100x100", size={"x":100, "y":100}),
    StudyResult("Study-100x100", size={"x":100, "y":100}),
    Baseline("Baseline-1000x1000", size={"x":1000, "y":1000}),
    GroundTruth("GroundTruth-1000x1000", size={"x":1000, "y":1000}),
    StudyResult("Study-1000x1000", size={"x":1000, "y":1000}),
    Baseline("Baseline-2000x2000", size={"x":2000, "y":2000}),
    GroundTruth("GroundTruth-2000x2000", size={"x":2000, "y":2000}),
    StudyResult("Study-2000x2000", size={"x":2000, "y":2000}),
    GroundTruth("GroundTruth-40-15", scale_up=0.4, scale_down=.15),
    StudyResult("Study-40-15", scale_up=0.4, scale_down=.15),
    GroundTruth("GroundTruth-30-10", scale_up=0.3, scale_down=.1),
    StudyResult("Study-30-10", scale_up=0.3, scale_down=.1),
    GroundTruth("GroundTruth-20-05", scale_up=0.2, scale_down=.05),
    StudyResult("Study-20-05", scale_up=0.2, scale_down=.05),
    GroundTruth("GroundTruth-r-2-10", min_replicas=2),
    StudyResult("Study-r-4-10", min_replicas=2),
    GroundTruth("GroundTruth-r-1-20", max_replicas=20),
    StudyResult("Study-r-1-20", max_replicas=20),
    GroundTruth("GroundTruth-r-2-20", min_replicas=2, max_replicas=20),
    StudyResult("Study-r-2-20", min_replicas=2, max_replicas=20),
    GroundTruth("GroundTruth-r-4-20", min_replicas=4, max_replicas=20),
    StudyResult("Study-r-4-20", min_replicas=4, max_replicas=20)
]

for test in tests:
    test.kubernetes_setup()
    for runid in range(test.tests):
        print(f"starting run #{runid}")
        print(f"test duration: {test.period} seconds")
        test.run()
    print(f"{test}\nFinshed, results: ")
    for result in test.response_data:
        for timestamp, response in result.items():
            print(f"{timestamp},{response['response_time']}")

    test.save()
