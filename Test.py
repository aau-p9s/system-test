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
    Baseline(size={"x":500, "y":500}, delay=10, period=60), # test tests test
    GroundTruth(size={"x":2000, "y":2000}, delay=10, period=60), # test tests test
    Baseline(),
    GroundTruth(),
    StudyResult(),
    Baseline(size={"x":100, "y":100}),
    GroundTruth(size={"x":100, "y":100}),
    StudyResult(size={"x":100, "y":100}),
    Baseline(size={"x":1000, "y":1000}),
    GroundTruth(size={"x":1000, "y":1000}),
    StudyResult(size={"x":1000, "y":1000}),
    Baseline(size={"x":2000, "y":2000}),
    GroundTruth(size={"x":2000, "y":2000}),
    StudyResult(size={"x":2000, "y":2000}),
    GroundTruth(scale_up=0.4, scale_down=.15),
    StudyResult(scale_up=0.4, scale_down=.15),
    GroundTruth(scale_up=0.3, scale_down=.1),
    StudyResult(scale_up=0.3, scale_down=.1),
    GroundTruth(scale_up=0.2, scale_down=.05),
    StudyResult(scale_up=0.2, scale_down=.05),
    GroundTruth(min_replicas=2),
    StudyResult(min_replicas=4),
    GroundTruth(max_replicas=20),
    StudyResult(max_replicas=20),
    GroundTruth(min_replicas=2, max_replicas=20),
    StudyResult(min_replicas=2, max_replicas=20),
    GroundTruth(min_replicas=4, max_replicas=20),
    StudyResult(min_replicas=4, max_replicas=20)
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
            print(f"{timestamp},{response}")

    test.save()
