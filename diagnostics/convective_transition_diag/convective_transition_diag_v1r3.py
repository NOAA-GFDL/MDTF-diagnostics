# This file is part of the convective_transition_diag module of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)

# ======================================================================
# convective_transition_diag_v1r3.py
#
#   Convective Transition Diagnostic Package
#   
#   The convective transition diagnostic package computes statistics that relate 
#    precipitation to measures of tropospheric temperature and moisture, as an evaluation 
#    of the interaction of parameterized convective processes with the large-scale 
#    environment. Here the basic statistics include the conditional average and 
#    probability of precipitation, PDF of column water vapor (CWV) for all events and 
#    precipitating events, evaluated over tropical oceans. The critical values at which 
#    the conditionally averaged precipitation sharply increases as CWV exceeds the 
#    critical threshold are also computed (provided the model exhibits such an increase).
#
#   Version 1 revision 3 13-Nov-2017 Yi-Hung Kuo (UCLA)
#   PI: J. David Neelin (UCLA; neelin@atmos.ucla.edu)
#   Current developer: Yi-Hung Kuo (yhkuo@atmos.ucla.edu)
#   Contributors: K. A. Schiro (UCLA), B. Langenbrunner (UCLA), F. Ahmed (UCLA),
#    C. Martinez (UCLA), C.-C. (Jack) Chen (NCAR)
#
#   This package and the MDTF code package are distributed under the LGPLv3 license 
#    (see LICENSE.txt).
#
#   Currently consists of following functionalities:
#    (1) Convective Transition Basic Statistics (convecTransBasic.py)
#    (2) Convective Transition Critical Collapse (convecTransCriticalCollapse.py)
#    *(3) Moisture Precipitation Joint Probability Density Function (cwvPrecipJPDF.py)
#    *(4) Super Critical Precipitation Probability (supCriticPrecipProb.py)
#    More on the way...(* under development)
#
#   As a module of the MDTF code package, all scripts of this package can be found under
#    MDTF-diagnostics/diagnostics/convective_transition_diag**
#   and pre-digested observational data under 
#    mdtf/inputdata/obs_data/convective_transition_diag
#   (**$ver depends on the actual version of the MDTF code package)
#
#   This package is written in Python 2, and requires the following Python packages:
#    os,glob,json,Dataset,numpy,scipy,matplotlib, networkx,warnings,numba, netcdf4
#   The plotting functions in this package depend on an older version of matplotlib, 
#    thus an older version of the Anaconda 2 installer (ver. 5.0.1) is recommended
#
#   The following three 3-D (lat-lon-time) high-frequency model fields are required:
#     (1) precipitation rate (units: mm/s = kg/m^2/s; 6-hrly avg. or shorter)
#     (2) column water vapor (CWV, or precipitable water vapor; units: mm = kg/m^2)
#     (3) column-integrated saturation humidity (units: mm = kg/m^2)
#          or mass-weighted column average temperature (units: K) 
#          with column being 1000-200 hPa by default 
#   Since (3) is not standard model output, this package will automatically
#    calculate (3) if the following 4-D (lat-lon-pressure-time) model field is available:
#     (4) air temperature (units: K)
#
#   Reference: 
#    Kuo, Y.-H., K. A. Schiro, and J. D. Neelin, 2018: Convective transition statistics 
#      over tropical oceans for climate model diagnostics: Observational baseline. 
#      J. Atmos. Sci., 75, 1553-1570.
#    Kuo, Y.-H., and Coauthors: Convective transition statistics over tropical oceans
#      for climate model diagnostics: GCM performance. In preparation.***
#    ***See http://research.atmos.ucla.edu/csi//REF/pub.html for updates.
# ======================================================================
# Import standard Python packages
import os
import glob

# TSJ edit 8/8/2020: introduce BULK_TROPOSPHERIC_TEMPERATURE_VAR env var in POD's
# settings.jsonc in order to remove code in shared_diagnostic specific to this 
# POD. This statement translates the value of BULK_TROPOSPHERIC_TEMPERATURE_VAR
# into BULK_TROPOSPHERIC_TEMPERATURE_MEASURE, the env var used in the rest of the
# POD's code.
if os.environ.get('BULK_TROPOSPHERIC_TEMPERATURE_VAR','').lower() == 'tave':
    os.environ['BULK_TROPOSPHERIC_TEMPERATURE_MEASURE'] = '1'
