import sys
import os.path
shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

import xarray as xr

# check  the input data in inputdata/model  directories DATADIR + mon
# 3D

vvar = ["zg", "ua", "va",  "ta", "hus", "wap", "pr", "ts", "hfss", \
        "hfls", "rsus", "rsds", \
        "rsdt", "rsut", "rlus", \
        "rlds", "rlut"]

size = len(vvar)

# check for missing files and mismatched units

unit = ["m", "m s-1", "m s-1", "K", "1", "Pa s-1",\
        "kg m-2 s-1", "K", "W m-2", "W m-2",  "W m-2", "W m-2",\
        "W m-2", "W m-2",  "W m-2", "W m-2", "W m-2"]

for iv in range(0, size):
    filevar = os.path.join(os.environ["DATADIR"], "mon", os.environ["CASENAME"] + "." + vvar[iv] + ".mon.nc")
    try:
        os.path.isfile(filevar)
    except FileExistsError:
        print("===  MISSING INPUT FILE ", filevar)
        print("====  EXITING =================== ")
        sys.exit(1)

# check the units for each variable
    data = xr.open_dataset(filevar, decode_cf=False)
    datax = data[vvar[iv]]
    chunit = datax.attrs["units"]

    data.close()
    if not chunit == unit[iv]:
        print("Warning: unit", chunit, "for variable ",  vvar[iv])
        print(" in file : ", filevar)
        print("does not match assumed unit of ",  unit[iv])
        print("please quit and check the units, or proceed with caution")

print(" =========================================================")
print("====== All model input files found for COMPOSITE calculation =======")
print(" =========================================================")

