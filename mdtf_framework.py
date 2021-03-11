#!/usr/bin/env python3

# This is the top-level python script for the MDTF diagnostics package.
# See http://gfdl.noaa.gov/mdtf-diagnostics.

# NOTE: Under the standard installation procedure, users should never call this
# script directly, but should instead call the "mdtf" wrapper shell script 
# created during installation.

import sys
# do version check before anything else
if sys.version_info.major != 3 or sys.version_info.minor < 7:
    sys.exit("ERROR: The MDTF package requires python >= 3.7. Please check "
        "which version of python is on your $PATH (e.g. with `which python`.)\n"
        f"Attempted to run with following python version:\n{sys.version}")
# passed; continue with imports
import os
import logging
from src import cli
from src.util import logs

def validate_base_environment():
    """Check that the package's required third-party dependencies (listed in 
    src/conda/env_base.yml) are accessible.
    """        
    # checking existence of one third-party module is imperfect, but will
    # catch the most common case where user hasn't installed environments
    try:
        import cfunits
    except ModuleNotFoundError:
        sys.exit("ERROR: MDTF dependency check failed. Please make sure the "
            "package's base environment has been activated prior to execution, e.g. "
            "by calling the 'mdtf' wrapper script.\nSee installation instructions "
            "at mdtf-diagnostics.rtfd.io/en/latest/sphinx/start_install.html.")

def main():
    # get dir of currently executing script: 
    code_root = os.path.dirname(os.path.realpath(__file__))

    # poor man's subparser: argparse's subparser doesn't handle this
    # use case easily, so just dispatch on first argument
    if len(sys.argv) == 1 or \
        len(sys.argv) == 2 and sys.argv[1].lower().endswith('help'):
        # build CLI, print its help and exit
        cli_obj = cli.MDTFTopLevelArgParser(code_root)
        cli_obj.print_help()
        return 0 # will actually exit from print_help
    elif sys.argv[1].lower() == 'info': 
        from src import mdtf_info
        # "subparser" for command-line info
        mdtf_info.InfoCLIHandler(code_root, sys.argv[2:])
        return 0 # will actually exit from print_help
    else:
        # run the actual framework
        print(f"=== Starting {os.path.realpath(__file__)}\n")
        validate_base_environment()

        # Cache log info in memory until log file is set up
        logs.configure_console_loggers()
        _log = logging.getLogger()
        _log.setLevel(logging.NOTSET)
        log_cache = logs.MultiFlushMemoryHandler(1024*16, flushOnClose=False)
        _log.addHandler(log_cache)

        # not printing help or info, setup CLI normally 
        cli_obj = cli.MDTFTopLevelArgParser(code_root)
        framework = cli_obj.dispatch()
        exit_code = framework.main()
        return exit_code

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
