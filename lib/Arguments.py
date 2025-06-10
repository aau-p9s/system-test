import argparse
import sys

parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--logfrequency", "-l", type=int, default="-1")
parser.add_argument("--reinitdb", "-r", action="store_true")
parser.add_argument("--postgres_address", type=str, default="localhost")
parser.add_argument("--postgres_port", type=int, default=30432)
parser.add_argument("--postgres_database", type=str, default="autoscaler")
parser.add_argument("--postgres_user", type=str, default="root")
parser.add_argument("--postgres_password", type=str, default="password")
parser.add_argument("--deployment", "-d", type=str, default="kubernetes")
parser.add_argument("--plot", "-p", type=str, default=None)

args = vars(parser.parse_args())
verbose = args["verbose"]
log_frequency = args["logfrequency"]
reinit_db = args["reinitdb"]
postgres_address = args["postgres_address"]
postgres_port = args["postgres_port"]
postgres_database = args["postgres_database"]
postgres_user = args["postgres_user"]
postgres_password = args["postgres_password"]
deployment = args["deployment"]
plot = args["plot"]
