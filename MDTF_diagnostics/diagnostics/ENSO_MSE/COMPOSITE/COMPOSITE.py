#
#      The code preprocesses the model input data to create
#      climatologies and corresponding anomalies.
#      Based on calculated anomalies, the code selects the El Nino/La Nina
#      years and construct corresponding seasonal composites.
#      Additionally,  seasonal correlations and regressions are calculated.
#      The final graphical outputs are placed in ~/wkdir/MDTF_$CASE directories.
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

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

from get_parameters_in import get_parameters_in

import datetime

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

now = datetime.datetime.now()
print("=========== COMPOSITE.py =======================================")
print("   Start of Composite Module calculations  " + now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")

###     The code construct the 24 month ENSO evolution cycle Year(0)+Year(1) and 
###     the resulting plots are set for default  DJF season (Year(0) of the 24 month ENSO cycle
####    
####     

undef = float(1.1e+20)
iundef = -9999

prefix = os.path.join(os.environ["POD_HOME"],"COMPOSITE")
wkdir_model = os.path.join(os.environ["ENSO_MSE_WKDIR_COMPOSITE"],"model")


season = "NIL"

llon1 = undef
llon2 = undef
llat1 = undef
llat2 = undef

imindx1 = undef
imindx2 = undef

sigma = undef
composite = 0
composite24 = 0
regression = 0
correlation = 0
## optionally read in the parameters

iy1 = os.environ["FIRSTYR"] 
iy2 = os.environ["LASTYR"] 
iy1 = int(iy1)
iy2 = int(iy2)

model = os.environ["CASENAME"] 
im1 = int( undef)
im2 = int( undef)  
#####

llon1, llon2, llat1, llat2, sigma, imindx1, imindx2,  composite, im1, im2, season,  composite24, regression, correlation,  undef =  get_parameters_in(llon1, llon2, llat1, llat2, sigma, imindx1, imindx2, composite, im1, im2, season, composite24, regression, correlation,  undef, prefix)


### print diagnostic message 
print ("  The following parameters are set in the Composite Module Calculations  ")
print ("      the reference area for SST indices calculations is selected to:        ")
print ("      lon = ", llon1, " - ", llon2 , " E", "lat = ", llat1, " - ", llat2, "N" )
print ("      ENSO indices  based on SST reference anomalies +/- ", sigma, " of SST sigma")
print ("      Selected season  is : ", season   )
print ("      Selected year span for composites is : ", iy1,"/",  iy2 )
print ("      Selected model  : " , model  )
print ("   " )
print ("    The following elements will be calculated  " )
if( composite == 1):
    print ("       Seasonal Composites for El Nino/La Nina years ")
if( composite24 == 1):
    print ("       2 Year life cycle of ENSO:  Year(0) and Year(1) " )
    print ("                Year (0) = developing phase and Year(1) = decaying phase ")
if( correlation == 1):
    print ("       Reference area SST correlations will be calculated ") 
if( regression == 1):
    print ("      Regressions to reference area SST will be calculated ")

print (" ") 

### run the composite data routine 
generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL_DATA/get_composites.ncl")
  

###   plotting composites  
generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_composite_all.ncl")

now = datetime.datetime.now()
print ("   Seasonal ENSO composites completed:  " + now.strftime("%Y-%m-%d %H:%M") )
print ("   plots of ENSO seasonal composites finished  ")
print ("   resulting plots are located in : " + wkdir_model)
print ("   with prefix composite  + ELNINO/LANINA +  variable name " )

####################################3333
##########   seasonal correlation, calculations with seasonal NINO3.4 SST anomalies 
###   plot correlations 
generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_correlation_all.ncl")

print ("   Seasonal  SST  correlations completed  " + now.strftime("%Y-%m-%d %H:%M") )
print ("   plots of  seasonal correlations  finished  " )
print ("   resulting plots are located in : " + wkdir_model )
print ("     with prefix correlation + variable name " )

print (" ")     
###  plotting routine  below:
print("DRBDBG COMPOSITE.py regression ",regression)
##     plotting the regressions 
##     print("DRBDBG calling ",os.environ["POD_HOME"],"/COMPOSITE/NCL/plot_regression_all.ncl")
generate_ncl_call(os.environ["POD_HOME"]+ "/COMPOSITE/NCL/plot_regression_all.ncl")

print ("   Seasonal SST  regressions completed  " + now.strftime("%Y-%m-%d %H:%M") )
print ("   plots of seasonal regressions  finished  ")
print ("   resulting plots are located in : " + wkdir_model)
print ("     with prefix  regression  +  variable name " )

print(os.system("ls "+wkdir_model))

file_src  = os.environ["POD_HOME"]+"/COMPOSITE/COMPOSITE.html"
file_dest = os.environ["ENSO_MSE_WKDIR"]+"/COMPOSITE.html" 
if os.path.isfile( file_dest ):
    os.system("rm -f "+file_dest)
os.system("cp "+file_src+" "+file_dest)

#============================================================
#
now = datetime.datetime.now()
print ("   ") 
print (" ===================================================================")
print ("         Composite Module Finished  " +  now.strftime("%Y-%m-%d %H:%M") )
print (" ===================================================================")
### 
