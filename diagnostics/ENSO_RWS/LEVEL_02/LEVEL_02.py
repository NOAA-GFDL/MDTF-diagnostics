#
#      The code calculates basic Rossby Wave Source terms and associatted variables 
#
#       Contact Information:
#       PI :  Dr. H. Annamalai,
#             International Pacific Research Center,
#             University of Hawaii at Manoa
#             E-mail: hanna@hawaii.edu
#
#       programming :  Jan Hafner,  jhafner@hawaii.edu
#
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
print("=========== LEVEL_02.py =======================================")
print("   Start of LEVEL_02 calculations  " + now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")


generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_02/NCL/plot_betastar_clima.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_02/NCL/plot_divergence_clima.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_02/NCL/plot_divergent_wind_clima.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_02/NCL/plot_stream_fnc_clima.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_02/NCL/plot_U_wind_clima.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_02/NCL/plot_wave_number_clima.ncl")

## copy the html file
file_src  = os.environ["POD_HOME"]+"/LEVEL_02/LEVEL_02.html"
file_dest = os.environ["ENSO_RWS_WKDIR"]+"/LEVEL_02.html"
if os.path.isfile( file_dest ):
    os.system("rm -f "+file_dest)
os.system("cp "+file_src+" "+file_dest)


now = datetime.datetime.now()
print (" LEVEL_02 completed " +  now.strftime("%Y-%m-%d %H:%M") )

