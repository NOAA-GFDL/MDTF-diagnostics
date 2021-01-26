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
###  check  the input data in inputdata/obs_data  directories  DATADIR 
####    pre-digested data 
## 3D
size = 13

vvar = [ "zg", "ua", "va", "ta", "hus", "wap", "pr", "ts", "hfss", "hfls", "lw", "sw", "frad" ]

## check for missing files 
## 

mode = [ "ELNINO", "LANINA" ]

for n in range(0, 2):
    for iv in range(0, 13):
        filevar = os.environ["OBS_DATA"] + "/DATA/netCDF/" + mode[n]  + "/" +  vvar[iv] + ".nc"

        if not os.path.exists(filevar):
            print ("=============================================")
            print ("===  MISSING  PRE-DIGESTED OBSERVATIONAL DATA FILE " + filevar  )
            print ("====  EXITING =================== ")
            sys.exit()
        else:
            print ("L49 Found "+filevar)


        filevar = os.environ["OBS_DATA"] + "/DATA/netCDF/" +  vvar[iv] + "_clim.nc"

        if not os.path.exists(filevar):
            print ("=============================================")
            print ("===  MISSING  PRE-DIGESTED OBSERVATIONAL DATA FILE " + filevar  )
            print ("====  EXITING =================== ")
            sys.exit()
        else:
            print ("L49 Found "+filevar)

###   similarly CORR and REGRESS

mode = [ "CORR", "REGRESS" ]
vvar = [ "pr", "hfss", "hfls", "sw", "lw" ] 

for n in range(0, 2):
    for iv in range(0, 5):
        filevar = os.environ["OBS_DATA"] + "/DATA/netCDF/" + mode[n]  + "_" +  vvar[iv] + ".nc"

        if not os.path.exists(filevar):
            print ("=============================================")
            print ("===  MISSING  PRE-DIGESTED OBSERVATIONAL DATA FILE " + filevar  )
            print ("====  EXITING =================== ")
            sys.exit()
        else:
            print ("L49 Found "+filevar)

print (" =========================================================")
print (" ==========================================================")
print (" ==== All Pre-digested Observational files  found ======== ")
print (" =========================================================")
print (" ==========================================================")
print (" ==========================================================")
####
