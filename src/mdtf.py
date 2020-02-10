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
import cli
import util
import data_manager
import environment_manager
from shared_diagnostic import Diagnostic  

class MDTFFramework(object):
    def __init__(self, code_root, defaults_rel_path):
        # set up CLI, parse settings
        self.code_root = code_root
        self.config = dict()
        config = cli.ConfigManager(os.path.join(code_root, defaults_rel_path))
        config.parse_cli()
        self.parse_mdtf_args()
        print('DEBUG: SETTINGS:\n', util.pretty_print_json(self.config))
        self._post_config_init()
        
    def _post_config_init(self):
        util.PathManager(self.config['paths']) # initialize
        self.set_mdtf_env_vars()
        self.DataManager = self.manual_dispatch(
            self.config['settings']['data_manager'], 'DataManager'
        )
        self.EnvironmentManager = self.manual_dispatch(
            self.config['settings']['environment_manager'], 'EnvironmentManager'
        )
        self.Diagnostic = Diagnostic

    def caselist_from_args(self, config_obj):
        d = dict()
        d2 = config_obj.config
        self._populate_dict(config_obj, 'MODEL', d)
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

    @staticmethod
    def _populate_dict(config_obj, group_nm, d):
        # hacky temp code, for backwards compatibility
        for action in config_obj.parser_args_from_group[group_nm]:
            key = action.dest
            d[key] = config_obj.config[key]

    def parse_mdtf_args(self):
        """Parse script options.
        """
        config = cli.ConfigManager()

        self.config['pod_list'] = config.pod_list
        if config.config.get('model', None) or config.config.get('experiment', None) \
            or config.config.get('CASENAME', None):
            self.config['case_list'] = self.caselist_from_args(config)
        else:
            self.config['case_list'] = config.case_list
        for i in range(len(self.config['case_list'])):
            d = self.config['case_list'][i]
            # remove empty entries
            d = {k:v for k,v in d.iteritems() if v}
            if not d.get('CASE_ROOT_DIR', None) and d.get('root_dir', None):
                d['CASE_ROOT_DIR'] = d['root_dir']
            elif not d.get('root_dir', None) and d.get('CASE_ROOT_DIR', None):
                d['root_dir'] = d['CASE_ROOT_DIR']
        
        self.config['paths'] = dict()
        self._populate_dict(config, 'PATHS', self.config['paths'])
        self.config['settings'] = dict()
        settings_gps = set(config.parser_groups.keys()).difference(
            set(['parser','PATHS','MODEL'])
        )
        for group in settings_gps:
            self._populate_dict(config, group, self.config['settings'])

        # only let this be overridden if we're in a unit test
        rel_paths_root = config.config.get('CODE_ROOT', None)
        if not rel_paths_root or rel_paths_root == '.':
            rel_paths_root = self.code_root
        # convert relative to absolute paths
        for key, val in self.config['paths'].iteritems():
            # print('DEBUG: {},{}'.format(key,val))
            self.config['paths'][key] = util.resolve_path(
                util.coerce_from_iter(val), rel_paths_root
            )
        if config.config.get('dry_run', False):
            self.config['settings']['test_mode'] = True

    def set_mdtf_env_vars(self):
        # pylint: disable=maybe-no-member
        paths = util.PathManager()
        util.check_required_dirs(
            already_exist = [paths.CODE_ROOT, paths.OBS_DATA_ROOT], 
            create_if_nec = [
                paths.MODEL_DATA_ROOT, paths.WORKING_DIR, paths.OUTPUT_DIR
        ])
        self.config["envvars"] = self.config['settings'].copy()
        self.config["envvars"].update(self.config['paths'])
        # following are redundant but used by PODs
        self.config["envvars"]["RGB"] = os.path.join(paths.CODE_ROOT,'src','rgb')

    _dispatch_search = [data_manager, environment_manager]

    def manual_dispatch(self, class_prefix, class_suffix):
        # drop '_' and title-case class name
        class_prefix = ''.join(class_prefix.split('_')).title()
        for mod in self._dispatch_search:
            try:
                return getattr(mod, class_prefix+class_suffix)
            except:
                continue
        print("No class named {}.".format(class_prefix+class_suffix))
        raise Exception('no_class')  

    def set_case_pod_list(self, case_dict):
        if 'pod_list' in case_dict:
            # run a set of PODs specific to this model
            pod_list = case_dict['pod_list']
        elif 'pod_list' in self.config:
            # use global list of PODs  
            pod_list =  self.config['pod_list'] 
        else:
            pod_list = [] # should raise warning
        return pod_list

    def main_loop(self):
        caselist = []
        # only run first case in list until dependence on env vars cleaned up
        for case_dict in self.config['case_list'][0:1]: 
            case_dict['pod_list'] = self.set_case_pod_list(case_dict)
            for p in case_dict['pod_list']:
                print("\tDEBUG: will run {}".format(p))
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
    print("\n======= Starting "+__file__)
    mdtf.main_loop()
    print("Exiting normally from ",__file__)