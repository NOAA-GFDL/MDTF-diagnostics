# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# ObsSubset.py
#
#   Subset input observational data
#    as part of functionality provided by
#   Surface Temperature Extremes and Distribution Shape Package (temp_extremes_distshape.py)
#
#   Version 1 07-Jul-2020 Arielle J. Catalano (PSU)
#   PI: J. David Neelin (UCLA; neelin@atmos.ucla.edu)
#   Science lead: Paul C. Loikith (PSU; ploikith@pdx.edu)
#   Current developer: Arielle J. Catalano (PSU; a.j.catalano@pdx.edu)
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape Package
#    and the MDTF code package. See LICENSE.txt for the license.
#
#   Subsets input observational netcdf data to seasonal temperature distribution moment text files, seasonal shift ratio text files for both sides of the temperature distribution, and seasonal netcdf files
#
#   Depends on the following scripts:
#    (1) ObsSubset_usp.py
#    (2) TempExtDistShape_Moments_util.py
#        Including functions: Region_Mask, and Seasonal_Moments
#    (3) TempExtDistShape_ShiftRatio_util.py
#        Including functions: Seasonal_Anomalies, and ShiftRatio_Calc
#    (4) Seasonal_NCfile.sh
#
# ======================================================================
# Import standard Python packages
import glob
import json
import os
import numpy
import subprocess

# Import Python functions specific to Non-Gaussian to Gaussian Shift Ratio
from TempExtDistShape_Moments_util import Region_Mask
from TempExtDistShape_Moments_util import Seasonal_Moments
from TempExtDistShape_ShiftRatio_util import Seasonal_Anomalies
from TempExtDistShape_ShiftRatio_util import ShiftRatio_Calc

print("**************************************************")
print("Executing Observations Subset (ObsSubset.py)......")
print("**************************************************")

# ======================================================================
### Subset netcdf files to summer and winter seasons
subprocess.call(['./Seasonal_NCfile.sh'])

# ======================================================================
### Load user-specified parameters
print(("Load user-specified parameters..."), end=' ')
os.system("python "+os.environ["POD_HOME"]+"/ObsSubset_usp.py")
with open(os.environ["WK_DIR"]+"/ObsSubset_parameters.json") as outfile:
    sub_data=json.load(outfile)
print("...Loaded!")

# ======================================================================
### List model filenames for two-meter temperature data
T2Mfile=sorted(glob.glob(sub_data["MODEL_OUTPUT_DIR"]+"/"+sub_data["MODEL"]+"*"+sub_data["T2M_VAR"]+".day.nc"))[0]

# ======================================================================
### Subset Data for Seasonal Temperature Moments to Text Files
# ----  Generate a map of values corresponding to land regions only by masking
msk=Region_Mask(sub_data["REGION_MASK_DIR"]+'/'+sub_data["REGION_MASK_FILENAME"],T2Mfile,sub_data["LON_VAR"],sub_data["LAT_VAR"])

# ======================================================================
### Loop over each season
for seasind in range(len(sub_data["monthsubs"])):
    # ---- Calculate seasonal moments using two-meter temperature
    seas_mean,seas_std,seas_skew,lon,lat=Seasonal_Moments(T2Mfile,sub_data["LON_VAR"],sub_data["LAT_VAR"],sub_data["T2M_VAR"],sub_data["TIME_VAR"],sub_data["monthsubs"][seasind],sub_data["yearbeg"],sub_data["yearend"],msk)

    # ---- Save out each moment as text file
    numpy.savetxt(sub_data["MODEL_OUTPUT_DIR"]+'/'+sub_data['MODEL']+'_moments_mean_'+sub_data["monthstrs"][seasind]+'.txt', seas_mean)
    numpy.savetxt(sub_data["MODEL_OUTPUT_DIR"]+'/'+sub_data['MODEL']+'_moments_std_'+sub_data["monthstrs"][seasind]+'.txt', seas_std)
    numpy.savetxt(sub_data["MODEL_OUTPUT_DIR"]+'/'+sub_data['MODEL']+'_moments_skew_'+sub_data["monthstrs"][seasind]+'.txt', seas_skew)

    # ======================================================================
    # ---- Calculate two-meter temperature anomaly
    T2Manom_data,lon,lat=Seasonal_Anomalies(T2Mfile,sub_data["LON_VAR"],sub_data["LAT_VAR"],sub_data["T2M_VAR"],sub_data["TIME_VAR"],sub_data["monthsubs"][seasind],sub_data["yearbeg"],sub_data["yearend"])

    ### Loop over each distribution tail
    for ptileval in sub_data["ptiles"]:
        # ---- Calculate underlying-to-Gaussian distribution shift ratio
        shiftratio=ShiftRatio_Calc(ptileval,sub_data["shift"],msk,T2Manom_data,lon,lat)
        numpy.savetxt(sub_data["MODEL_OUTPUT_DIR"]+'/'+sub_data['MODEL']+'_shiftratio_'+sub_data["monthstrs"][seasind]+'_'+str(ptileval)+'th-ptile.txt', seas_skew)

### Save out latitude/longitude values
numpy.savetxt(sub_data["MODEL_OUTPUT_DIR"]+'/'+sub_data['MODEL']+'_global_lons.txt',lon)
numpy.savetxt(sub_data["MODEL_OUTPUT_DIR"]+'/'+sub_data['MODEL']+'_global_lats.txt',lat)
