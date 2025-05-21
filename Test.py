from os import get_terminal_size
from lib.TestCase import TestCase
from tests.Utils import make_test_triple
import lib.Arguments as args # force entire module to load

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

tests: list[TestCase] = (
    make_test_triple("Quick-10x10", size=size, period=60) +
    make_test_triple("Quick-3-10x10", size=size, period=60, workload_count=3) +
    make_test_triple("Short-10x10", size=size, period=60*60*6) +
    make_test_triple("Short-3-10x10", size=size, period=60*60*6, workload_count=3) +
    make_test_triple("10x10", size=size) +
    make_test_triple("3-10x10", size=size, workload_count=3)
)

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
