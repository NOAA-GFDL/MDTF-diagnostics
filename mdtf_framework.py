#!/usr/bin/env python3

# This is the top-level python script for the MDTF diagnostics package.
# See http://gfdl.noaa.gov/mdtf-diagnostics.

# NOTE: Under the standard installation procedure, users should never call this
# script directly, but should instead call the "mdtf" wrapper shell script
# created during installation.

import sys
# do version check before anything else
if sys.version_info.major != 3 or sys.version_info.minor < 10:
    sys.exit("ERROR: The MDTF package requires python >= 3.10. Please check "
        "which version of python is on your $PATH (e.g. with `which python`.)\n"
        f"Attempted to run with following python version:\n{sys.version}")
# passed; continue with imports
import os
import click
from src import cli
from src.util import logs

@click.option('-f',
              '--configfile',
              required=True,
              type=click.Path(),
              help='Path to the runtime configuration file'
              )
@click.option("-v",
              "--verbose",
              is_flag=True,
              default=False,
              help="Enables verbose mode.")

@click.command()
@click.pass_context
def main(ctx, configfile:str, verbose:bool=False)->int:
    """A community-developed package to run Process Oriented Diagnostics on weather and climate data
    """
    # get dir of currently executing script:
    code_root = os.path.dirname(os.path.realpath(__file__))
    # Cache log info in memory until log file is set up
    logs.initial_log_config()

    # case where we run the actual framework
    #print(f"=== Starting {os.path.realpath(__file__)}\n")

        # not printing help or info, setup CLI normally
        #cli_obj = cli.MDTFTopLevelArgParser(code_root,argv=argv)
        #framework = cli_obj.dispatch()
       # exit_code = framework.main()
    ctx.config = cli.parse_config_file(configfile)


if __name__ == '__main__':
    main(prog_name='MDTF-diagnostics')
