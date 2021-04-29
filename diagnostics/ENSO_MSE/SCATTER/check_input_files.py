import numpy as np
import os.path
import math
import sys
import os

##  
##  
###  check  the input data in inputdata/model  directories  required for SCATTER routine 
## 

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

wkdir =  os.environ["ENSO_MSE_WKDIR"]
vardir = os.environ["POD_HOME"]
obsdata = os.environ["OBS_DATA"] 

### checking the output direcories and create if missing 
if not os.path.exists( wkdir + "/SCATTER/" ):
    os.makedirs( wkdir + "/SCATTER/" )

if not os.path.exists( wkdir + "/SCATTER/netCDF" ):
    os.makedirs( wkdir + "/SCATTER/netCDF" )

if not os.path.exists( wkdir + "/SCATTER/PS" ):
    os.makedirs( wkdir + "/SCATTER/PS" )

####  copy pre-calculated scatter data to working directory from inputdata/obs_data/SCATTER
dest = wkdir  + "/SCATTER/netCDF/"
namein1 = obsdata +  "/SCATTER/central_pacific_MSE_terms.txt"
namein2 = obsdata +  "/SCATTER/eastern_pacific_MSE_terms.txt"
namein3 = obsdata +  "/SCATTER/list-models-historical-obs"

os.system( 'cp ' + namein1 + ' ' + dest )
os.system( 'cp ' + namein2 + ' ' + dest )
os.system( 'cp ' + namein3 + ' ' + dest )

######  check for each input model data .. 
namein = dest +  "central_pacific_MSE_terms.txt"
if not os.path.exists( namein):
    print ("=============================================")
    print ("===  MISSING FILE for SCATTER  =====" )
    print ( namein )
    exit()
namein = dest + "eastern_pacific_MSE_terms.txt"
if not os.path.exists( namein):
    print ("=============================================")
    print ("===  MISSING FILE for SCATTER  =====" )
    print ( namein )
    exit()

print( "=============================================")
print( " SCATTER input file check COMPLETED  ") 
print( "=============================================")
####
