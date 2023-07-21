#!/usr/bin/env python3

# This is the top-level python script for the MDTF-diagnostics package.
# See http://gfdl.noaa.gov/mdtf-diagnostics.

# NOTE: Under the standard installation procedure, users should never call this
# script directly, but should instead call the "mdtf" wrapper shell script
# created during installation.

import sys
from enum import Enum

# do version check before anything else
if sys.version_info.major != 3 or sys.version_info.minor < 10:
    sys.exit("ERROR: The MDTF-diagnostics package requires python >= 3.10. Please check "
             "which version of python is on your $PATH (e.g. with `which python`.)\n"
             f"Attempted to run with following python version:\n{sys.version}")
# passed; continue with imports
import os
import click
from src import util, cli, pod_setup, translation
from src.conda import conda_utils
import dataclasses
import logging
import datetime


_log = logging.getLogger(__name__)


class MainLogger(util.MDTFObjectLoggerMixin, util.MDTFObjectLogger):
    """Class to hold logging information for main driver script"""
    log: dataclasses.InitVar = _log
    name: str

    def __init__(self, log_dir: str):
        if not os.path.exists:
            os.mkdir(log_dir)
        self.name = "MDTF_main.{:%Y-%m-%d:%H.%M.%S}".format(datetime.datetime.now())
        # Access MDTFObjectLogger attributes
        super().__init__(name=self.name)
        self.init_log(log_dir=log_dir)


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
def main(ctx, configfile: str, verbose: bool = False) -> int:
    """A community-developed package to run Process Oriented Diagnostics on weather and climate data
    """
    status: util.ObjectStatus = dataclasses.field(default=util.ObjectStatus.NOTSET, compare=False)
    # Cache log info in memory until log file is set up
    util.logs.initial_log_config()

    conda_utils.verify_conda_env('_MDTF_base')
    # case where we run the actual framework
    # print(f"=== Starting {os.path.realpath(__file__)}\n")

    # not printing help or info, setup CLI normally
    # cli_obj = cli.MDTFTopLevelArgParser(code_root,argv=argv)
    # framework = cli_obj.dispatch()
    # exit_code = framework.main()
    # NameSpace allows dictionary keys to be referenced with dot notation
    ctx.config = util.NameSpace()
    # parse the runtime config file
    ctx.config = cli.parse_config_file(configfile)
    # add path of currently executing script
    print(ctx.config.WORK_DIR)
    ctx.config.CODE_ROOT = os.path.dirname(os.path.realpath(__file__))
    cli.verify_runtime_config_options(ctx.config)
    log = MainLogger(log_dir=ctx.config["WORK_DIR"])
    if verbose:
        log.log.debug("Initialized cli context")
    # configure a variable translator object with information from Fieldlist tables
    var_translator = translation.VariableTranslator(ctx.config.CODE_ROOT)
    var_translator.read_conventions(ctx.config.CODE_ROOT)
    # configure pod object(s)
    for pod_name in ctx.config.pod_list:
        pod_obj = pod_setup.PodObject(pod_name, ctx.config)
        pod_obj.setup_pod(ctx.config)

    # close the main log file
    log._log_handler.close()
    return util.exit_handler(code=0)


if __name__ == '__main__':
    exit_code = main(prog_name='MDTF-diagnostics')
    sys.exit(exit_code)
