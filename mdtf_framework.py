#!/usr/bin/env python3

# This is the top-level python script for the MDTF-diagnostics package.
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
from src import util, cli, pod_setup, preprocessor, translation, environment_manager, output_manager
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

    # print(f"=== Starting {os.path.realpath(__file__)}\n")
    # NameSpace allows dictionary keys to be referenced with dot notation
    ctx.config = util.NameSpace()
    # parse the runtime config file
    ctx.config = cli.parse_config_file(configfile)
    # Test ctx.config
    print(ctx.config.WORK_DIR)
    ctx.config.CODE_ROOT = os.path.dirname(os.path.realpath(__file__))
    cli.verify_runtime_config_options(ctx.config)
    # Initialize the model path object and define the model data output paths
    make_new_work_dir = not ctx.config.overwrite
    model_paths = util.ModelDataPathManager(ctx.config,
                                            new_work_dir=make_new_work_dir)
    model_paths.setup_data_paths(ctx.config.case_list)
    # Set up main logger
    log = MainLogger(log_dir=model_paths.WORK_DIR)
    if verbose:
        log.log.debug("Initialized cli context")
    # configure a variable translator object with information from Fieldlist tables
    var_translator = translation.VariableTranslator(ctx.config.CODE_ROOT)
    var_translator.read_conventions(ctx.config.CODE_ROOT)

    # initialize the preprocessor (dummy pp object if run_pp=False)
    data_pp = preprocessor.init_preprocessor(model_paths,
                                             ctx.config,
                                             ctx.config.run_pp
                                             )

    pods = dict.fromkeys(ctx.config.pod_list, [])
    # configure pod object(s)
    for pod_name in ctx.config.pod_list:
        pods[pod_name] = pod_setup.PodObject(pod_name, ctx.config)
        pods[pod_name].setup_pod(ctx.config, model_paths)
        # run custom scripts on dataset
        if any([s for s in ctx.config.user_pp_scripts]):
            pods[pod_name].add_user_pp_scripts(ctx.config)
        pods[pod_name].log.info(f"Preprocessing data for {pod_name}")
        cat_subset = data_pp.process(pods[pod_name].cases, ctx.config, model_paths.MODEL_WORK_DIR)
        data_pp.write_ds(pods[pod_name].cases, cat_subset, pods[pod_name].runtime_requirements)

    if not any(p.failed for p in pods.values()):
        log.log.info("### %s: running pods '%s'.", [p for p in pods.keys()])
        run_mgr = environment_manager.SubprocessRuntimeManager(pods, ctx.config, log)
        run_mgr.setup()
        run_mgr.run(log)
    else:
        for p in pods.values:
            if any(p.failed):
                log.log.info("Data request for pod '%s' failed; skipping  execution.", p)

    for p in pods.values():
        out_mgr = output_manager.HTMLOutputManager(p, ctx.config)
        out_mgr.make_output(p, ctx.config)
    tempdirs = util.TempDirManager()
    tempdirs.cleanup()

    # close the main log file
    log._log_handler.close()
    return util.exit_handler(code=0)


if __name__ == '__main__':
    exit_code = main(prog_name='MDTF-diagnostics')
    sys.exit(exit_code)
