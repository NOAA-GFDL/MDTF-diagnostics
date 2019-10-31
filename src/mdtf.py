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
import util
import data_manager
import environment_manager
from shared_diagnostic import Diagnostic
try:
    import gfdl
except ImportError:
    pass  

def argparse_wrapper():
    """Wraps command-line arguments to script.

    Returns: :obj:`dict` of command-line parameters.
    """
    cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
    code_root = os.path.realpath(os.path.join(cwd, '..')) # parent dir of that
    parser = argparse.ArgumentParser(
        epilog="All command-line arguments override defaults set in src/config.yml."
    )
    parser.add_argument("-v", "--verbosity", 
        action="count",
        help="Increase output verbosity")
    parser.add_argument("--frepp", 
        action="store_true", # so default to False
        help="Set flag to take configuration info from env vars set by frepp.")
    # default paths set in config.yml/paths
    parser.add_argument('--CODE_ROOT', 
        nargs='?', default=code_root,
        help="Code installation directory.")
    parser.add_argument('--MODEL_DATA_ROOT', 
        nargs='?',
        help="Parent directory containing results from different models.")
    parser.add_argument('--OBS_DATA_ROOT', 
        nargs='?', 
        help="Parent directory containing observational data used by individual PODs.")
    parser.add_argument('--WORKING_DIR', 
        nargs='?',
        help="Working directory.")
    parser.add_argument('--OUTPUT_DIR', 
        nargs='?',
        help="Directory to write output files. Defaults to working directory.")
    # defaults set in config.yml/settings
    parser.add_argument("--test_mode", 
        action="store_true", # so default to False
        help="Set flag to do a dry run, disabling calls to PODs")
    parser.add_argument("--save_nc", 
        action="store_true", # so default to False
        help="Set flag to have PODs save netCDF files of processed data.")
    parser.add_argument('--data_manager', 
        nargs='?',
        help="Method to fetch model data. Currently supported options are {'Localfile'}.")
    parser.add_argument('--environment_manager', 
        nargs='?',
        help="Method to manage POD runtime dependencies. Currently supported options are {'None', 'Conda'}.")                                      
    # casename args, set by frepp
    parser.add_argument('--CASENAME', 
        nargs='?')
    parser.add_argument('--model', 
        nargs='?')
    parser.add_argument('--experiment', 
        nargs='?')
    parser.add_argument('--CASE_ROOT_DIR', 
        nargs='?')
    parser.add_argument('--FIRSTYR', 
        nargs='?', type=int)
    parser.add_argument('--LASTYR', 
        nargs='?', type=int)
    parser.add_argument("--ignore-component", 
        action="store_true", # so default to False
        help="Set flag to ignore model component passed by frepp and search entire /pp/ directory.")
    parser.add_argument("--component", 
        nargs='?')
    parser.add_argument("--data_freq", 
        nargs='?')   
    parser.add_argument("--chunk_freq", 
        nargs='?')       
    parser.add_argument('--config_file', 
        nargs='?', default=os.path.join(cwd, 'config.yml'),
        help="Configuration file.")
    args = parser.parse_args()
    
    d = args.__dict__
    if args.verbosity == None:
        d['verbose'] = 1
    else:
        d['verbose'] = args.verbosity + 1 # fix for case  verb = 0
    # remove entries that weren't set
    del_keys = [key for key in d if d[key] is None]
    for key in del_keys:
        del d[key]
    return d

def manual_dispatch(class_name):
    for mod in [data_manager, environment_manager, gfdl]:
        try:
            return getattr(mod, class_name)
        except:
            continue
    print "No class named {}.".format(class_name)
    raise Exception('no_class')

if __name__ == '__main__':
    print "==== Starting "+__file__

    cmdline_args = argparse_wrapper()
    print cmdline_args
    default_args = util.read_yaml(cmdline_args['config_file'])
    config = util.parse_mdtf_args(None, cmdline_args, default_args)
    print config #debug
    
    verbose = config['settings']['verbose']
    util.PathManager(config['paths']) # initialize
    util.set_mdtf_env_vars(config, verbose)
    DataMgr = manual_dispatch(
        config['settings']['data_manager'].title()+'DataManager'
    )
    EnvironmentMgr = manual_dispatch(
        config['settings']['environment_manager'].title()+'EnvironmentManager'
    )

    caselist = []
    # only run first case in list until dependence on env vars cleaned up
    for case_dict in config['case_list'][0:1]: 
        case = DataMgr(case_dict, config)
        for pod_name in case.pod_list:
            try:
                pod = Diagnostic(pod_name)
            except AssertionError as error:  
                print str(error)
            if verbose > 0: print "POD long name: ", pod.long_name
            case.pods.append(pod)
        case.setUp()
        case.fetch_data()
        caselist.append(case)

    for case in caselist:
        env = EnvironmentMgr(config)
        env.pods = case.pods # best way to do this?
        env.setUp()
        env.run()
        env.tearDown()

    for case in caselist:
        case.tearDown(config)

    print "Exiting normally from ",__file__
    exit()
