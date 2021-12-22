import sys
import os

#  check  the input data in inputdata/model  directories  required for SCATTER routine
shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)

wkdir = os.environ["ENSO_MSE_WKDIR"]
vardir = os.environ["POD_HOME"]
obsdata = os.environ["OBS_DATA"] 

# Create output directories if they do not exist
scatdir = os.path.join(wkdir, "SCATTER")
if not os.path.exists(scatdir):
    print("Creating directory", scatdir)
    os.makedirs(scatdir)

ncdir = os.path.join(wkdir, "SCATTER/netCDF")
if not os.path.exists(ncdir):
    print("Creating directory",ncdir)
    os.makedirs(ncdir)
try:
    os.path.exists(ncdir)
except FileExistsError:
    print("Directory", ncdir, "does not exist")

psdir = os.path.join(wkdir, "SCATTER/PS")
if not os.path.exists(wkdir + "/SCATTER/PS"):
    print("Creating directory", psdir)
    os.makedirs(psdir)

try:
    os.path.exists(psdir)
except FileExistsError:
    print("Directory", psdir, "does not exist")

#  copy pre-calculated scatter data to working directory from inputdata/obs_data/SCATTER
dest = ncdir
namein1 = os.path.join(obsdata, "SCATTER/central_pacific_MSE_terms.txt")
namein2 = os.path.join(obsdata, "SCATTER/eastern_pacific_MSE_terms.txt")
namein3 = os.path.join(vardir, "SCATTER/list-models-historical-obs")

os.system('cp ' + namein1 + ' ' + dest)
os.system('cp ' + namein2 + ' ' + dest)
os.system('cp ' + namein3 + ' ' + dest)

# check for input model data
namedest1 = os.path.join(dest, "central_pacific_MSE_terms.txt")
try:
    os.path.exists(namedest1)
except FileExistsError:
    print("=============================================")
    print("===  MISSING FILE for SCATTER  =====")
    print(namedest1)
    sys.exit(1)

namedest2 = os.path.join(dest, "eastern_pacific_MSE_terms.txt")
try:
    os.path.exists(namedest2)
except FileExistsError:
    print("=============================================")
    print("===  MISSING FILE for SCATTER  =====")
    print(namedest2)
    sys.exit(1)

print("=============================================")
print(" SCATTER input file check COMPLETED  ")
print("=============================================")

