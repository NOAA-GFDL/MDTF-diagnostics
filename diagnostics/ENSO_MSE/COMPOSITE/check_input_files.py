
import os
import math
import sys
import os.path


import numpy as np
import xarray as xr

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

vvar = [ os.environ["zg_var"], os.environ["ua_var"], os.environ["va_var"],  \
         os.environ["ta_var"], os.environ["qa_var"], os.environ["omega_var"], \
         os.environ["pr_var"], os.environ["ts_var"], os.environ["hfss_var"], \
         os.environ["hfls_var"],  os.environ["rsus_var"], os.environ["rsds_var"], \
         os.environ["rsdt_var"], os.environ["rsut_var"], os.environ["rlus_var"], \
         os.environ["rlds_var"], os.environ["rlut_var"] ]

## check for missing files and mismatched units 

unit = [ "m", "m s-1", "m s-1", "K", "1", "Pa s-1",  \
          "kg m-2 s-1", "K", "W m-2", "W m-2",  "W m-2", "W m-2", \
           "W m-2", "W m-2",  "W m-2", "W m-2", "W m-2" ]

for iv in range(0, 17):
    filevar = os.environ["DATADIR"] + "/mon/" +os.environ["CASENAME"] + "." + vvar[iv] + ".mon.nc"
###   check the units for each variables 
    data = xr.open_dataset( filevar, decode_cf=False)
    datax = data[ vvar[iv] ]
    chunit =  datax.attrs["units"] 
##    print( "variable unit check ", vvar[iv] , chunit, " ", unit[iv] )

    if( not (chunit ==  unit[iv]) ):
        print( "Warning: unit", chunit, "for variable ",  vvar[iv] )
        print( " in file : ", filevar ) 
        print( "does not match assumed unit of ",  unit[iv] ) 
        print( "please quit and check the units, or proceed with caution")
        input("Press any key to continue")

    data.close()

    if not os.path.exists(filevar):
        print ("=============================================")
        print ("===  MISSING INPUT FILE " + filevar  )
        print ("====  EXITING =================== ")
        input("Press any key to continue")
        sys.exit()

print  (" =========================================================")
print  (" ==========================================================")
print  ("===========  All model input files found =============== ")
print  ( " =========================================================")
print  (" ==========================================================")
####
