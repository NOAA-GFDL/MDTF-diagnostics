import os
import sys

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

###   
###  check  the input data in inputdata/obs_data  directories  DATADIR 
####    pre-digested data 
## 3D

size = 7

vvar = [ "zg", "ua", "va", "ta", "wap", "pr", "ts" ]

## check for missing files 
## 

mode = [ "ELNINO", "LANINA" ]

for n in range(0, 2):
    for iv in range(0, size):
        filevar = os.environ["OBS_DATA"] + "/DATA/netCDF/" + mode[n]  + "/" +  vvar[iv] + ".nc"

        if not os.path.exists(filevar):
            print ("=============================================")
            print ("===  MISSING  PRE-DIGESTED OBSERVATIONAL DATA FILE " + filevar  )
            print ("====  EXITING =================== ")
            sys.exit()
        else:
            print ("L49 Found "+filevar)


        filevar = os.environ["OBS_DATA"] + "/DATA/netCDF/" +  vvar[iv] + ".nc"

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
