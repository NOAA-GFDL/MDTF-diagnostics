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
import os
import sys
import signal
import cli
import util
import util_mdtf
import data_manager
import environment_manager
import shared_diagnostic

class MDTFFramework(object):
    def __init__(self, code_root, defaults_rel_path):
        """Initial dispatch of CLI args: are we printing help info or running
        framework. 
        """
        self.code_root = code_root
        # tell PathManager to delete temp files if we're killed
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
            self._real_init_hook(code_root, defaults_rel_path)

    def cleanup_tempdirs(self, signum=None, frame=None):
        # tell PathManager to delete temp files if we're killed
        # This is not called during normal operation and exit.
        if signum:
            # lookup signal name from number; https://stackoverflow.com/a/2549950
            sig_lookup = {
                k:v for v, k in reversed(sorted(signal.__dict__.items())) \
                    if v.startswith('SIG') and not v.startswith('SIG_')
            }
            print("\tDEBUG: {} caught signal {} ({})".format(
                self.__class__.__name__, sig_lookup.get(signum, 'UNKNOWN'), signum
            ))
            print("\tDEBUG: {}".format(frame))
        if not self.config['settings']['keep_temp']:
            paths = util_mdtf.PathManager()
            paths.cleanup()

    def _real_init_hook(self, code_root, defaults_rel_path):
        # set up CLI and parse arguments
        print('\tDEBUG: argv = {}'.format(sys.argv[1:]))
        cli_obj = cli.FrameworkCLIHandler(code_root, defaults_rel_path)
        self._cli_pre_parse_hook(cli_obj)
        cli_obj.parse_cli()
        # load pod info
        pod_info_tuple = cli.load_pod_settings(self.code_root)
        self.all_pods = pod_info_tuple.pod_list
        self.pods = pod_info_tuple.pod_data
        self.all_realms = pod_info_tuple.realm_list
        self.pod_realms = pod_info_tuple.realm_data
        # do nontrivial parsing
        self.dry_run = cli_obj.config.get('dry_run', False)
        self.timeout = cli_obj.config.get('timeout', False)
        self.parse_mdtf_args(cli_obj)
        # use final info to initialize ConfigManager
        print('DEBUG: SETTINGS:\n', util.pretty_print_json(self.config))
        exit()

    def _cli_pre_parse_hook(self, cli_obj):
        # gives subclasses the ability to customize CLI handler before parsing
        # although most of the work done by parse_mdtf_args
        pass

    def parse_mdtf_args(self, cli_obj):
        """Parse script options returned by the CLI. For greater customizability,
        most of the functionality is spun out into sub-methods.
        """
        self.postparse_cli(cli_obj)
        self.parse_env_vars(cli_obj)
        self.parse_pod_list(cli_obj)
        self.parse_case_list(cli_obj)
        self.parse_paths(cli_obj)
        
        # make config nested dict for backwards compatibility
        # this is all temporary
        self.config = dict()
        self.config['pod_list'] = self.pod_list
        self.config['case_list'] = self.case_list
        self.config['paths'] = self.paths
        util_mdtf.PathManager(self.config['paths']) # initialize
        self.config['settings'] = dict()
        settings_gps = set(cli_obj.parser_groups.keys()).difference(
            set(['parser','PATHS','MODEL','DIAGNOSTICS'])
        )
        for group in settings_gps:
            self._populate_dict(cli_obj, group, self.config['settings'])
        self.config['envvars'] = self.config['settings'].copy()
        self.config['envvars'].update(self.config['paths'])
        self.config['envvars']['RGB'] = os.path.join(self.code_root,'src','rgb')

    def postparse_cli(self, cli_obj):
        # stuff too cumbersome to do within cli.py 
        if self.dry_run:
            cli_obj.config['test_mode'] = True

    def parse_pod_list(self, cli_obj):
        self.pod_list = []
        args = util.coerce_to_iter(cli_obj.config.pop('pods', []), set)
        if 'all' in args:
            self.pod_list = self.all_pods
        else:
            # specify pods by realm
            realms = args.intersection(set(self.all_realms))
            args = args.difference(set(self.all_realms)) # remainder
            for key in self.pod_realms:
                if util.coerce_to_iter(key, set).issubset(realms):
                    self.pod_list.extend(self.pod_realms[key])
            # specify pods by name
            pods = args.intersection(set(self.all_pods))
            self.pod_list.extend(list(pods))
            for arg in args.difference(set(self.all_pods)): # remainder:
                print("WARNING: Didn't recognize POD {}, ignoring".format(arg))

    def parse_case_list(self, cli_obj):
        d = cli_obj.config # abbreviate
        self.case_list = []
        if d.get('model', None) or d.get('experiment', None) \
            or d.get('CASENAME', None):
            self.case_list = self.caselist_from_args(cli_obj)
        else:
            self.case_list = util.coerce_to_iter(cli_obj.case_list)
        for i in range(len(self.case_list)):
            d2 = self.case_list[i]
            # remove empty entries
            d2 = {k:v for k,v in d2.iteritems() if v}
            if not d2.get('CASE_ROOT_DIR', None) and d2.get('root_dir', None):
                d2['CASE_ROOT_DIR'] = d2['root_dir']
            elif not d2.get('root_dir', None) and d2.get('CASE_ROOT_DIR', None):
                d2['root_dir'] = d2['CASE_ROOT_DIR']

    def caselist_from_args(self, cli_obj):
        d = dict()
        d2 = cli_obj.config # abbreviate
        self._populate_dict(cli_obj, 'MODEL', d)
        # remove empty entries first
        d = {k:v for k,v in d.iteritems() if v}
        if 'model' not in d:
            d['model'] = 'CMIP'
        if 'experiment' not in d:
            d['experiment'] = ''
        if 'variable_convention' not in d:
            d['variable_convention'] = 'CMIP'
        if 'CASENAME' not in d:
            d['CASENAME'] = '{}_{}'.format(d['model'], d['experiment'])
        if d2.get('root_dir', None):
            # overwrite flag if both are set
            d['CASE_ROOT_DIR'] = d2['root_dir']
            d['root_dir'] = d2['root_dir']
        elif d.get('CASE_ROOT_DIR', None):
            d['root_dir'] = d['CASE_ROOT_DIR']
        else:
            print('ERROR: need to sepcify root directory of model data.')
            exit()
        return [d]

    def parse_env_vars(self, cli_obj):
        self.envvars = dict()
        self.envvars = cli_obj.config.copy()

    def _mdtf_resolve_path(self, path, cli_obj):
        # wrapper to resolve relative paths and substitute env vars
        # only let CODE_ROOT be overridden if we're in a unit test
        rel_paths_root = cli_obj.config.get('CODE_ROOT', None)
        if not rel_paths_root or rel_paths_root == '.':
            rel_paths_root = self.code_root
        return util.resolve_path(util.coerce_from_iter(path), rel_paths_root)

    def parse_paths(self, cli_obj):
        self.paths = dict()
        for key, val in cli_obj.iteritems_cli('PATHS'):
            val2 = self._mdtf_resolve_path(val, cli_obj)
            # print('\tDEBUG: {},{},{}'.format(key, val, val2))
            self.paths[key] = val2
        util_mdtf.check_required_dirs(
            already_exist = [
                self.paths['CODE_ROOT'], self.paths['OBS_DATA_ROOT']
            ], 
            create_if_nec = [
                self.paths['MODEL_DATA_ROOT'], 
                self.paths['WORKING_DIR'], 
                self.paths['OUTPUT_DIR']
        ])

    @staticmethod
    def _populate_dict(cli_obj, group_nm, d):
        # hacky temp code, for backwards compatibility
        for key, val in cli_obj.iteritems_cli(group_nm):
            d[key] = val

    _dispatch_search = [data_manager, environment_manager, shared_diagnostic]
    def manual_dispatch(self):
        def _dispatch(setting, class_suffix):
            class_prefix = self.config['settings'].get(setting, '')
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

    def set_case_pod_list(self, case_dict):
        if not case_dict.get('pod_list', None):
            return self.pod_list # use global list of PODs 
        else:
            return case_dict['pod_list']

    def main_loop(self):
        self.manual_dispatch()
        caselist = []
        # only run first case in list until dependence on env vars cleaned up
        for case_dict in self.config['case_list'][0:1]: 
            case_dict['pod_list'] = self.set_case_pod_list(case_dict)
            case = self.DataManager(case_dict, self.config)
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
            env = self.EnvironmentManager(self.config)
            env.pods = case.pods # best way to do this?
            env.setUp()
            env.run()
            env.tearDown()

        for case in caselist:
            case.tearDown(self.config)
        self.cleanup_tempdirs()

def version_check():
    v = sys.version_info
    if v.major != 2 or v.minor < 7:
        print("""ERROR: attempted to run with python {}.{}.{}. The MDTF framework
        currently only supports python 2.7.*. Please check which version of python
        is on your $PATH (e.g. with `which python`.)""".format(
            v.major, v.minor, v.micro
        ))
        exit()

if __name__ == '__main__':
    version_check()
    # get dir of currently executing script: 
    cwd = os.path.dirname(os.path.realpath(__file__)) 
    code_root, src_dir = os.path.split(cwd)
    mdtf = MDTFFramework(code_root, os.path.join(src_dir, 'defaults.json'))
    print("\n======= Starting {}".format(__file__))
    mdtf.main_loop()
    print("Exiting normally from {}".format(__file__))
