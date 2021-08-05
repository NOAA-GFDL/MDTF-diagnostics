# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_CircComps.py
#
#   Composite Circulation at Non-Gaussian Tail Locations
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
#   Composites the seasonal circulation patterns associated with days in Non-Gaussian distribution tails at specified locations, following Loikith and Neelin (2019), Loikith et al. (2018), Loikith and Neelin (2015), Ruff and Neelin (2012)
#
#   Generates spatial plot of seasonal composites at lag times to days identified as function of two-meter temperature, sea level pressure, and 500hPa geopotential height
#
#   Depends on the following scripts:
#    (1) TempExtDistShape_CircComps_usp.py
#    (2) TempExtDistShape_CircComps_util.py
#
#   Defaults for location, plotting parameters,  etc. that can be altered by user are in TempExtDistShape_CircComps_usp.py
#   Defaults for season, tail percentile threshold, range of years, etc. that can be altered by user, are in TempExtDistShape_SeasonAndTail_usp.py
#
#   Utility functions are defined in TempExtDistShape_CircComps_util.py
#
# ======================================================================
# Import standard Python packages
import glob
import os
import json
import matplotlib.pyplot as mplt
import numpy
import cartopy.crs as ccrs

# Import Python functions specific to Non-Gaussian Circulation Composites
from TempExtDistShape_CircComps_util import Seasonal_Subset
from TempExtDistShape_CircComps_util import Variable_Anomaly
from TempExtDistShape_CircComps_util import Labfunc
from TempExtDistShape_CircComps_util import Circ_Comp_Lags
from TempExtDistShape_CircComps_util import Plot_Circ_Comp_Lags
from TempExtDistShape_CircComps_util import Set_Colorbars
from TempExtDistShape_CircComps_util import Lag_Correct

print("**************************************************")
print("Executing Non-Gaussian Tails Circulation Composites (TempExtDistShape_CircComps.py)......")
print("**************************************************")

# ======================================================================
### Load user-specified parameters (usp) for calcluating and plotting shift ratio

print("Load user-specified parameters...")
os.system("python "+os.environ["POD_HOME"]+"/TempExtDistShape_CircComps_usp.py")
with open(os.environ["WK_DIR"]+"/TempExtDistShape_CircComps_parameters.json") as outfile:
    circ_data=json.load(outfile)
print("...Loaded!")
monthsub=json.loads(circ_data["monthsub"]) #change unicode string into array of integers

# ======================================================================
### List model filenames based on variable of interest
T2Mfile=sorted(glob.glob(circ_data["MODEL_OUTPUT_DIR"]+"/"+circ_data["MODEL"]+"*"+circ_data["T2M_VAR"]+".day.nc"))[0]
SLPfile=sorted(glob.glob(circ_data["MODEL_OUTPUT_DIR"]+"/"+circ_data["MODEL"]+"*"+circ_data["SLP_VAR"]+".day.nc"))[0]
Z500file=sorted(glob.glob(circ_data["MODEL_OUTPUT_DIR"]+"/"+circ_data["MODEL"]+"*"+circ_data["Z500_VAR"]+".day.nc"))[0]

# ======================================================================
### Calculate seasonal subset for each variable and rename from original file
T2M_data,lon,lat,datearrstr,T2M_units=Seasonal_Subset(T2Mfile,circ_data["LON_VAR"],circ_data["LAT_VAR"],circ_data["T2M_VAR"],circ_data["TIME_VAR"],monthsub,circ_data["yearbeg"],circ_data["yearend"])
T2M_VAR='T2M'
SLP_data,lon,lat,datearrstr,SLP_units=Seasonal_Subset(SLPfile,circ_data["LON_VAR"],circ_data["LAT_VAR"],circ_data["SLP_VAR"],circ_data["TIME_VAR"],monthsub,circ_data["yearbeg"],circ_data["yearend"])
SLP_VAR='SLP'
Z500_data,lon,lat,datearrstr,Z500_units=Seasonal_Subset(Z500file,circ_data["LON_VAR"],circ_data["LAT_VAR"],circ_data["Z500_VAR"],circ_data["TIME_VAR"],monthsub,circ_data["yearbeg"],circ_data["yearend"])
Z500_VAR='Z500'

