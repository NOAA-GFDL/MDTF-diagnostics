#!/usr/bin/env python

# ======================================================================
# NOAA Model Diagnotics Task Force (MDTF) Diagnostic Driver
#
# March 2019
# Dani Coleman, NCAR
# Chih-Chieh (Jack) Chen, NCAR, 
# Yi-Hung Kuo, UCLA
#
# ======================================================================
# Usage
#
# USAGE: python mdtf.py input_file (default=namelist)
# The input file sets all model case/dates and which modules to run
# This file (mdtf.py) should NOT be modified
#
# Please see Getting Started [link] and Developer's Walk-Through
# for full description of how to run
# ======================================================================
# What's Included
#
# The input file (namelist) provided in the distribution will run
# the following diagnostic modules (PODs) by default:
#    Convective Transition Diagnostics   from J. David Neelin (UCLA)
#    MJO Teleconnections                 from Eric Maloney (CSU)
#    Extratropical Variance (EOF 500hPa) from CESM/AMWG (NCAR)
#    Wavenumber-Frequency Spectra        from CESM/AMWG (NCAR)
#    MJO Spectra and Phasing             from CESM/AMWG (NCAR)
#
# In addition, the following package is provided in full but does not run
# by default because of higher memory requirements
#    Diurnal Cycle of Precipitation      from Rich Neale (NCAR)
#
# The following modules are under development. Future releases will be
# available on the  MDTF main page
# http://www.cesm.ucar.edu/working_groups/Atmosphere/mdtf-diagnostics-package/index.html
#    MJO Propagation and Amplitude        from Xianan Jiang, UCLA
#    ENSO Moist Static Energy budget      from Hariharasubramanian Annamalai, U. Hawaii
#    Warm Rain Microphysics               from Kentaroh Suzuki (AORI, U. Tokyo
#    AMOC 3D structure                    from Xiaobiao Xu (FSU/COAPS)
#
# The MDTF code package and the participating PODs are distributed under
# the LGPLv3 license (see LICENSE.txt).
# ======================================================================
# Requirements
#
# As well as Ncar Command Language (NCL),
# this release uses the following Python modules: 
#     os, glob, json, dataset, numpy, scipy, matplotlib, 
#     networkx, warnings, numba, netcdf4
# ======================================================================

import os
import sys
import argparse
from ConfigParser import _Chainmap as ChainMap # in collections in py3
import util
import data_manager
import environment_manager
from shared_diagnostic import Diagnostic  

