#
#      The code preprocesses the model input data to create
#      climatologies and corresponding anomalies.
#      Based on calculated anomalies, the code selects the El Nino/La Nina
#      years and construct corresponding seasonal composites.
#
#       Contact Information:
#       PI :  Dr. H. Annamalai,
#             International Pacific Research Center,
#             University of Hawaii at Manoa
#             E-mail: hanna@hawaii.edu
#
#       programming :  Jan Hafner,  jhafner@hawaii.edu
#
#       Reference:
#       Annamalai, H., J. Hafner, A. Kumar, and H. Wang, 2014:
#       A Framework for Dynamical Seasonal Prediction of Precipitation
#       over the Pacific Islands. J. Climate, 27 (9), 3272-3297,
#       doi:10.1175/JCLI-D-13-00379.1. IPRC-1041.
#
#       last update : 2020-10-05
#
##      This package is distributed under the LGPLv3 license (see LICENSE.txt)

import sys
import os

import datetime

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

from generate_ncl_call import generate_ncl_call

'''
      This package is distributed under the LGPLv3 license (see LICENSE.txt)
      The top driver code for the COMPOSITE module.

      The code preprocessed the model input data to create
      climatologies and corresponding anomalies.

   ========================================================================
      input data are as follows:
      3-dimensional atmospheric variables dimensioned IMAX, JMAX, ZMAX
     HGT - geopotential height [m]
     UU  - U  wind  [m/s]
     VV  - V wind [m/s]
     TEMP  - temperature [K]
     VVEL - vertical velocity [Pa/s]

    2-dimensional variables  (fluxes)

      PRECIP precip. kg/m2/sec
      SST    Skin Surface Temperature   [K]

    all for full values.
    outputs are 3-dimensional composites and its 2-dimensional vertical integrals
'''

now = datetime.datetime.now()
print("=========== LEVEL_01.py =======================================")
print("   Start of LEVEL_01 calculations  " + now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")

### print diagnostic message

##  need to get Q1 vertically integrated 
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL_DATA/get_composites.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL_DATA/Q1_routine.ncl")

now = datetime.datetime.now()
print (" Plotting routines start " + now.strftime("%Y-%m-%d %H:%M") )

generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RR_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_SST_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_HGT_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_Q1_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_stream_fnc_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_divergent_wind_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_divergence_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RR_adiv_aUVdiv_overlay.ncl")

generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_Hgt_Vanom_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RR_adiv_aUVdiv_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RWS_aUVdiv_cvort_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RWS_betastar_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RWS_Uclima_overlay.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/plot_RWS_wavenumber_overlay.ncl")

## copy the html file
file_src  = os.environ["POD_HOME"]+"/LEVEL_01/LEVEL_01.html"
file_dest = os.environ["ENSO_RWS_WKDIR"]+"/LEVEL_01.html"
if os.path.isfile( file_dest ):
    os.system("rm -f "+file_dest)
os.system("cp "+file_src+" "+file_dest)


now = datetime.datetime.now()
print (" LEVEL_01 completed " +  now.strftime("%Y-%m-%d %H:%M") )

