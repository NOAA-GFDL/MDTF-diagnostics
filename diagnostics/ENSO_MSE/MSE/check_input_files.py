
import os
import sys
### import xarray as xr 


shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

###   
###  check  the input data in COMPOSITE/model  directories 
## 3D
size = 12

vvar  = [ "zg",  "ua", "va",  "ta", "hus", "wap", "pr",  "ts", "hfls", "hfss", "lw", "sw" ] 
##
 
mode = [ "ELNINO", "LANINA" ]

## check for missing files 


for iv in range(0, size):

    for n in range(0, 2):
        filevar = os.environ["WK_DIR"] + "/COMPOSITE/model/netCDF/" + mode[n] + "/" + vvar[iv] + ".nc"

        if not os.path.exists(filevar):
            print ("=============================================")
            print ("===  MISSING INPUT FILE " + filevar  )
            print ("====  EXITING =================== ")
            ##raw_input("Press any key to continue")
            sys.exit()


    filevar = os.environ["WK_DIR"] + "/COMPOSITE/model/netCDF/" + vvar[iv] + "_clim.nc"

    if not os.path.exists(filevar):
        print ("=============================================")
        print ("===  MISSING INPUT FILE " + filevar  )
        print ("====  EXITING =================== ")
        raw_input("Press any key to continue")
        sys.exit()

print  (" =========================================================")
print  (" ==========================================================")
print  ("===========  All model input files found =============== ")
print  ( " =========================================================")
print  (" ==========================================================")

####
