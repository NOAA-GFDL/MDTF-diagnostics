#
#      The code utilizes the pre-processed data from Level 1 - COMPOSITE.
#      It calculates and plots Moist Static Energy (MSE) budget variables 
#      as seasonal ENSO composite anomalies and their vertical integrals: 
#      horizontal moisture advection, vertical MSE advection,  MSE,   
#      MSE divergence, MSE avection, temperature advection, moisture divergence 
#
#       Contact Information:
#       PI :  Dr. H. Annamalai,
#             International Pacific Research Center,
#             University of Hawaii at Manoa
#             E-mail: hanna@hawaii.edu
#
#       programming :  Jan Hafner,  jhafner@hawaii.edu
#
#      This package is distributed under the LGPLv3 license (see LICENSE.txt)
### 
###    the OBServational routine just reads and plots 
###    pre-digested Observational Data 
##     

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

from generate_ncl_call import generate_ncl_call

'''
      This package is distributed under the LGPLv3 license (see LICENSE.txt)

      The top drived for the MSE budget component calculations
      input data are as follows:
      3-dimensional atmospheric variables dimensioned IMAX, JMAX, ZMAX
     HGT - geopotential height [m]
     UU  - U  wind  [m/s]
     VV  - V wind [m/s]
     TEMP  - temperature [K]
     SHUM - specific humidity [kg/kg]
     VVEL - vertical velocity [Pa/s]
 
    outputs are 3-dimensional MSE components and its 2-dimensional 
      vertical integrals

     MSE3 - Moist Static Energy   3-dimensional [J/kg]
     MSE2 - vertical integral of MSE  2-dimensional [J/m2]

     MSE3_ADV  MSE horizontal advection  3-dimensional [w/kg]
     MSE2_ADV  vertical integral of ADV_MSE3 2-dimensional [W/m2]

        MSE3_DIV  MSE horizontal divergence  3-dimensional [w/kg]
        MSE2_DIV  vertical integral of DIV_MSE3 2-dimensional [W/m2]

     MADV3 -  horizontal advection of moisture  3-dimensional [W/kg]
     MADV2 -  vertical integral of MADV3 2-dimensional [W/m2]

        MDIV3 -  horizontal  moisture  divergence  3-dimensional [W/kg]
        MDIV2 -  vertical integral of MDIV3 2-dimensional [W/m2]
 
        TADV3 -  horizontal advection of temperature  3-dimensional [W/kg]
        TADV2 -  vertical integral of TADV3 2-dimensional [W/m2]
        
        OMSE3 -  vertical advection of MSE  3-dimensional [W/kg]
        OMSE2 -  vertical integral of OMSE3 2-dimensional [W/m2]

     Additionally needed on input :
      LON - longitudes [deg.]
      LAT - latitudes [deg.]
      PLEV - pressure levels [mb]

     missing values are flagged by UNDEF which is a large number

'''

### declaration and set up of relavant directories 

outdir = os.environ["ENSO_MSE_WKDIR_MSE"] + "/obs"

## base path of all input files (created by COMPOSITE package)
now = datetime.datetime.now()

print("===============================================================")
print("      Start of Observational Moist Static Energy  Module  " +  now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")
print( "  ")

###     plotting routine for all El Nino/La Nina cases 
generate_ncl_call(os.environ["POD_HOME"]+ "/MSE/NCL/plot_composite_all_OBS.ncl")
    
now = datetime.datetime.now()

print ("   Seasonal Observational ENSO MSE composites completed  " + now.strftime("%Y-%m-%d %H:%M") )
print ("   plots of ENSO seasonal MSE anomalies finished  ")
print ("   resulting plots are located in : " + outdir )
print ("   with prefix composite  + ELNINO/LANINA +  variable name ")
print ("  " )
#============================================================
############  end 
