import argparse
import sys

parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--logfrequency", "-l", type=int, default="-1")
parser.add_argument("--reinitdb", "-r", action="store_true")

args = vars(parser.parse_args())
verbose = args["verbose"]
log_frequency = args["logfrequency"]
reinit_db = args["reinitdb"]
