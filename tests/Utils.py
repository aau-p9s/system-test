from lib.TestCase import TestCase
from tests.Baseline import Baseline
from tests.GroundTruth import GroundTruth
from tests.StudyResult import StudyResult
from tests.Idle import Idle

def make_test_triple(name: str, size: dict[str, int] = {"x": 10, "y": 10}, period: int = 86400, delay: int = 25, scale_up: float = .5, scale_down: float = .2, min_replicas: int = 1, max_replicas: int = 10, workload_count: int = 1, idle=False) -> list[TestCase]:
    return [
        Baseline(f"Baseline-{name}", size, period, delay, scale_up, scale_down, min_replicas, max_replicas, workload_count),
        GroundTruth(f"GroundTruth-{name}", size, period, delay, scale_up, scale_down, min_replicas, max_replicas, workload_count),
        StudyResult(f"StudyResult-{name}", size, period, delay, scale_up, scale_down, min_replicas, max_replicas, workload_count)
    ] + [Idle(f"Idle-{name}", period=period)] if idle else []
