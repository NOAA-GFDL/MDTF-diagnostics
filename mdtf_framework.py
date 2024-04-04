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
import copy
import click
from src import util, cli, data_sources, pod_setup, preprocessor, translation, environment_manager, output_manager
import dataclasses
import logging
import datetime
import collections


_log = logging.getLogger(__name__)

ConfigTuple = collections.namedtuple(
    'ConfigTuple', 'name backup_filename contents'
)
ConfigTuple.__doc__ = """
    Class wrapping general structs used for configuration.
"""


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


def print_summary(pods, _log: logging.log):
    def summary_info_tuple(pod):
        """create tuple of ([failed cases], [not failed cases], POD_OUTPUT_DIR) for input pod
        """
        return (
            [p_name for p_name, p in pod.multi_case_dict['CASE_LIST'].items() if pod.failed],
            [p_name for p_name, p in pod.multi_case_dict['CASE_LIST'].items() if not pod.failed],
            getattr(pod.paths, 'POD_OUTPUT_DIR', '<ERROR: dir not created.>')
        )

    d = {p_name: summary_info_tuple(p) for p_name, p in pods.items()}
    failed = any(len(tup[0]) > 0 for tup in d.values())
    _log.info('\n' + (80 * '-'))
    if failed:
        _log.info(f"Exiting with errors.")
        for case_name, tup in d.items():
            _log.info(f"Summary for {case_name}:")
            if tup[0][0] == 'dummy sentinel string':
                _log.info('\tAn error occurred in setup. No PODs were run.')
            else:
                if tup[1]:
                    _log.info((f"\tThe following PODs exited normally: "
                               f"{', '.join(tup[1])}"))
                if tup[0]:
                    _log.info((f"\tThe following PODs raised errors: "
                               f"{', '.join(tup[0])}"))
            _log.info(f"\tOutput written to {tup[2]}")
    else:
        _log.info(f"Exiting normally.")
        for pod_name, tup in d.items():
            _log.info(f"Summary for {pod_name}:")
            _log.info(f"\tAll PODs exited normally.")
            _log.info(f"\tOutput written to {tup[2]}")
        for pod_name, pod_atts in pods.items():
            pod_atts.status = util.ObjectStatus.SUCCEEDED


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

    def backup_config(config):
        """Copy serializable version of parsed settings, in order to write
        backup config file.
        """
        d = copy.deepcopy(config)
        d = {k: v for k, v in d.items() if not k.endswith('_is_default_')}
        d['case_list'] = copy.deepcopy(config.case_list)
        return ConfigTuple(
            name='backup_config',
            backup_filename='config_save.json',
            contents=d
        )

    # Cache log info in memory until log file is set up
    util.logs.initial_log_config()

    # print(f"=== Starting {os.path.realpath(__file__)}\n")
    # NameSpace allows dictionary keys to be referenced with dot notation
    ctx.config = util.NameSpace()
    # parse the runtime config file
    ctx.config = cli.parse_config_file(configfile)
    # Test ctx.config
    # print(ctx.config.WORK_DIR)
    ctx.config.CODE_ROOT = os.path.dirname(os.path.realpath(__file__))
    ctx.config.TEMP_DIR_ROOT = ctx.config.WORK_DIR
    log_config = cli.read_config_file(
        ctx.config.CODE_ROOT, "src", "logging.jsonc"
    )
    cli.verify_runtime_config_options(ctx.config)
    # Initialize the model path object and define the model data output paths
    make_new_work_dir = not ctx.config.overwrite
    model_paths = util.ModelDataPathManager(ctx.config,
                                            new_work_dir=make_new_work_dir)
    model_paths.setup_data_paths(ctx.config.case_list)
    ctx.config.update({'WORK_DIR': model_paths.WORK_DIR})
    ctx.config.update({'OUTPUT_DIR': model_paths.OUTPUT_DIR})
    cat_path = ctx.config.DATA_CATALOG
    ctx.config.update({'DATA_CATALOG': util.filesystem.resolve_path(cat_path)})
    # TODO: update paths in ctx.config so that POD paths are placed in the correct sub-directories
    backup_config = backup_config(ctx.config)
    ctx.config._configs = dict()
    ctx.config._configs[backup_config.name] = backup_config
    ctx.config._configs['log_config'] = ConfigTuple(
        name='log_config',
        backup_filename=None,
        contents=log_config
    )

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
    # set up the case data source dictionary
    cases = dict()
    for case_name, case_dict in ctx.config.case_list.items():
        # instantiate the data_source class instance for the specified convention
        cases[case_name] = data_sources.data_source[case_dict.convention.upper() + "DataSource"](case_name,
                                                                                                 case_dict,
                                                                                                 model_paths,
                                                                                                 parent=None)
        cases[case_name].set_date_range(case_dict.startdate, case_dict.enddate)

    pods = dict.fromkeys(ctx.config.pod_list, [])
    pod_runtime_reqs = dict()
    # configure pod object(s)
    for pod_name in ctx.config.pod_list:
        pods[pod_name] = pod_setup.PodObject(pod_name, ctx.config)
        pods[pod_name].setup_pod(ctx.config, model_paths, cases)
        pods[pod_name].log.info(f"Preprocessing data for {pod_name}")
        for k, v in pods[pod_name].runtime_requirements.items():
            if not hasattr(pod_runtime_reqs, k):
                pod_runtime_reqs[k] = v
    # run module(s)
    if "module_list" in ctx.config:
        for module in ctx.config.module_list:
            module_obj = __import__(module)
            for function in ctx.config.module_list[module]:
                args = ctx.config.module_list[module][function].args
                func = getattr(module_obj, function)
                func(args)
    # read the subset of data for the cases and date range(s) and preprocess the data
    cat_subset = data_pp.process(cases, ctx.config, model_paths.MODEL_WORK_DIR)
    # write the preprocessed files
    data_pp.write_ds(cases, cat_subset, pod_runtime_reqs)
    # write the ESM intake catalog for the preprocessed  files
    data_pp.write_pp_catalog(cat_subset, model_paths, log.log)
    # configure the runtime environments and run the POD(s)
    if not any(p.failed for p in pods.values()):
        log.log.info("### %s: running pods '%s'.", [p for p in pods.keys()])
        run_mgr = environment_manager.SubprocessRuntimeManager(pods, ctx.config, log)
        run_mgr.setup()
        run_mgr.run(cases, log)
    else:
        for p in pods.values:
            if any(p.failed):
                log.log.info("Data request for pod '%s' failed; skipping  execution.", p)

    # convert POD figure files if necessary
    # generate html output
    for p in pods.values():
        out_mgr = output_manager.HTMLOutputManager(p, ctx.config)
        out_mgr.make_output(p, ctx.config)

    # clean up temporary directories
    tempdirs = util.TempDirManager(ctx.config)
    tempdirs.cleanup()

    print_summary(pods, log.log)
    # close the varlistEntry log handlers
    for case_name, case_dict in cases.items():
        for var in case_dict.iter_children():
            var._log_handler.close()

    # close the main log file
    log._log_handler.close()

    if not any(v.failed for v in pods.values()):
        return util.exit_handler(code=0)
    else:
        return util.exit_handler(code=1)


if __name__ == '__main__':
    exit_code = main(prog_name='MDTF-diagnostics')
    sys.exit(exit_code)
