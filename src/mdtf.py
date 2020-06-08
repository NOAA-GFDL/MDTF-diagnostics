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

from __future__ import print_function
import sys
# do version check before importing other stuff
if sys.version_info[0] != 2 or sys.version_info[1] < 7:
    print(("ERROR: MDTF currently only supports python 2.7.*. Please check "
    "which version is on your $PATH (e.g. with `which python`.)"))
    print("Attempted to run with following python version:\n{}".format(sys.version))
    exit()
# passed; continue with imports
import os
import signal
import shutil
import cli
import util
import util_mdtf
import data_manager
import environment_manager
import shared_diagnostic
import netcdf_helper

class MDTFFramework(object):
    def __init__(self, code_root, defaults_rel_path):
        """Initial dispatch of CLI args: are we printing help info or running
        framework. 
        """
        self.code_root = code_root
        # delete temp files if we're killed
        signal.signal(signal.SIGTERM, self.cleanup_tempdirs)
        signal.signal(signal.SIGINT, self.cleanup_tempdirs)

        # poor man's subparser: argparse's subparser doesn't handle this
        # use case easily, so just dispatch on first argument
        if len(sys.argv) == 1 or \
            len(sys.argv) == 2 and sys.argv[1].lower().endswith('help'):
            # build CLI, print its help and exit
            cli_obj = cli.FrameworkCLIHandler(code_root, defaults_rel_path)
            cli_obj.parser.print_help()
            exit()
        elif sys.argv[1].lower() == 'info': 
            # "subparser" for command-line info
            cli.InfoCLIHandler(self.code_root, sys.argv[2:])
        else:
            # not printing help or info, setup CLI normally 
            # move into its own function so that child classes can customize
            # above options without having to rewrite below
            self._framework_init(code_root, defaults_rel_path)

    def cleanup_tempdirs(self, signum=None, frame=None):
        # delete temp files
        util.signal_logger(self.__class__.__name__, signum, frame)
        config = util_mdtf.ConfigManager()
        tmpdirs = util_mdtf.TempDirManager()
        if not config.config.get('keep_temp', False):
            tmpdirs.cleanup()

    def _framework_init(self, code_root, defaults_rel_path):
        # set up CLI and parse arguments
        # print('\tDEBUG: argv = {}'.format(sys.argv[1:]))
        cli_obj = cli.FrameworkCLIHandler(code_root, defaults_rel_path)
        self._cli_pre_parse_hook(cli_obj)
        cli_obj.parse_cli()
        self._cli_post_parse_hook(cli_obj)
        # load pod data
        pod_info_tuple = cli.load_pod_settings(code_root)
        # do nontrivial parsing
        config = util_mdtf.ConfigManager(cli_obj, pod_info_tuple)
        print(util.pretty_print_json(config.paths))
        self.parse_mdtf_args(cli_obj, config)
        # config should be read-only from here on
        self._post_parse_hook(cli_obj, config)
        self._print_config(cli_obj, config)

    def _cli_pre_parse_hook(self, cli_obj):
        # gives subclasses the ability to customize CLI handler before parsing
        # although most of the work done by parse_mdtf_args
        pass

    def _cli_post_parse_hook(self, cli_obj):
        # gives subclasses the ability to customize CLI handler after parsing
        # although most of the work done by parse_mdtf_args
        if cli_obj.config.get('dry_run', False):
            cli_obj.config['test_mode'] = True

    @staticmethod
    def _populate_from_cli(cli_obj, group_nm, target_d=None):
        if target_d is None:
            target_d = dict()
        for key, val in cli_obj.iteritems_cli(group_nm):
            if val: # assign nonempty items only
                target_d[key] = val
        return target_d

    def parse_mdtf_args(self, cli_obj, config):
        """Parse script options returned by the CLI. For greater customizability,
        most of the functionality is spun out into sub-methods.
        """
        self.parse_env_vars(cli_obj, config)
        self.parse_pod_list(cli_obj, config)
        self.parse_case_list(cli_obj, config)
        self.parse_paths(cli_obj, config)

    def parse_env_vars(self, cli_obj, config):
        # don't think PODs use global env vars?
        # self.envvars = self._populate_from_cli(cli_obj, 'PATHS', self.envvars)
        config.global_envvars['RGB'] = os.path.join(self.code_root,'src','rgb')

    def parse_pod_list(self, cli_obj, config):
        self.pod_list = []
        args = util.coerce_to_iter(config.config.pop('pods', []), set)
        if 'example' in args or 'examples' in args:
            self.pod_list = [pod for pod in config.pods.keys() \
                if pod.startswith('example')]
        elif 'all' in args:
            self.pod_list = [pod for pod in config.pods.keys() \
                if not pod.startswith('example')]
        else:
            # specify pods by realm
            realms = args.intersection(set(config.all_realms))
            args = args.difference(set(config.all_realms)) # remainder
            for key in config.pod_realms:
                if util.coerce_to_iter(key, set).issubset(realms):
                    self.pod_list.extend(config.pod_realms[key])
            # specify pods by name
            pods = args.intersection(set(config.pods.keys()))
            self.pod_list.extend(list(pods))
            for arg in args.difference(set(config.pods.keys())): # remainder:
                print("WARNING: Didn't recognize POD {}, ignoring".format(arg))
            # exclude examples
            self.pod_list = [pod for pod in self.pod_list \
                if not pod.startswith('example')]
        if not self.pod_list:
            print(("WARNING: no PODs selected to be run. Do `./mdtf info pods`"
            " for a list of available PODs, and check your -p/--pods argument."))
            print('Received --pods = {}'.format(list(args)))
            exit()

    def parse_case_list(self, cli_obj, config):
        case_list_in = util.coerce_to_iter(cli_obj.case_list)
        cli_d = self._populate_from_cli(cli_obj, 'MODEL')
        if 'CASE_ROOT_DIR' not in cli_d and cli_obj.config.get('root_dir', None): 
            # CASE_ROOT was set positionally
            cli_d['CASE_ROOT_DIR'] = cli_obj.config['root_dir']
        if not case_list_in:
            case_list_in = [cli_d]
        case_list = []
        for case_tup in enumerate(case_list_in):
            case_list.append(self.parse_case(case_tup, cli_d, cli_obj, config))
        self.case_list = [case for case in case_list if case is not None]
        if not self.case_list:
            print("ERROR: no valid entries in case_list. Please specify model run information.")
            print('Received:')
            print(util.pretty_print_json(case_list_in))
            exit(1)

    def parse_case(self, case_tup, cli_d, cli_obj, config):
        n, d = case_tup
        if 'CASE_ROOT_DIR' not in d and 'root_dir' in d:
            d['CASE_ROOT_DIR'] = d.pop('root_dir')
        case_convention = d.get('convention', '')
        d.update(cli_d)
        if case_convention:
            d['convention'] = case_convention

        if not ('CASENAME' in d or ('model' in d and 'experiment' in d)):
            print(("WARNING: Need to specify either CASENAME or model/experiment "
                "in caselist entry {}, skipping.").format(n+1))
            return None
        _ = d.setdefault('model', d.get('convention', ''))
        _ = d.setdefault('experiment', '')
        _ = d.setdefault('CASENAME', '{}_{}'.format(d['model'], d['experiment']))

        for field in ['FIRSTYR', 'LASTYR', 'convention']:
            if not d.get(field, None):
                print(("WARNING: No value set for {} in caselist entry {}, "
                    "skipping.").format(field, n+1))
                return None
        # if pods set from CLI, overwrite pods in case list
        d['pod_list'] = self.set_case_pod_list(d, cli_obj, config)
        return d

    def set_case_pod_list(self, case, cli_obj, config):
        # if pods set from CLI, overwrite pods in case list
        # already finalized self.pod-list by the time we get here
        if not cli_obj.is_default['pods'] or not case.get('pod_list', None):
            return self.pod_list
        else:
            return case['pod_list']

    def parse_paths(self, cli_obj, config):
        config.paths.parse(cli_obj.config, cli_obj.custom_types.get('path', []))

    def _post_parse_hook(self, cli_obj, config):
        # init other services
        _ = util_mdtf.TempDirManager()
        _ = util_mdtf.VariableTranslator()
        self.verify_paths(config)

    def verify_paths(self, config):
        # clean out WORKING_DIR if we're not keeping temp files
        if os.path.exists(config.paths.WORKING_DIR) and not \
            (config.config.get('keep_temp', False) \
            or config.paths.WORKING_DIR == config.paths.OUTPUT_DIR):
            shutil.rmtree(config.paths.WORKING_DIR)
        util_mdtf.check_required_dirs(
            already_exist = [
                config.paths.CODE_ROOT, config.paths.OBS_DATA_ROOT
            ], 
            create_if_nec = [
                config.paths.MODEL_DATA_ROOT, 
                config.paths.WORKING_DIR, 
                config.paths.OUTPUT_DIR
        ])

    def _print_config(self, cli_obj, config):
        # make config nested dict for backwards compatibility
        # this is all temporary
        d = dict()
        for n, case in enumerate(self.case_list):
            key = 'case_list({})'.format(n)
            d[key] = case
        d['pod_list'] = self.pod_list
        d['paths'] = config.paths
        d['paths'].pop('_unittest_flag', None)
        d['settings'] = dict()
        settings_gps = set(cli_obj.parser_groups.keys()).difference(
            set(['parser','PATHS','MODEL','DIAGNOSTICS'])
        )
        for group in settings_gps:
            d['settings'] = self._populate_from_cli(cli_obj, group, d['settings'])
        d['settings'] = {k:v for k,v in d['settings'].iteritems() \
            if k not in d['paths']}
        d['envvars'] = config.global_envvars
        print('DEBUG: SETTINGS:')
        print(util.pretty_print_json(d))

    _dispatch_search = [
        data_manager, environment_manager, shared_diagnostic, netcdf_helper
    ]
    def manual_dispatch(self, config):
        def _dispatch(setting, class_suffix):
            class_prefix = config.config.get(setting, '')
            class_prefix = util.coerce_from_iter(class_prefix)
            # drop '_' and title-case class name
            class_prefix = ''.join(class_prefix.split('_')).title()
            for mod in self._dispatch_search:
                try:
                    return getattr(mod, class_prefix+class_suffix)
                except:
                    continue
            print("No class named {}.".format(class_prefix+class_suffix))
            raise Exception('no_class')

        self.DataManager = _dispatch('data_manager', 'DataManager')
        self.EnvironmentManager = _dispatch('environment_manager', 'EnvironmentManager')
        self.Diagnostic = _dispatch('diagnostic', 'Diagnostic')
        self.NetCDFHelper = _dispatch('netcdf_helper', 'NetcdfHelper')

    def main_loop(self):
        config = util_mdtf.ConfigManager()
        self.manual_dispatch(config)
        caselist = []
        # only run first case in list until dependence on env vars cleaned up
        for case_dict in self.case_list[0:1]: 
            case = self.DataManager(case_dict)
            for pod_name in case.pod_list:
                try:
                    pod = self.Diagnostic(pod_name)
                except AssertionError as error:  
                    print(str(error))
                case.pods.append(pod)
            case.setUp()
            case.fetch_data()
            caselist.append(case)

        for case in caselist:
            env_mgr = self.EnvironmentManager(config)
            env_mgr.pods = case.pods # best way to do this?
            # nc_helper = self.NetCDFHelper()

            # case.preprocess_local_data(
            #     netcdf_mixin=nc_helper, environment_manager=env_mgr
            # )
            env_mgr.setUp()
            env_mgr.run()
            env_mgr.tearDown()

        for case in caselist:
            case.tearDown()
        self.cleanup_tempdirs()


if __name__ == '__main__':
    # get dir of currently executing script: 
    cwd = os.path.dirname(os.path.realpath(__file__)) 
    code_root, src_dir = os.path.split(cwd)
    defaults_rel_path = os.path.join(src_dir, 'cli.jsonc')
    if not os.path.exists(defaults_rel_path):
        # print('Warning: site-specific cli.jsonc not found, using template.')
        defaults_rel_path = os.path.join(src_dir, 'cli_template.jsonc')
    mdtf = MDTFFramework(code_root, defaults_rel_path)
    print("\n======= Starting {}".format(__file__))
    mdtf.main_loop()
    print("Exiting normally from {}".format(__file__))