# ======================================================================
### Calculate variable anomalies for temperature and 500hPa geopotential height
T2Manom_data=Variable_Anomaly(T2M_data,lon,lat,datearrstr)
Z500anom_data=Variable_Anomaly(Z500_data,lon,lat,datearrstr)

# ======================================================================
### Composite seasonal circulation at specified location for lag times to days in the non-Gaussian distribution tail
tail_days_lags,statlonind,statlatind,T2M_data,SLP_data,Z500_data,Z500_units,SLP_units,T2M_units=Circ_Comp_Lags(T2Manom_data,T2M_data,T2M_units,SLP_data,SLP_units,Z500_data,Z500_units,lat,lon,circ_data["ptile"],circ_data["statlat"],circ_data["statlon"],circ_data["lagtot"],circ_data["lagstep"])

# ======================================================================
### Plot seasonal circulation at specified location for lag times to days in the non-Gaussian distribution tail
# -----  values 0,1,2 specify columns of plot for temperature, sea level pressure, and geopotential height, respectively
# -----  sea level pressure panels do not include anomalies, so zeroes are passed to the function where applicable
print("Plotting Circulation Composites...")
fig, axes = mplt.subplots(len(numpy.arange(0,circ_data["lagtot"]+circ_data["lagstep"],circ_data["lagstep"])), 3, sharex='all',figsize=(30,15),subplot_kw=dict(projection=ccrs.PlateCarree(central_longitude=lon[statlonind])))
subplotnum=1
for lag in numpy.arange(0,circ_data["lagtot"]+circ_data["lagstep"],circ_data["lagstep"]):
    figstep=lag//2

    ### Correct for lags outside season
    newtailinds=Lag_Correct(lag,figstep,tail_days_lags,datearrstr,circ_data["lagstep"],monthsub)
    col1=Plot_Circ_Comp_Lags(T2Mfile,circ_data["LON_VAR"],figstep,0,lon,lat,newtailinds,T2M_data,T2Manom_data,T2M_VAR,circ_data["Tminval"],circ_data["Tmaxval"],circ_data["Trangestep"],lag,circ_data["Tanomminval"],circ_data["Tanommaxval"],circ_data["Tanomrangestep"],statlonind,statlatind,axes,fig)
    col2=Plot_Circ_Comp_Lags(SLPfile,circ_data["LON_VAR"],figstep,1,lon,lat,newtailinds,SLP_data,0,SLP_VAR,circ_data["SLPminval"],circ_data["SLPmaxval"],circ_data["SLPrangestep"],lag,0,0,0,statlonind,statlatind,axes,fig)
    col3=Plot_Circ_Comp_Lags(Z500file,circ_data["LON_VAR"],figstep,2,lon,lat,newtailinds,Z500_data,Z500anom_data,Z500_VAR,circ_data["Z500minval"],circ_data["Z500maxval"],circ_data["Z500rangestep"],lag,circ_data["Z500anomminval"],circ_data["Z500anommaxval"],circ_data["Z500anomrangestep"],statlonind,statlatind,axes,fig)

### Format colorbars
Set_Colorbars(circ_data["Tminval"],circ_data["Tmaxval"],circ_data["Tcbarstep"],col1,circ_data["lagtot"]//2,0,T2M_units,axes,fig)
Set_Colorbars(circ_data["SLPminval"],circ_data["SLPmaxval"],circ_data["SLPcbarstep"],col2,circ_data["lagtot"]//2,1,SLP_units,axes,fig)
Set_Colorbars(circ_data["Z500minval"],circ_data["Z500maxval"],circ_data["Z500cbarstep"],col3,circ_data["lagtot"]//2,2,Z500_units,axes,fig)

### Format subplot spacing
fig.subplots_adjust(wspace=0.06, hspace=0.02)

### Save figure to png
fig.savefig(circ_data["FIG_OUTPUT_DIR"]+"/"+circ_data["FIG_OUTPUT_FILENAME"],bbox_inches='tight')

print("...Completed!")
print("      Figure saved as "+circ_data["FIG_OUTPUT_DIR"]+"/"+circ_data["FIG_OUTPUT_FILENAME"]+"!")

# ======================================================================

print("**************************************************")
print("Non-Gaussian Tail Circulation Composites (TempExtDistShape_CircComps.py) Executed!")
print("**************************************************")
