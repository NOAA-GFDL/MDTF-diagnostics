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
sys.path.insert(0,'var_code/util/')
import read_files
import write_files 
from util import setenv, check_required_dirs


os.system("date")


errstr = "ERROR "+__file__+" : "

# ======================================================================
# Default script settings over-ridden by namelist: VAR var-name varvalue
# It is recommended to make all changes in the namelist
#
verbose = 1                           # 0 = sparse, 1 = normal, 2 = a lot, 3 = every possible thing
test_mode = False                     # False = run the packages, True = don't make the calls, just say what would be called

# dictionary of all the environment variables set in this script, to be archived in variab_dir/namelist file
envvars = {}   

# ======================================================================
# Check for programs that must exist (eg ncl)
# To Do: make a dictionary 'program name':'ENV VARNAME' and loop like dir_list below
# ======================================================================

ncl_err = os.system("which ncl")
if ncl_err == 0:
   setenv("NCL",subprocess.check_output("which ncl", shell=True),envvars,overwrite=False,verbose=verbose)
   print("using ncl "+os.environ["NCL"])
else:
   print(errstr+ ": ncl not found")
# workaround for conda-installed ncl on csh: ncl activation script doesn't set environment variables properly
if not ("NCARG_ROOT" in os.environ) and ("CONDA_PREFIX" in os.environ):
   setenv("NCARG_ROOT","CONDA_PREFIX",envvars,verbose=verbose)


# ======================================================================
# DIRECTORIES: set up locations
# ======================================================================

# ======================================================================
#  Home directory for diagnostic code (needs to have 'var_code',  sub-directories)
setenv("DIAG_HOME",os.getcwd(),envvars,verbose=verbose)   # eg. mdtf/MDTF_2.0
setenv("DIAG_ROOT",os.path.dirname(os.environ["DIAG_HOME"]),envvars,verbose=verbose) # dir above DIAG_HOME

path_var_code_absolute = os.environ["DIAG_HOME"]+'/var_code/util/'

if ( verbose > 1): print "Adding absolute path to modules in "+path_var_code_absolute
sys.path.insert(0,path_var_code_absolute)

# ======================================================================
# inputdata contains model/$casename, obs_data/$package/*  #drb change?
setenv("DATA_IN",os.environ["DIAG_ROOT"]+"/inputdata/",envvars,verbose=verbose)

# ======================================================================
# output goes into wkdir & variab_dir (diagnostics should generate .nc files & .ps files in subdirectories herein)
setenv("WKDIR",os.getcwd()+"/wkdir",envvars,verbose=verbose)


# ======================================================================
# Input settings from namelist file (name = argument to this script, default DIAG_HOME/namelist)
# to set CASENAME,model,FIRSTYR,LASTYR, POD list and environment variables 
# Namelist class defined in read_files, contains: case (dict), pod_list (list), envvar (dict)

try:
   namelist_file = read_files.determine_namelist_file(sys.argv,verbose=verbose)
except Exception as error:
   print error
   exit()

# case info (type dict) =  {['casename',casename],['model',model],['FIRSTYR',FIRSTYR],['LASTYR',LASTYR]}
namelist  = read_files.read_text_file(namelist_file,verbose).namelist    

# pod_list (type list) =  [pod_name1,pod_name2,...]
pod_do    = namelist.pod_list   # list of pod names to do here

# Check if any required namelist/envvars are missing  
read_files.check_required_envvar(verbose,["CASENAME","model","FIRSTYR","LASTYR","NCARG_ROOT"])

# update local variables used in this script with env var changes from reading namelist
# variables that are used through os.environ don't need to be assigned here (eg. NCARG_ROOT)
test_mode = read_files.get_var_from_namelist('test_mode','bool',namelist.envvar,default=test_mode,verbose=verbose)
verbose   = read_files.get_var_from_namelist('verbose','int',namelist.envvar,default=verbose,verbose=verbose)

# ======================================================================
# OUTPUT
# output goes into WKDIR & variab_dir (diagnostics should generate .nc
# files & .ps files in subdirectories herein)

setenv("variab_dir",os.environ["WKDIR"]+"/MDTF_"+os.environ["CASENAME"],envvars,overwrite=False,verbose=verbose)

# ======================================================================
# INPUT: directory of model output
setenv("DATADIR",os.environ["DATA_IN"]+"model/"+os.environ["CASENAME"],envvars,overwrite=False,verbose=verbose)

# ======================================================================

# ======================================================================
# Software 
# ======================================================================
#
# Diagnostic package location and settings
#
# The environment variable DIAG_HOME must be set to run this script
#    It indicates where the variability package source code lives and should
#    contain the directories var_code and obs_data although these can be 
#    located elsewhere by specifying below.
setenv("VARCODE",os.environ["DIAG_HOME"]+"/var_code",envvars,overwrite=False,verbose=verbose)
setenv("VARDATA",os.environ["DATA_IN"]+"obs_data/",envvars,overwrite=False,verbose=verbose)
setenv("RGB",os.environ["VARCODE"]+"/util/rgb",envvars,overwrite=False,verbose=verbose)

