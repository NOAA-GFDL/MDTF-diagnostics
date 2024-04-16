"""
This file is part of the precip_buoy_diag module of the 
MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt).

DESCRIPTION:

REQUIRED MODULES:

AUTHORS: Fiaz Ahmed

LAST EDIT:

REFERENCES: 
"""
# Import standard Python packages
import os
import subprocess
from precip_buoy_diag_util import precipbuoy

# Set environment variables pointing to pr, hus, ta and ps.
# Once path variables from settings.jsonc are available, this step is redundant.
os.environ["ta_file"] = "{DATADIR}/1hr/{CASENAME}.{ta_var}.1hr.nc".format(**os.environ)
os.environ["hus_file"] = "{DATADIR}/1hr/{CASENAME}.{qa_var}.1hr.nc".format(**os.environ)
os.environ["pr_file"] = "{DATADIR}/1hr/{CASENAME}.{pr_var}.1hr.nc".format(**os.environ)
os.environ["ps_file"] = "{DATADIR}/1hr/{CASENAME}.{ps_var}.1hr.nc".format(**os.environ)
# This POD produces intermediate files that are worth saving.
# Here we specify the save directory.
# Can include option to obtain this from settings.jsonc.
os.environ["temp_dir"] = os.environ["WORK_DIR"]+'/model'
os.environ["temp_file"] = "{temp_dir}/{CASENAME}.buoy_var.1hr.nc".format(**os.environ)
os.environ["binned_output"] = "{WORK_DIR}/obs/{CASENAME}.binnedpcp.1hr.nc".format(**os.environ)

# Read obs. files for plotting
OBS_FILE_NAME = 'trmm3B42_era5_2002_2014.convecTransLev2.nc'
CMIP6_FILE_NAME = 'ERA5_CMIP6_gamma_properties.nc'

os.environ["binned_obs"] = "{OBS_DATA}/".format(**os.environ) + OBS_FILE_NAME
os.environ["cmip6_output"] = "{OBS_DATA}/".format(**os.environ) + CMIP6_FILE_NAME

# Obtain the location of the region mask ###
# Another flexible option to read in from user
os.environ["region_mask"] = os.environ["WORK_DIR"] + '/model/' + 'region_0.25x0.25_costal2.5degExcluded.mat'

# A cython executable must be created.
# First delete any existing builds ###

try:
    os.remove(os.environ["POD_HOME"] + '/*.c')
    os.remove(os.environ["POD_HOME"] + '/*.so')
except Exception as exc:
    print(exc)
    pass

# Compiling cython
try:
    build_cython=subprocess.run(['python', 
    os.environ["POD_HOME"] + "/precip_buoy_diag_setup_cython.py", 'build_ext',
                                 '--build-lib=' + os.environ['POD_HOME']], check=True)
    if build_cython.returncode == 0:
        print('>>>>>>>Successfully compiled cython file')
except subprocess.CalledProcessError as err:
    print("PODError > ", err.output)
    print("PODError > ", err.stderr)


# Calling POD ###

# initialize pod ###
pb_pod = precipbuoy()

if pb_pod.binned:
    print('BINNED OUTPUT AVAILABLE. MOVING ONTO PLOTTING...')
    pb_pod.plot()
else:
    print('BINNED OUTPUT UNAVAILABLE. CHECKING FOR PREPROCESSED FILES')
        
    # Check if pre-processed files are available.

    if pb_pod.preprocessed:
        print('PREPROCESSED FILES AVAILABLE. MOVING ONTO BINNING...')
        pb_pod.bin()
        print('BINNING DONE. NOW PLOTTING...')
        pb_pod.plot()
    
    else:
        print('PREPROCESSING REQUIRED....')
        pb_pod.preprocess()
        print('PREPROCESSING DONE. NOW BINNING...')
        pb_pod.bin()
        print('BINNING DONE. NOW PLOTTING...')
        pb_pod.plot()
