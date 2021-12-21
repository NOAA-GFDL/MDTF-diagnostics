
import os
import sys

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

# check the input data in COMPOSITE/model directories
# 3D variables
vvar = ["zg", "ua", " va", "ta", " hus", "wap", "pr", "ts", "hfls", "hfss", "lw", "sw"]
mode = ["ELNINO", "LANINA"]
wkdir = os.environ["WK_DIR"]

# check for missing files
for iv in range(0, len(vvar)):
    for n in range(0, len(mode)):
        dirpath = os.path.join(wkdir, "COMPOSITE/model/netCDF", mode[n])
        try:
            os.path.exists(dirpath)
        except IsADirectoryError:
            print("Directory", dirpath, "does not exist")
            sys.exit(1)
        filevar = os.path.join(dirpath, vvar[iv] + ".nc")
        try:
            os.path.exists(filevar)
        except FileExistsError:
            print("===  MISSING INPUT FILE ", filevar)
            print("====  EXITING ====")
            sys.exit(1)

    filevarclim = os.path.join(wkdir, "COMPOSITE/model/netCDF", vvar[iv] + "_clim.nc")
    try:
        os.path.exists(filevarclim)
    except FileExistsError:
        print("===  MISSING INPUT FILE ", filevarclim)
        print("====  EXITING ==== ")
        sys.exit(1)

print(" =========================================================")
print(" ==========================================================")
print("===  All model input files required for MSE computation found ===")
print(" =========================================================")
print(" ==========================================================")

