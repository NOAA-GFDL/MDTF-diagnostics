###
#       The code makes scatter plots of seasonal El Nino/La Nina
#       composite anomalies of selected variables and selected models.
#       It requires pre-processed data from the COMPOSITE module for
#       all selected models and variables.
#
#       Contact Information:
#       PI :  Dr. H. Annamalai,
#             International Pacific Research Center,
#             University of Hawaii at Manoa
#             E-mail: hanna@hawaii.edu
#
#       programming :  Jan Hafner,  jhafner@hawaii.edu
#
#    This package is distributed under the LGPLv3 license (see LICENSE.txt)


import numpy as np
import sys
import math
import subprocess
import time

import datetime
import os


shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

from get_scatter_data import get_scatter_data
from generate_ncl_call import generate_ncl_call


'''
       This package is distributed under the LGPLv3 license (see LICENSE.txt)

        input data are as follows:
 
      2-dimensional variables  (fluxes)
     vertical integrals

      PR -precip. kg/m2/sec
         moisture advection  W/m2
         net radiative flux  W/m2
         vertical MSE advection W/m2
         total heat flux (LHF + SHF) W/m2

     Additionally needed on input :
      LON - longitudes [deg.]
      LAT - latitudes [deg.]
      PLEV - pressure levels [mb]

     missing values are flagged by UNDEF which is a large number

'''

now = datetime.datetime.now()
print("===============================================================")
print("      Start of Scatter Plot Module calculations " +  now.strftime("%Y-%m-%d %H:%M"))
print("===============================================================")

undef = float(1.1e+20)

###  first prefix for data   + other variables passed to the code 
wkdir =  os.environ["ENSO_MSE_WKDIR"]

####  creating  data fro NEW MODEL to be plotted in SCATTER plots 
###   Central Pacific
clon1 = 160.
clon2 = 200.
clat1 = -10.
clat2 = 5.
##  and  Eastern Pacific
elon1 = 220.
elon2 = 280.
elat1 = -5.
elat2 = 5.

####  call  the model routine to select NEW MODEL data for SCATTER plots 

get_scatter_data( clon1, clon2, clat1, clat2, elon1, elon2, elat1, elat2, undef)

#############################
time.sleep(6.)

###  make the plots  in NCL  
####     default domain plotting   
generate_ncl_call(os.environ["POD_HOME"]+ "/SCATTER/NCL/scatter_01.ncl")
generate_ncl_call(os.environ["POD_HOME"]+ "/SCATTER/NCL/scatter_02.ncl")
generate_ncl_call(os.environ["POD_HOME"]+ "/SCATTER/NCL/scatter_03.ncl")
generate_ncl_call(os.environ["POD_HOME"]+ "/SCATTER/NCL/scatter_04.ncl")

###    copy the html files for to create webpages
if os.path.isfile( os.environ["ENSO_MSE_WKDIR"]+"/SCATTER.html" ):
    os.system("rm -f "+os.environ["ENSO_MSE_WKDIR"]+"/SCATTER/SCATTER.html")

os.system("cp "+os.environ["POD_HOME"]+"/SCATTER/SCATTER.html "+os.environ["ENSO_MSE_WKDIR"]  )

###  the end 
now = datetime.datetime.now()
print("   " )
print( " ===================================================================")
print( "  Scatter  Module Finished    " + now.strftime("%Y-%m-%d %H:%M") )
print( "  resulting plots are located in : " +os.environ["ENSO_MSE_WKDIR"],"/SCATTER/")
print( " ===================================================================")
### 
