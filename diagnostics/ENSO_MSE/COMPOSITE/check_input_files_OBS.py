import os
import sys

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

# check the input data in inputdata/obs_data directories DATADIR  pre-digested data
# 3D
vvar = ["zg", "ua", "va", "ta", "hus", "wap", "pr", "ts", "hfss", "hfls", "lw", "sw", "frad"]

# check for missing files

mode = ["ELNINO", "LANINA"]

for n in range(0, len(mode)):
    for iv in range(0, len(vvar)):
        filevar = os.environ["OBS_DATA"] + "/DATA/netCDF/" + mode[n] + "/" + vvar[iv] + ".nc"
        try:
            os.path.exists(filevar)
        except FileExistsError:
            print("===  MISSING  PRE-DIGESTED OBSERVATIONAL DATA FILE " + filevar)
            print("====  EXITING =================== ")
            sys.exit(1)

        filevarobs = os.environ["OBS_DATA"] + "/DATA/netCDF/" + vvar[iv] + "_clim.nc"
        try:
            os.path.exists(filevarobs)
        except FileExistsError:
            print("===  MISSING  PRE-DIGESTED OBSERVATIONAL DATA FILE " + filevarobs)
            print("====  EXITING =====")
            sys.exit(1)

# Search for CORR and REGRESS files
mode = ["CORR", "REGRESS"]
vvar = ["pr", "hfss", "hfls", "sw", "lw"]

for n in range(0, len(mode)):
    for iv in range(0, len(vvar)):
        filevar = os.environ["OBS_DATA"] + "/DATA/netCDF/" + mode[n] + "_" + vvar[iv] + ".nc"
        try:
            os.path.exists(filevar)
        except FileExistsError:
            print("===  MISSING  PRE-DIGESTED OBSERVATIONAL DATA FILE " + filevar)
            print("====  EXITING =================== ")
            sys.exit(1)

print(" ==== All Pre-digested Observational files found for COMPOSITE calculations ===== ")
