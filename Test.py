from os import get_terminal_size
from tests.Baseline import Baseline
from tests.StudyResult import StudyResult
import lib.Arguments as args # force entire module to load
from lib.Plot import plot_from_file

if args.plot is not None:
    plot_from_file(args.plot)
    exit(0)


def headline(title: str) -> str:
    total = get_terminal_size()[0]
    needed = total - (len(title) + 2)
    left = needed // 2
    right = needed - left
    return f"{'-'*left} {title} {'-'*right}"

print(args.parser.prog)

size = {
    "x": 10,
    "y": 10
}

workload_configs = [
    (100, 4000, "mapped"),
    (100, 4000, "sinusodal")
]

forecaster_remote_config = (
    "http://10.92.1.54:8085",
)

tests = [
    # This first entry is for initialization
    #StudyResult("study-short-10x10", size=size, workload_configs=workload_configs, period=60)
    StudyResult("study-v2-candidate-check", size=size, period=7200, workload_configs=workload_configs, forecaster_remote_config=forecaster_remote_config, deployment_settings={
        "scaleperiod":"600000"
    }),
    Baseline("baseline", size=size, workload_configs=workload_configs),
    StudyResult("study-v2-candidate", size=size, workload_configs=workload_configs, forecaster_remote_config=forecaster_remote_config),
]

for test in tests:
    test.cleanup()
    test.kubernetes_setup()
    print(headline(test.name))
    print(f"test duration: {test.period} seconds")
    test.run()
    # cleanup again to clean up local dependencies
    test.cleanup()
    print(f"{test}\nFinshed, saving results...")
    print("-"*get_terminal_size()[0])
