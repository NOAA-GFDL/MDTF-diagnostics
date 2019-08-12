#! /usr/bin/env python
import os
import sys
import argparse
import util
from shared_runner import DiagnosticRunner


cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbosity", action="count",
                    help="Increase output verbosity")
parser.add_argument("--test_mode", action="store_const", const=True,
                    help="Set flag to not call PODs, just say what would be called")
# default paths set in config.yml/paths
parser.add_argument('--DIAG_HOME', nargs='?', type=str, 
                    default=os.path.realpath(os.path.join(cwd, '..')),
                    help="Code installation directory.")
parser.add_argument('--MODEL_ROOT_DIR', nargs='?', type=str, 
                    help="Parent directory containing results from different models.")
parser.add_argument('--OBS_ROOT_DIR', nargs='?', type=str, 
                    help="Parent directory containing observational data used by individual PODs.")
parser.add_argument('--WORKING_DIR', nargs='?', type=str, 
                    help="Working directory.")
parser.add_argument('--OUTPUT_DIR', nargs='?', type=str, 
                    help="Directory to write output files. Defaults to working directory.")
parser.add_argument('config_file', nargs='?', type=str, 
                    default=os.path.join(cwd, 'config.yml'),
                    help="Configuration file.")
args = parser.parse_args()
if args.verbosity == None:
    verbose = 1
else:
    verbose = args.verbosity + 1 # fix for case  verb = 0

print "==== Starting "+__file__
try:
    config = util.read_mdtf_config_file(args.config_file, verbose=verbose)
except Exception as error:
    print error
    exit()

runner = DiagnosticRunner(args, config)
runner.setUp(config, config['case_list'])
runner.run(config)
runner.tearDown(config)

print "Exiting normally from ",__file__
exit()