#! /usr/bin/env python

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
from data_manager import LocalFileData as DataMgr
from environment_manager import CondaEnvironmentManager as EnvironmentMgr
from shared_diagnostic import Diagnostic

cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
code_root = os.path.realpath(os.path.join(cwd, '..')) # parent dir of that
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbosity", action="count",
                    help="Increase output verbosity")
parser.add_argument("--test_mode", action="store_const", const=True,
                    help="Set flag to not call PODs, just say what would be called")
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
parser.add_argument('config_file', nargs='?', type=str, 
                    default=os.path.join(cwd, 'config.yml'),
                    help="Configuration file.")
args = parser.parse_args()
if args.verbosity == None:
    verbose = 1
else:
    verbose = args.verbosity + 1 # fix for case  verb = 0

print "==== Starting "+__file__
config = util.read_yaml(args.config_file)
config = util.parse_mdtf_args(args, config)
util.set_mdtf_env_vars(config, verbose)

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