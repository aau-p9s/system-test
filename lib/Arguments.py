import argparse
import sys

parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument("target")
parser.add_argument("target_deployment")
parser.add_argument("--verbose", "-v", type=bool, default=False)

args = vars(parser.parse_args())
target = args["target"]
target_deployment = args["target_deployment"]
verbose = args["verbose"]
