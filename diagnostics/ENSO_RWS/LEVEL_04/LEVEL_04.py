#
#      The code calculates basic Rossby Wave Source terms and associatted variables 
#          on all available pressure levels 
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

    2-dimensional variables  (fluxes)

      PRECIP precip. kg/m2/sec

    all for full values.
'''

now = datetime.datetime.now()
print("=========== LEVEL_04.py =======================================")
print("   Start of LEVEL_04 calculations  " + now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")

##  input data directory
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/get_PNA_index.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_01.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_02.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_03.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_04.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_05.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_06.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_07.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_08.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_09.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_04/NCL/scatter_plot_10.ncl")

## copy the html file
file_src  = os.environ["POD_HOME"]+"/LEVEL_04/LEVEL_04.html"
file_dest = os.environ["ENSO_RWS_WKDIR"]+"/LEVEL_04.html"
if os.path.isfile( file_dest ):
    os.system("rm -f "+file_dest)
os.system("cp "+file_src+" "+file_dest)


now = datetime.datetime.now()
print (" LEVEL_04 completed " +  now.strftime("%Y-%m-%d %H:%M") )

