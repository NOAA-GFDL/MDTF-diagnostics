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

def process_frepp_stub():
    """Converts the frepp arguments to a Python dictionary.

    See `https://wiki.gfdl.noaa.gov/index.php/FRE_User_Documentation#Automated_creation_of_diagnostic_figures`_.

    Returns: :obj:`dict` of frepp parameters.
    """
    frepp_stub = str("""
        set in_data_dir     #pp directory containing files to be analyzed
        set descriptor      #experiment name
        set out_dir         #directory to write output files
        set WORKDIR         #working directory for script execution
        set frexml          #path to xml file
        set yr1             #start year of analysis
        set yr2             #ending year
        set make_variab_tar 1
        set test_mode       True
        set verbose         0
    """)
    return util.parse_frepp_stub(frepp_stub)

def argparse_wrapper():
    """Wraps command-line arguments to script.

    Returns: :obj:`dict` of command-line parameters.
    """
    cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
    code_root = os.path.realpath(os.path.join(cwd, '..')) # parent dir of that
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", action="count",
                        help="Increase output verbosity")
    # default paths set in config.yml/paths
    parser.add_argument('--CODE_ROOT', nargs='?', type=str, 
                        default=code_root,
                        help="Code installation directory.")
    parser.add_argument('--MODEL_DATA_ROOT', nargs='?', type=str, 
                        help="Parent directory containing results from different models.")
    parser.add_argument('--OBS_DATA_ROOT', nargs='?', type=str, 
                        help="Parent directory containing observational data used by individual PODs.")
    parser.add_argument('--WORKING_DIR', nargs='?', type=str, 
                        help="Working directory.")
    parser.add_argument('--OUTPUT_DIR', nargs='?', type=str, 
                        help="Directory to write output files. Defaults to working directory.")
    # defaults set in config.yml/settings
    parser.add_argument("--test_mode", action="store_const", const=True,
                        help="Set flag to do a dry run, disabling calls to PODs")
    parser.add_argument('--data_manager', nargs='?', type=str, 
                        help="Method to fetch model data. Currently supported options are {'Localfile'}.")
    parser.add_argument('--environment_manager', nargs='?', type=str, 
                        help="Method to manage POD runtime dependencies. Currently supported options are {'None', 'Conda'}.")
    # non-flag arguments                                        
    parser.add_argument('config_file', nargs='?', type=str, 
                        default=os.path.join(cwd, 'config.yml'),
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

if __name__ == '__main__':
    print "==== Starting "+__file__

    cmdline_args = argparse_wrapper()
    print cmdline_args
    frepp_args = process_frepp_stub()
    print frepp_args
    default_args = util.read_yaml(cmdline_args['config_file'])
    config = util.parse_mdtf_args(frepp_args, cmdline_args, default_args)
    
    verbose = config['settings']['verbose']
    PathManager(config['paths']) # initialize
    util.set_mdtf_env_vars(config, verbose)

    class_name = config['settings']['data_manager'].title()+'DataManager'
    try:
        DataMgr = getattr(data_manager, class_name)
    except:
        print "No class named {}.".format(class_name)
    class_name = config['settings']['environment_manager'].title()+'EnvironmentManager'
    try:
        EnvironmentMgr = getattr(environment_manager, class_name)
    except:
        print "No class named {}.".format(class_name)

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
        case.setUp(config)
        case.fetchData()
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