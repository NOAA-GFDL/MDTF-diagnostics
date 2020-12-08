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

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
# do version check before importing other stuff
if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    print(("ERROR: MDTF currently only supports python >= 2.7. Please check "
    "which version is on your $PATH (e.g. with `which python`.)"))
    print("Attempted to run with following python version:\n{}".format(sys.version))
    exit(1)
# passed; continue with imports
import os
import signal
import shutil
from src import cli, util, util_mdtf, data_manager, environment_manager, \
    diagnostic

class MDTFFramework(object):
    def __init__(self, config, modules_to_search):
        self.code_root = config.code_root
        self.pod_list = config.pod_list
        self.case_list = config.case_list
        # delete temp files if we're killed
        signal.signal(signal.SIGTERM, self.cleanup_tempdirs)
        signal.signal(signal.SIGINT, self.cleanup_tempdirs)

        def _dispatch(setting):
            def _var_to_class_name(str_):
                # drop '_' and title-case class name
                return ''.join(str_.split('_')).title()

            class_prefix = config.config.get(setting, '')
            class_prefix = _var_to_class_name(util.coerce_from_iter(class_prefix))
            class_suffix = _var_to_class_name(setting)
            for mod in modules_to_search:
                try:
                    return getattr(mod, class_prefix+class_suffix)
                except Exception:
                    continue
            print("No class named {}.".format(class_prefix+class_suffix))
            raise Exception('no_class')

        self.Diagnostic = _dispatch('diagnostic')
        self.DataManager = _dispatch('data_manager')
        self.Preprocessor = _dispatch('preprocessor')
        self.EnvironmentManager = _dispatch('environment_manager')

    def cleanup_tempdirs(self, signum=None, frame=None):
        # delete temp files
        util.signal_logger(self.__class__.__name__, signum, frame)
        config = util_mdtf.ConfigManager()
        tmpdirs = util_mdtf.TempDirManager()
        if not config.config.get('keep_temp', False):
            tmpdirs.cleanup()

    def run_case(self, case_name, case_d):
        print(f"Framework: initialize {case_name}")
        pod_d = {
            pod_name: self.Diagnostic.from_config(pod_name) \
                for pod_name in case_d.get('pod_list', [])
        }
        case = self.DataManager(case_d, pod_d, self.Preprocessor)
        case.setup()

        print(f'Framework: get data for {case_name}')
        case.query_and_fetch_data()
        case.preprocess_data()

        print(f'Framework: run {case_name}')
        run_mgr = environment_manager.SubprocessRuntimeManager(
            pod_d, self.EnvironmentManager
        )
        run_mgr.setup()
        run_mgr.run()
        run_mgr.tear_down()
        case.tear_down()
        return self.summary_info_tuple(case, pod_d)

    def main_loop(self):
        # only run first case in list until dependence on env vars cleaned up
        summary_d = dict()
        for d in self.case_list[0:1]:
            case_name = d.get('CASENAME', '')
            summary_info = self.run_case(case_name, d)
            summary_d[case_name] = summary_info
        self.cleanup_tempdirs()
        bad_exit = self.print_summary(summary_d)
        return bad_exit

    @staticmethod
    def summary_info_tuple(case, pod_d):
        """Debug information; will clean this up.
        """
        if not pod_d:
            return (
                ['dummy sentinel string'], [],
                getattr(case, 'MODEL_OUT_DIR', '<ERROR: dir not created.>')
            )
        else:
            return (
                [p_name for p_name, p in pod_d.items() if p.failed],
                [p_name for p_name, p in pod_d.items() if not p.failed],
                getattr(case, 'MODEL_OUT_DIR', '<ERROR: dir not created.>')
            )

    @staticmethod
    def print_summary(d):
        failed = any(len(tup[0]) > 0 for tup in d.values())
        if failed:
            print(f"\nExiting with errors from {__file__}")
            for case_name, tup in d.items():
                print(f"Summary for {case_name}:")
                if tup[0][0] == 'dummy sentinel string':
                    print('\tAn error occurred in setup. No PODs were run.')
                else:
                    if tup[1]:
                        print((f"\tThe following PODs exited cleanly: "
                            f"{', '.join(tup[1])}"))
                    if tup[0]:
                        print((f"\tThe following PODs raised errors: "
                            f"{', '.join(tup[0])}"))
                print(f"\tOutput written to {tup[2]}")
        else:
            print(f"\nExiting normally from {__file__}")
            for case_name, tup in d.items():
                print(f"Summary for {case_name}:")
                print(f"\tAll PODs exited cleanly.")
                print(f"\tOutput written to {tup[2]}")
        return failed


def main(code_root, cli_rel_path):
    # poor man's subparser: argparse's subparser doesn't handle this
    # use case easily, so just dispatch on first argument
    if len(sys.argv) == 1 or \
        len(sys.argv) == 2 and sys.argv[1].lower().endswith('help'):
        # build CLI, print its help and exit
        cli_obj = cli.FrameworkCLIHandler(code_root, cli_rel_path)
        cli_obj.parser.print_help()
    elif sys.argv[1].lower() == 'info': 
        # "subparser" for command-line info
        cli.InfoCLIHandler(code_root, sys.argv[2:])
    else:
        # not printing help or info, setup CLI normally 
        # move into its own class so that child classes can customize
        # above options without having to rewrite below
        config = util_mdtf.ConfigManager(code_root, cli_rel_path)
        framework = MDTFFramework(
            config,
            (data_manager, environment_manager, diagnostic)
        )
        print(f"\n======= Starting {__file__}")
        bad_exit = framework.main_loop()
        if bad_exit:
            exit(1)

# should move this out of "src" package, but need to create wrapper shell script
# to set framework conda env.
if __name__ == '__main__':
    # get dir of currently executing script: 
    cwd = os.path.dirname(os.path.realpath(__file__)) 
    code_root, src_dir = os.path.split(cwd)
    cli_rel_path = os.path.join(src_dir, 'cli.jsonc')
    if not os.path.exists(cli_rel_path):
        # print('Warning: site-specific cli.jsonc not found, using template.')
        cli_rel_path = os.path.join(src_dir, 'cli_template.jsonc')

    main(code_root, cli_rel_path)
    exit(0)
