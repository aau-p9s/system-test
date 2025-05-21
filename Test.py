from os import get_terminal_size
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
    Baseline("Quick-Baseline-10x10", size=size, period=60),
    GroundTruth("Quick-GroundTruth-10x10", size=size, period=60),
    StudyResult("Quick-StudyResult-10x10", size=size, period=60),
    Baseline("Quick-Baseline-3-10x10", size=size, period=60, workload_count=3),
    GroundTruth("Quick-GroundTruth-3-10x10", size=size, period=60, workload_count=3),
    StudyResult("Quick-StudyResult-3-10x10", size=size, period=60, workload_count=3),
    Baseline("Short-Baseline-10x10", size=size, period=60*60*6),
    GroundTruth("Short-GroundTruth-10x10", size=size, period=60*60*6),
    StudyResult("Short-StudyResult-10x10", size=size, period=60*60*6),
    Baseline("Baseline-10x10", size=size),
    GroundTruth("GroundTruth-10x10", size=size),
    StudyResult("StudyResult-10x10", size=size)
]

for test in tests:
    test.cleanup()
    test.kubernetes_setup()
    print(f"test duration: {test.period} seconds")
    test.run()
    # cleanup again to clean up local dependencies
    test.cleanup()
    print(f"{test}\nFinshed, saving results...")
    print("-"*get_terminal_size()[0])