elif os.environ.get('BULK_TROPOSPHERIC_TEMPERATURE_VAR','').lower() == 'qsat_int':
    os.environ['BULK_TROPOSPHERIC_TEMPERATURE_MEASURE'] = '2'
else:
    raise KeyError(
        'Unrecognized BULK_TROPOSPHERIC_TEMPERATURE_VAR = {}'.format(
        os.environ.get('BULK_TROPOSPHERIC_TEMPERATURE_VAR',''))
    )

os.environ["pr_file"] = "*."+os.environ["pr_var"]+".1hr.nc"
os.environ["prw_file"] = "*."+os.environ["prw_var"]+".1hr.nc"
os.environ["ta_file"] = "*."+os.environ["ta_var"]+".1hr.nc"
os.environ["tave_file"] = "*."+os.environ["tave_var"]+".1hr.nc"
os.environ["qsat_int_file"] = "*."+os.environ["qsat_int_var"]+".1hr.nc"

## Model output filename convention
os.environ["MODEL_OUTPUT_DIR"]=os.environ["DATADIR"]+"/1hr"
#os.environ["pr_file"] = "*."+os.environ["pr_var"]+".1hr.nc"
#os.environ["prw_file"] = "*."+os.environ["prw_var"]+".1hr.nc"
#os.environ["ta_file"] = "*."+os.environ["ta_var"]+".1hr.nc"
#os.environ["tave_file"] = "*."+os.environ["tave_var"]+".1hr.nc"
#os.environ["qsat_int_file"] = "*."+os.environ["qsat_int_var"]+".1hr.nc"

missing_file=0
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["pr_file"]))==0:
    print("Required Precipitation data missing!")
    missing_file=1
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["prw_file"]))==0:
    print("Required Precipitable Water Vapor (CWV) data missing!")
    missing_file=1
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["ta_file"]))==0:
    if (os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"]=="2" and \
       len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["qsat_int_file"]))==0) \
    or (os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"]=="1" and \
       (len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["qsat_int_file"]))==0 or \
        len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["tave_file"]))==0)):
        print("Required Temperature data missing!")
        missing_file=1

if missing_file==1:
    print("Convective Transition Diagnostic Package will NOT be executed!")
else:

    ##### Functionalities in Convective Transition Diagnostic Package #####
    # ======================================================================
    # Convective Transition Basic Statistics
    #  See convecTransBasic.py for detailed info
    try:
        os.system("python "+os.environ["POD_HOME"]+"/"+"convecTransBasic.py")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("Convective Transition Basic Statistics (convecTransBasic.py) is NOT Executed as Expected!")		
        print("**************************************************")

    ## ======================================================================
    ## Convective Transition Critical Collapse
    ##  Requires output from convecTransBasic.py
    ##  See convecTransCriticalCollapse.py for detailed info
    try:
        os.system("python "+os.environ["POD_HOME"]+"/"+"convecTransCriticalCollapse.py")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("Convective Transition Thermodynamic Critical Collapse (convecTransCriticalCollapse.py) is NOT Executed as Expected!")		
        print("**************************************************")

    ##### THE FOLLOWING FUNCTIONALITIES HAVE NOT BEEN IMPLEMENTED YET!!!#####
    ## ======================================================================
    ## Moisture Precipitation Joint Probability Density Function
    ##  See cwvPrecipJPDF.py for detailed info
    #os.system("python "+os.environ["POD_HOME"]+"/"+"cwvPrecipJPDF.py")
    ## ======================================================================
    ## Super Critical Precipitation Probability
    ##  Requires output from convecTransBasic.py
    ##  See supCriticPrecipProb.py for detailed info
    #os.system("python "+os.environ['POD_HOME']+"/supCriticPrecipProb.py") 

    print("**************************************************")
    print("Convective Transition Diagnostic Package (convective_transition_diag_v1r3.py) Executed!")
    print("**************************************************")
