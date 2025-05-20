from lib.TestCase import TestCase
from tests.Baseline import Baseline
from tests.GroundTruth import GroundTruth
from tests.StudyResult import StudyResult
import lib.Arguments as args # force entire module to load

print(f"argparse name: {args.parser.prog}")

size = {
    "x": 10,
    "y": 10
}

tests:list[TestCase] = [
    Baseline("Quick-Baseline-10x10", size=size, period=360),
    GroundTruth("Quick-GroundTruth-10x10", size=size, period=360),
    StudyResult("Quick-StudyResult-10x10", size=size, period=360),
    Baseline("Baseline-10x10", size=size),
    GroundTruth("GroundTruth-10x10", size=size),
    StudyResult("StudyResult-10x10", size=size)
]

for test in tests:
    test.cleanup()
    test.kubernetes_setup()
    for runid in range(test.tests):
        print(f"starting run #{runid}")
        print(f"test duration: {test.period} seconds")
        test.run()
    print(f"{test}\nFinshed, saving results...")

    test.save()
