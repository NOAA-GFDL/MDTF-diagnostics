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

print "==== Starting "+__file__

import os
import sys
import argparse
import glob
import shutil
import timeit
if os.name == 'posix' and sys.version_info[0] < 3:
  try:
    import subprocess32 as subprocess
  except (ImportError, ModuleNotFoundError):
    import subprocess
else:
    import subprocess
import yaml
import src as util
from src.util import setenv

cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbosity", action="count",
                    help="Increase output verbosity")
parser.add_argument("--test_mode", action="store_const", const=True,
                    help="Set flag to not call PODs, just say what would be called")
# default paths set in config.yml/paths
parser.add_argument('--DIAG_HOME', nargs='?', type=str, 
                    default=cwd,
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

# ======================================================================
# Input settings from namelist file (name = argument to this script, default DIAG_HOME/namelist)
# to set CASENAME,model,FIRSTYR,LASTYR, POD list and environment variables 

try:
   config = util.read_mdtf_config_file(args.config_file, verbose=verbose)
except Exception as error:
   print error
   exit()
util.set_mdtf_env_vars(args, config, verbose=verbose)
verbose = config['envvars']['verbose']
util.check_required_dirs(
   already_exist =["DIAG_HOME","MODEL_ROOT_DIR","OBS_ROOT_DIR","RGB"], 
   create_if_nec = ["WORKING_DIR","OUTPUT_DIR"], 
   verbose=verbose)

try:
   model_varnames = util.read_model_varnames(verbose=verbose)
except Exception as error:
   print error
   exit()

os.system("date")

errstr = "ERROR "+__file__+" : "

#### Future loop over models in config['case_list'] starts here
# loop over PODs by model, since starting a new model may involve 
# time-consuming gcp'ing of remote data 

# ======================================================================
# Default script settings over-ridden by namelist: VAR var-name varvalue
# It is recommended to make all changes in the namelist
#

# ======================================================================
# DIRECTORIES: set up locations
# ======================================================================

# inputdata contains model/$casename, obs_data/$package/*  #drb change?
# output goes into wkdir & variab_dir (diagnostics should generate .nc files & .ps files in subdirectories herein)

# ======================================================================
# set variable names based on model
# ======================================================================

util.set_model_env_vars(os.environ["model"], model_varnames)



# ======================================================================
# Check for programs that must exist (eg ncl)
# To Do: make a dictionary 'program name':'ENV VARNAME' and loop like dir_list below
# ======================================================================

# ncl_err = os.system("which ncl")
# if ncl_err == 0:
#    setenv("NCL",subprocess.check_output("which ncl", shell=True),config['envvars'],overwrite=False,verbose=verbose)
#    print("using ncl "+os.environ["NCL"])
# else:
#    print(errstr+ ": ncl not found")
# # workaround for conda-installed ncl on csh: ncl activation script doesn't set environment variables properly
# if not ("NCARG_ROOT" in os.environ) and ("CONDA_PREFIX" in os.environ):
#    setenv("NCARG_ROOT",os.environ['CONDA_PREFIX'],config['envvars'],verbose=verbose)

# Check if any required namelist/envvars are missing  
#util.check_required_envvar(verbose,["CASENAME","model","FIRSTYR","LASTYR","NCARG_ROOT"])
#util.check_required_dirs( already_exist =["NCARG_ROOT"], [], verbose=verbose)





# ======================================================================
# Check directories that must already exist
# ======================================================================



for pod in pod_configs:
   # shouldn't need to re-set env vars, but used by 
   # convective_transition_diag to set filename info 
   util.set_pod_env_vars(pod['settings'], config, verbose=verbose)

   pod_name = pod['settings']['pod_name']
   util.make_pod_html(pod_name, pod['settings']['description'])
   util.convert_pod_figures(pod_name)
   util.cleanup_pod_files(pod_name)







print "Exiting normally from ",__file__
exit()
