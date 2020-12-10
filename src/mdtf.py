#!/usr/bin/env python

# ======================================================================
# NOAA Model Diagnotics Task Force (MDTF) Diagnostic Driver
#
# March 2019
# Dani Coleman, NCAR
# Chih-Chieh (Jack) Chen, NCAR, 
# Yi-Hung Kuo, UCLA
#
# The MDTF code package and the participating PODs are distributed under
# the LGPLv3 license (see LICENSE.txt).
# ======================================================================

import sys
# do version check before importing other stuff
if sys.version_info[0] != 3 or sys.version_info[1] < 7:
    sys.exit("ERROR: MDTF currently only supports python >= 3.7.*. Please check "
    "which version is on your $PATH (e.g. with `which python`.)\n"
    f"Attempted to run with following python version:\n{sys.version}")
# passed; continue with imports
import os
import logging
from src import cli, mdtf_info
from src.util import logs

_log = logging.getLogger()
_log.setLevel(logging.INFO)
logging.captureWarnings(True)

def main():
    # get dir of currently executing script: 
    cwd = os.path.dirname(os.path.realpath(__file__)) 
    code_root = os.path.dirname(cwd)

    # poor man's subparser: argparse's subparser doesn't handle this
    # use case easily, so just dispatch on first argument
    if len(sys.argv) == 1 or \
        len(sys.argv) == 2 and sys.argv[1].lower().endswith('help'):
        # build CLI, print its help and exit
        cli_obj = cli.MDTFTopLevelArgParser(code_root)
        cli_obj.print_help()
    elif sys.argv[1].lower() == 'info': 
        # "subparser" for command-line info
        mdtf_info.InfoCLIHandler(code_root, sys.argv[2:])
    else:
        # run the actual framework
        # Cache log info in memory until log file is set up
        log_cache = logs.MultiFlushMemoryHandler(1024*16, flushOnClose=False)
        _log.addHandler(log_cache)

        # not printing help or info, setup CLI normally 
        cli_obj = cli.MDTFTopLevelArgParser(code_root)
        framework = cli_obj.dispatch()
        print(framework)
        exit_code = framework.main()
        exit(exit_code)

    logging.shutdown()

# should move this out of "src" package, but need to create wrapper shell script
# to set framework conda env.
if __name__ == '__main__':
    main()
    exit(0)
