#
#      The code prepares the pre-digested OBS  data 
#      The final graphical outputs are placed in ~/wkdir/COMPOSITE/obs/ directory
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
##      This package is distributed under the LGPLv3 license (see LICENSE.txt) 

import numpy as np
import sys
import math

import datetime

import os
shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

from util import check_required_dirs
from generate_ncl_call import generate_ncl_call

'''
      This package is distributed under the LGPLv3 license (see LICENSE.txt)
      The top driver code for the COMPOSITE module for observational data.

      The code prepares the pre-digested OBS model input data to create
      final graphical output
  ========================================================================
     The pre-digested input data are as follows : 

     3-dimensional atmospheric variables dimensioned IMAX, JMAX, ZMAX
     HGT - geopotential height [m]
     UU  - U  wind  [m/s]
     VV  - V wind [m/s]
     TEMP  - temperature [K]
     SHUM - specific humidity [kg/kg]
     VVEL - vertical velocity [Pa/s]
 
    2-dimensional variables  (fluxes)
    outputs are 3-dimensional MSE components and its 2-dimensional 
      vertical integrals

      PRECIP precip. kg/m2/sec
      SST    Skin Surface Temperature   [K]
      SHF    sensible heat flux  [W/m2]
      LHF    latent heat flux [W/m2]
      SW     net SW flux [W/m2]  ( or individual SW flux components)
      LW     net LW flux [W/m2]  ( or individual LW flux components)
      
    all for full values.

     Additionally needed on input :
      imax  - x horizontal model dimension
      jmax -  y horizontal model dimension
         zmax -  z vertical model  dimension  and 
      PLEV - pressure levels [mb]

     missing values are flagged by UNDEF which is a large number

'''

### 
####    
##   the pointer to code directory 
##  call for plotting routines 
wkdir_obs = os.environ["ENSO_MSE_WKDIR_COMPOSITE"]+"/obs"
####  make the plots  composites 
now = datetime.datetime.now()
print ("  Seasonal Observational ENSO composites starting:  " + now.strftime("%Y-%m-%d %H:%M") )
print ("  ")

generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_composite_all_OBS.ncl")

now = datetime.datetime.now()
print ("   Seasonal Observational ENSO composites completed:  " + now.strftime("%Y-%m-%d %H:%M") )
print ("   plots of ENSO seasonal composites finished  " )
print ("   resulting plots are located in : " +  wkdir_obs )
print ("   with prefix composite  + ELNINO/LANINA +  variable name " ) 

##########   correlation 
generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_correlation_all_OBS.ncl")

print ("   Seasonal Observational SST  correlations completed  " )
print ("   plots of  seasonal correlations  finished  " )
print ("   resulting plots are located in : " + wkdir_obs )
print ("   with prefix correlation + variable name " )

###########  regression 
generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_regression_all_OBS.ncl")

print ("   Seasonal Observational SST  regressions completed  " )
print ("   plots of seasonal regressions  finished  " )
print ("   resulting plots are located in : " + wkdir_obs )
print ("     with prefix  regression  +  variable name " )


##############   end 
now = datetime.datetime.now()
print ("   ")
print (" ===================================================================" )
print (" Observational Composite Module Finished  " +  now.strftime("%Y-%m-%d %H:%M") )
print (" ===================================================================" )
### 
