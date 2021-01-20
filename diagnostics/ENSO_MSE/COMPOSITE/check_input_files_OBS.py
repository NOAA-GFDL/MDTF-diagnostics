import numpy as np
import os
import math
import sys

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)
from util import check_required_dirs

###   
###  check  the input data in inputdata/model  directories DATADIR + mon
## 3D
size = 17
vvar =  np.chararray( size, 5)

vvar[0]  = os.environ["zg_var"]
vvar[1]  = os.environ["ua_var"]
vvar[2]  = os.environ["va_var"]
vvar[3]  = os.environ["ta_var"]
vvar[4]  = os.environ["qa_var"]
vvar[5]  = os.environ["omega_var"]
##    2D  vars
vvar[6] = os.environ["pr_var"]
vvar[7] = os.environ["ts_var"]
vvar[8] = os.environ["hfss_var"]
vvar[9] = os.environ["hfls_var"]
## radiation
vvar[10] = os.environ["rsus_var"] 
vvar[11] = os.environ["rsds_var"] 
vvar[12] = os.environ["rsdt_var"] 
vvar[13] = os.environ["rsut_var"] 

vvar[14] = os.environ["rlus_var"] 
vvar[15] = os.environ["rlds_var"] 
vvar[16] = os.environ["rlut_var"] 

## check for missing files 

## hard coded for ERA-INTERIM
obsmodel = "ERA-INTERIM"

for iv in range(0, 16):
    filevar = os.environ["OBS_DATA"] + "/DATA/mon/" + obsmodel  + "." +  vvar[iv] + ".mon.nc"

    if not os.path.exists(filevar):
        print "============================================="
        print ("===  MISSING OBSERVATIONAL DATA FILE " + filevar  )
        print ("====  EXITING =================== ")
        sys.exit()
    else:
        print ("L49 Found "+filevar)

print  " ========================================================="
print " =========================================================="
print( " ============ All Observational files  found ============ ")
print  " ========================================================="
print " =========================================================="
print " =========================================================="

####
