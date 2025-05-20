from lib.TestCase import TestCase
from tests.Baseline import Baseline
from tests.GroundTruth import GroundTruth
from tests.StudyResult import StudyResult

import argparse
import sys

parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument("target")
parser.add_argument("target_deployment")
parser.add_argument("--raw", type=bool, default=False)

args = vars(parser.parse_args())
target = args["target"]
target_deployment = args["target_deployment"]

TestCase.target = args["target"]
TestCase.target_deployment = args["target_deployment"]
TestCase.print_raw = args["raw"]

tests:list[TestCase] = [
    Baseline("Baseline-10x10", size={"x":10, "y":10}),
    GroundTruth("GroundTruth-10x10", size={"x":10, "y":10}),
    StudyResult("StudyResult-10x10", size={"x":10, "y":10})
]

for test in tests:
    test.cleanup()
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
