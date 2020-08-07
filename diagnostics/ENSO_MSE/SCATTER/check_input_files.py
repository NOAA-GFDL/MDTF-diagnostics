import numpy as np
import os.path
import math
import sys
import os

##  
##  
###  check  the input data in inputdata/model  directories  reqquired for SCATTER routine 
## 

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)


wkdir =  os.environ["ENSO_MSE_WKDIR"]
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
if not os.path.exists( wkdir + "/SCATTER/" ):
    os.makedirs( wkdir + "/SCATTER/" )

######  check for each input model data .. 
namein =  os.environ["POD_HOME"]  + "/SCATTER/central_pacific_MSE_terms.txt"
if not os.path.exists( namein):
    print "============================================="
    print ("===  MISSING FILE for SCATTER  =====" )
    print ( namein )
    exit()
namein =  os.environ["POD_HOME"] + "/SCATTER/eastern_pacific_MSE_terms.txt"
if not os.path.exists( namein):
    print "============================================="
    print ("===  MISSING FILE for SCATTER  =====" )
    print ( namein )
    exit()

print "============================================="
print( " SCATTER input file check COMPLETED  ") 
print "============================================="
####