class MDTFFramework(object):
    def __init__(self):
        # get dir of currently executing script: 
        cwd = os.path.dirname(os.path.realpath(__file__)) 
        self.code_root = os.path.dirname(cwd) # parent dir of that

        self.parser = argparse.ArgumentParser(
            epilog="""
                All command-line arguments override defaults set in 
                src/mdtf_settings.json.
            """
        )
        self.argparse_setup()
        cmdline_args = self.argparse_parse()
        print cmdline_args, '\n'
        default_args = util.read_json(cmdline_args['config_file'])
        self.config = self.parse_mdtf_args(cmdline_args, default_args)
        print 'SETTINGS:\n', util.pretty_print_json(self.config) #debug

        util.PathManager(self.config['paths']) # initialize
        self._post_config_init() # hook to allow inserting other commands
        
    def _post_config_init(self):
        self.set_mdtf_env_vars()
        self.DataManager = self.manual_dispatch(
            self.config['settings']['data_manager'], 'DataManager'
        )
        self.EnvironmentManager = self.manual_dispatch(
            self.config['settings']['environment_manager'], 'EnvironmentManager'
        )
        self.Diagnostic = Diagnostic

    def argparse_setup(self):
        """Wraps command-line arguments to script.
        """
        self.parser.add_argument("-v", "--verbose", 
            action="count", default = 1,
            help="Increase output verbosity")
        # default paths set in mdtf_settings.json/paths
        self.parser.add_argument('--CODE_ROOT', 
            nargs='?', default=self.code_root,
            help="Code installation directory.")
        self.parser.add_argument('--MODEL_DATA_ROOT', 
            nargs='?',
            help="Parent directory containing results from different models.")
        self.parser.add_argument('--OBS_DATA_ROOT', 
            nargs='?', 
            help="Parent directory containing observational data used by individual PODs.")
        self.parser.add_argument('--WORKING_DIR', 
            nargs='?',
            help="Working directory.")
        self.parser.add_argument('--OUTPUT_DIR', 
            nargs='?',
            help="Directory to write output files. Defaults to working directory.")
        # defaults set in mdtf_settings.json/settings
        self.parser.add_argument("--test_mode", 
            action="store_true", # so default to False
            help="Set flag to fetch data but skip calls to PODs")
        self.parser.add_argument("--dry_run", 
            action="store_true", # so default to False
            help="Set flag to do a dry run, disabling data fetching and calls to PODs")
        self.parser.add_argument("--save_nc", 
            action="store_true", # so default to False
            help="Set flag to have PODs save netCDF files of processed data.")
        self.parser.add_argument('--data_manager', 
            nargs='?',
            help="Method to fetch model data. Currently supported options are {'Localfile'}.")
        self.parser.add_argument('--environment_manager', 
            nargs='?',
            help="Method to manage POD runtime dependencies. Currently supported options are {'None', 'Conda'}.")                                      
        # casename args, set by frepp
        self.parser.add_argument('--CASENAME', 
            nargs='?')
        self.parser.add_argument('--model', 
            nargs='?')
        self.parser.add_argument('--experiment', 
            nargs='?')
        self.parser.add_argument('--CASE_ROOT_DIR', 
            nargs='?')
        self.parser.add_argument('--FIRSTYR', 
            nargs='?', type=int)
        self.parser.add_argument('--LASTYR', 
            nargs='?', type=int)
        self.parser.add_argument("--component", 
            nargs='?')
        self.parser.add_argument("--data_freq", 
            nargs='?')   
        self.parser.add_argument("--chunk_freq", 
            nargs='?')       
        self.parser.add_argument('--config_file', 
            nargs='?', default=os.path.join(self.code_root, 'src', 'mdtf_settings.json'),
            help="Configuration file.")

    def argparse_parse(self):
        d = self.parser.parse_args().__dict__
        # remove entries that weren't set
        return {key: val for key, val in d.iteritems() if val is not None}

    @staticmethod
    def caselist_from_args(args):
        d = {}
        for k in ['CASENAME', 'FIRSTYR', 'LASTYR', 'root_dir', 'component', 
            'chunk_freq', 'data_freq', 'model', 'experiment', 'variable_convention']:
            if k in args:
                d[k] = args[k]
        if 'model' not in d:
            d['model'] = 'CMIP_GFDL'
        if 'variable_convention' not in d:
            d['variable_convention'] = 'CMIP_GFDL'
        if 'CASENAME' not in d:
            d['CASENAME'] = '{}_{}'.format(d['model'], d['experiment'])
        if 'root_dir' not in d and 'CASE_ROOT_DIR' in args:
            d['root_dir'] = args['CASE_ROOT_DIR']
        return [d]

    @classmethod
    def parse_mdtf_args(cls, user_args_list, default_args, rel_paths_root=''):
        """Parse script options.

        We provide three ways to configure the script. In order of precendence,
        they are:

        1. Parameter substitution via GFDL's internal `frepp` utility; see
        `https://wiki.gfdl.noaa.gov/index.php/FRE_User_Documentation`_.

        2. Through command-line arguments.

        3. Through default values set in a YAML configuration file, by default
        in src/config.yml.

        This function applies the precendence and returns a single dict of the
        actual configuration.

        Args:

        Returns: :obj:`dict` of configuration settings.
        """
        if isinstance(user_args_list, dict):
            user_args = user_args_list
        elif isinstance(user_args_list, list):
            user_args = ChainMap(*user_args_list)
        else:
            user_args = dict()

        # overwrite defaults with command-line args.
        for section in ['paths', 'settings']:
            for key in default_args[section]:
                if key in user_args:
                    default_args[section][key] = user_args[key]
        if ('model' in user_args and 'experiment' in user_args) or \
            'CASENAME' in user_args:
            # also set up caselist with frepp data
            default_args['case_list'] = cls.caselist_from_args(user_args)

        if 'CODE_ROOT' in user_args:
            # only let this be overridden if we're in a unit test
            rel_paths_root = user_args['CODE_ROOT']
        # convert relative to absolute paths
        for key, val in default_args['paths'].items():
            default_args['paths'][key] = util.resolve_path(val, rel_paths_root)

        if util.get_from_config('dry_run', default_args, default=False):
            default_args['settings']['test_mode'] = True

        return default_args

    def set_mdtf_env_vars(self):
        # pylint: disable=maybe-no-member
        paths = util.PathManager()
        util.check_required_dirs(
            already_exist = [paths.CODE_ROOT, paths.OBS_DATA_ROOT], 
            create_if_nec = [paths.MODEL_DATA_ROOT, paths.WORKING_DIR, paths.OUTPUT_DIR], 
            )
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
        print "No class named {}.".format(class_prefix+class_suffix)
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
                print "\tDEBUG: will run {}".format(p)
            case = self.DataManager(case_dict, self.config)
            for pod_name in case.pod_list:
                try:
                    pod = self.Diagnostic(pod_name)
                except AssertionError as error:  
                    print str(error)
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


if __name__ == '__main__':
    print "\n======= Starting "+__file__
    mdtf = MDTFFramework()
    mdtf.main_loop()
    print "Exiting normally from ",__file__