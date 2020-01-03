import numpy as np
import os.path
import math
import sys
import os

##  
##  
###  check  the input data in inputdata/model  directories  reqquired for SCATTER routine 
## 


wkdir =  os.environ["WK_DIR"]
vardir = os.environ["POD_HOME"]

size = 4
vvar =  np.chararray( size, 5)
vvar[0]  = "FRAD"
vvar[1]  = "LHF"
vvar[2]  = "PR"
vvar[3]  = "SHF"

size = 2
vvar2 =  np.chararray( size, 8)
vvar2[0]  = "MSE_omse"
vvar2[1]  = "MSE_madv"

### checking the output direcories and create if missing 
if not os.path.exists( wkdir + "/MDTF_SCATTER/" ):
    os.makedirs( wkdir + "/MDTF_SCATTER/" )

######  check for each input model data .. 
namein =  os.environ["OBS_DATA"]  + "/SCATTER/central_pacific_MSE_terms.txt"
if not os.path.exists( namein):
    print "============================================="
    print ("===  MISSING FILE for SCATTER  =====" )
    print ( namein )
    exit()
namein =  os.environ["OBS_DATA"] + "/SCATTER/eastern_pacific_MSE_terms.txt"
if not os.path.exists( namein):
    print "============================================="
    print ("===  MISSING FILE for SCATTER  =====" )
    print ( namein )
    exit()

print "============================================="
print( " SCATTER input file check COMPLETED  ") 
print "============================================="
####
