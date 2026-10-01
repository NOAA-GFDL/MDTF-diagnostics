#
#      The code at this level uses pre-calculated data from levels 1 and 2
#     COMPOSITE and MSE.  It calculates the Moist Static Energy (MSE)
#    variances and select variable co-variances.  Area averaged seasonal
#     MSE variances and co-variances are displayed in bar charts in
#     ~/wkdir/MDTF_$CASE  directories.
#
#       Contact Information:
#       PI :  Dr. H. Annamalai,
#             International Pacific Research Center,
#             University of Hawaii at Manoa
#             E-mail: hanna@hawaii.edu
#
#       programming :  Jan Hafner,  jhafner@hawaii.edu
#
#     This package is distributed under the LGPLv3 license (see LICENSE.txt)


import sys

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

      The top driver for the MSE component variances calculations
       all need to be anomalies !!!
      input data are as follows:
       2 dimensional atmospheric variables: all vertical integrals
   dimensions:  IMAX, JMAX
   variables : TS:  skin surface  temperature [K]
               PR :  precipitation rate [kg/m2/sec]
               LHF :  latent heat flux  [W/m2]
               SHF :  sensible heat flux  [W/m2]
               SW  :  net  shortwave flux [W/m2]
               LW  :  net  longwave flux [W/m2]
               MSE :  vertical integral of Moist Static Energy [J/m2]
               MADV :  moisture advection [W/m2]
               OMSE  : MSE vertical advection [W/m2]
   1 dimensional INPUT:
         LON(IMAX) - longitude dimensions
         LAT(JMAX) - latitude dimensions
         PLEV(ZMAX) - vertical dimensions and  pressure levels [mb]
         REARTH  - radius of earth in  [m]

     pamaters LON1, LON2, LAT1, LAT2   for spatial variances
    OUTPUT:   variances of input variables (over selected area)
               TS_VAR:  skin surface  temperature [K]
               PR_VAR :  precipitation rate [kg/m2/sec]
               LHF_VAR :  latent heat flux  [W/m2]
               SHF_VAR :  sensible heat flux  [W/m2]
               SW_VAR  :  net  shortwave flux [W/m2]
               LW_VAR  :  net  longwave flux [W/m2]
               MSE_VAR :  vertical integral of Moist Static Energy [J/m2]
               MADV_VAR :  moisture advection [W/m2]
               OMSE_VAR  : MSE vertical advection [W/m2]


  missing data are flaged by UNDEF which is a very large number

'''

now = datetime.datetime.now()
print ("   Seasonal MODEL ENSO MSE Variance composites started  " + now.strftime("%Y-%m-%d %H:%M") )

###   call the routine to calculate MSE
generate_ncl_call(os.environ["POD_HOME"]+ "/MSE_VAR/NCL_DATA/get_MSE_VAR.ncl")

###########  plot the default domain NINO3.4 bar plots
generate_ncl_call(os.environ["POD_HOME"]+ "/MSE_VAR/NCL/plot_bars_composite.ncl")
generate_ncl_call(os.environ["POD_HOME"]+ "/MSE_VAR/NCL/plot_bars_composite_general.ncl")

##################################
file =  os.environ["ENSO_MSE_WKDIR"] + "/MSE_VAR.html"
if os.path.isfile( file ):
    os.system("rm -f "+file)
os.system("cp "+os.environ["POD_HOME"]+"/MSE_VAR/MSE_VAR.html " + file)

#============================================================
# DRB: no longer necessary to add a link to top index.html
# because it is linked from the ENSO_MSE/index.html
#============================================================

mse_var_dir   = os.environ["ENSO_MSE_WKDIR_MSE_VAR"] + "/model"

now = datetime.datetime.now()
print (" ===================================================================" )
print ("         MSE Variances Finished     " + now.strftime("%Y-%m-%d %H:%M") )
print ( "   resulting plots are located in : " +mse_var_dir )
print (" ===================================================================")

