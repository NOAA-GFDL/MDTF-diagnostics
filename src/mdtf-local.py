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
#


import os
import sys
import argparse
import util
from shared_runner import DiagnosticRunner


cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbosity", action="count",
                    help="Increase output verbosity")
parser.add_argument("--test_mode", action="store_const", const=True,
                    help="Set flag to not call PODs, just say what would be called")
# default paths set in config.yml/paths
parser.add_argument('--DIAG_HOME', nargs='?', type=str, 
                    default=os.path.realpath(os.path.join(cwd, '..')),
                    help="Code installation directory.")
parser.add_argument('--MODEL_ROOT_DIR', nargs='?', type=str, 
                    help="Parent directory containing results from different models.")
parser.add_argument('--OBS_ROOT_DIR', nargs='?', type=str, 
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
try:
    config = util.read_yaml(args.config_file)
except Exception as error:
    print error
    exit()

runner = DiagnosticRunner(args, config)
runner.setUp(config, config['case_list'])
runner.run(config)
runner.tearDown(config)

print "Exiting normally from ",__file__
exit()