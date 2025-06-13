from lib.TestCase import TestCase
from tests.Baseline import Baseline
from tests.GroundTruth import GroundTruth
from tests.StudyResult import StudyResult
from tests.Idle import Idle

def make_test_triple(name: str, size: dict[str, int] = {"x": 10, "y": 10}, period: int = 86400, scale_up: float = .5, scale_down: float = .2, min_replicas: int = 1, max_replicas: int = 10, workload_configs: list[tuple[int, int, str]] = [(50, 2000, "mapped")], idle=False) -> list[TestCase]:
    return [
        Baseline(f"Baseline-{name}", size, period, scale_up, scale_down, min_replicas, max_replicas, workload_configs),
        GroundTruth(f"GroundTruth-{name}", size, period, scale_up, scale_down, min_replicas, max_replicas, workload_configs),
        StudyResult(f"StudyResult-{name}", size, period, scale_up, scale_down, min_replicas, max_replicas, workload_configs)
    ] + ([Idle(f"Idle-{name}", period=period)] if idle else [])
