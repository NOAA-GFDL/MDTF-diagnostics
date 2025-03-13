
import os
import sys
import os.path


import xarray as xr

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)


###   
###  check  the input data in inputdata/model  directories DATADIR + mon
## 3D + 2D 
size = 7

vvar = [ "zg", "ua", "va", "ta", "wap", "pr", "ts" ]

## check for missing files and mismatched units 

unit = [ "m", "m s-1", "m s-1", "K", "Pa s-1",  \
          "kg m-2 s-1", "K" ]

for iv in range(0, size):
    filevar = os.path.join(os.environ["DATADIR"] + "/mon/" +os.environ["CASENAME"] + "." + vvar[iv] + ".mon.nc")
###   check the units for each variables 
    data = xr.open_dataset( filevar, decode_cf=False)
    datax = data[ vvar[iv] ]
    chunit =  datax.attrs["units"] 

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