# ======================================================================
# set variable names based on model
# ======================================================================
found_model = False
if os.environ["model"] == "CESM":
   import set_variables_CESM        #in var_code/util
   found_model = True
if os.environ["model"] == "CMIP":
   import set_variables_CMIP
   found_model = True
if os.environ["model"] == "AM4":
   import set_variables_AM4
   found_model = True
if found_model == False:
   print "ERROR: model ", os.environ["model"]," Not Found"
   print "      This is set in namelist "
   print "      CASE case-name *model* start-year end-year"
   quit()


# ======================================================================
# Check directories that must already exist
# ======================================================================

check_required_dirs( already_exist =["DIAG_HOME","VARCODE","VARDATA","NCARG_ROOT"], create_if_nec = ["WKDIR","variab_dir"],verbose=verbose)
os.chdir(os.environ["WKDIR"])



# ======================================================================
# set up html file
# ======================================================================
if os.path.isfile(os.environ["variab_dir"]+"/index.html"):
   print("WARNING: index.html exists, not re-creating.")
else: 
   os.system("cp "+os.environ["VARCODE"]+"/html/mdtf_diag_banner.png "+os.environ["variab_dir"])
   os.system("cp "+os.environ["VARCODE"]+"/html/mdtf1.html "+os.environ["variab_dir"]+"/index.html")


# ======================================================================
# Record settings in file variab_dir/namelist_YYYYMMDDHHRR for rerunning
#====================================================================
write_files.write_namelist(os.environ["variab_dir"],namelist,envvars,verbose=verbose)  


# ======================================================================
# Diagnostics:
# ======================================================================

# Diagnostic logic: call a piece of python code that: 
#   (A) Calls NCL, python (or other languages) to generate plots (PS)
#   (B) Converts plots to png
#   (C) Adds plot links to HTML file

pod_procs = []
log_files = []
for pod in pod_do:

   if verbose > 0: print("--- MDTF.py Starting POD "+pod+"\n")

   # Find and confirm POD driver script , program (Default = {pod_name,driver}.{program} options)
   # Each pod could have a settings files giving the name of its driver script and long name

   pod_dir = os.environ["VARCODE"]+"/"+pod
   try:
      pod_settings = read_files.read_text_file(pod_dir+"/settings",verbose).pod_settings
   except AssertionError as error:  
      print str(error)
   else:

      run_pod = pod_settings['program']+" "+pod_settings['driver']
      if ('long_name' in pod_settings) and verbose > 0: print "POD long name: ",pod_settings['long_name']

      # Check for files necessary for the pod to run (if pod provides varlist file)

      missing_file_list = read_files.check_varlist(pod_dir,verbose=verbose)
      if ( missing_file_list  ):
         print "WARNING: POD ",pod," Not executed because missing required input files:"
         print missing_file_list
      else:  # all_required_files_found
         if (verbose > 0): print "No known missing required input files"
         if test_mode:
            print("TEST mode: would call :  "+run_pod)
         else:
            start_time = timeit.default_timer()
            log = open(os.environ["variab_dir"]+"/"+pod+".log", 'w')
            log_files.append(log)
            try:
               print("Calling :  "+run_pod) # This is where the POD is called #
               proc = subprocess.Popen(run_pod, shell=True, env = os.environ, stdout = log, stderr = subprocess.STDOUT)
               pod_procs.append(proc)
            except OSError as e:
               print('ERROR :',e.errno,e.strerror)
               print(errstr + " occured with call: " +run_pod)

for proc in pod_procs:
   proc.wait()

for log in log_files:
   log.close()
               
if verbose > 0: 
   print("---  MDTF.py Finished POD "+pod+"\n")
   # elapsed = timeit.default_timer() - start_time
   # print(pod+" Elapsed time ",elapsed)
        
# ==================================================================================================
#  Make tar file
# ==================================================================================================
if ( ( os.environ["make_variab_tar"] == "0" ) ):
   print "Not making tar file because make_variab_tar = ",os.environ["make_variab_tar"]
else:
   print "Making tar file because make_variab_tar = ",os.environ["make_variab_tar"]
   if os.path.isfile( os.environ["variab_dir"]+".tar" ):
      print "Moving existing "+os.environ["variab_dir"]+".tar to "+os.environ["variab_dir"]+".tar_old"
      os.system("mv -f "+os.environ["variab_dir"]+".tar "+os.environ["variab_dir"]+".tar_old")
      os.chdir(os.environ["WKDIR"])

   print "Creating "+os.environ["variab_dir"]+".tar "
   status = os.system("tar --exclude='*netCDF' --exclude='*nc' --exclude='*ps' --exclude='*PS' -cf MDTF_"+os.environ["CASENAME"]+".tar MDTF_"+os.environ["CASENAME"])
   if not status == 0:
      print("ERROR $0")
      print("trying to do:     tar -cf "+os.environ["variab_dir"]+".tar "+os.environ["variab_dir"])
      exit()

print "Exiting normally from ",__file__
exit()
