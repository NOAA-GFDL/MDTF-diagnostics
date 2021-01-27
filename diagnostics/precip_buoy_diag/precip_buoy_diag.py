'''
This file is part of the precip_buoy_diag module of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt).

DESCRIPTION:

REQUIRED MODULES:

AUTHORS: Fiaz Ahmed

LAST EDIT:

REFERENCES: 

'''
# Import standard Python packages
import os
import glob
from sys import exit, path
import subprocess

### Set environment variables pointing to pr, hus, ta and ps. 
### Once path variables from settings.jsonc are available, this step is redundant.
os.environ["pr_file"] = "{DATADIR}/1hr/{CASENAME}.{pr_var}.1hr.nc".format(**os.environ)
os.environ["ta_file"] = "{DATADIR}/1hr/{CASENAME}.{ta_var}.1hr.nc".format(**os.environ)
os.environ["hus_file"] = "{DATADIR}/1hr/{CASENAME}.{qa_var}.1hr.nc".format(**os.environ)
os.environ["ps_file"] = "{DATADIR}/1hr/{CASENAME}.{ps_var}.1hr.nc".format(**os.environ)

### A cython executable must first be created.
### First delete any existing builds ###

try:
    os.remove()

try:
    build_cython=subprocess.call(['python', os.environ["POD_HOME"]+"/precip_buoy_diag_setup_cython.py", 
    'build_ext','--build-lib='+os.environ['POD_HOME']])
    if (build_cython.returncode)==0:
        print(build_cython)
        print('>>>>>>>Successfully compiled cython file')
        
except subprocess.CalledProcessError as e:
    print ("PODError > ",e.output)
    print ("PODError > ",e.stderr)
 
### Call the POD ###
# try:
#     run_POD=subprocess.run(["python", os.environ["POD_HOME"]+"/precip_buoy_diag_main.py"],
#     capture_output=True, check=True)
# 
# except subprocess.CalledProcessError as e:
#     print ("PODError > ",e.output)
#     print ("PODError > ",e.stderr)
    
    
