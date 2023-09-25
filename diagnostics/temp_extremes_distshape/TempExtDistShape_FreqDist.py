# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_FreqDist.py
#
#   Frequency Distributions at Non-Gaussian Tail Locations
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
#   Computes the Gaussian distribution fit to the histogram of seasonal two-meter temperature anomalies at specified locations following Loikith and Neelin (2019), Loikith et al. (2018), Loikith and Neelin (2015), Ruff and Neelin (2012)
#
#   Generates plot of the distribution and associated Gaussian fit over season specified as function of two-meter temperature
#
#   Depends on the following scripts:
#    (1) TempExtDistShape_FreqDist_usp.py
#    (2) TempExtDistShape_FreqDist_util.py
#
#   Defaults for locations, seasons, etc. that can be altered by user are in TempExtDistShape_FreqDist_usp.py
#
#   Utility functions are defined in TempExtDistShape_FreqDist_util.py
#
# ======================================================================
# Import standard Python packages
import glob
import os
import json
import matplotlib.pyplot as mplt
import numpy

# Import Python functions specific to Non-Gaussian Frequency Distributions
from TempExtDistShape_FreqDist_util import Seasonal_Anomalies
from TempExtDistShape_FreqDist_util import Gaussfit_Params
from TempExtDistShape_FreqDist_util import Gaussfit_Est
from TempExtDistShape_FreqDist_util import Gaussfit_Plot

print("**************************************************")
print("Executing Frequency Distributions at Non-Gaussian Tail Locations (TempExtDistShape_FreqDist.py)......")
print("**************************************************")

# ======================================================================
### Load user-specified parameters (usp) for calcluating and plotting shift ratio

print("Load user-specified parameters including season...")
os.system("python "+os.environ["POD_HOME"]+"/TempExtDistShape_FreqDist_usp.py")
with open(os.environ["WK_DIR"]+"/TempExtDistShape_FreqDist_parameters.json") as outfile:
    freq_data=json.load(outfile)
print("...Loaded!")

# ======================================================================
### List model filenames for two-meter temperature
T2Mfile=sorted(glob.glob(freq_data["MODEL_OUTPUT_DIR"]+"/"+freq_data["MODEL"]+"*"+freq_data["T2M_VAR"]+".day.nc"))[0]

# ======================================================================
### Estimate and plot Gaussian fit to two-meter temperature distribution at specified locations, save figure in wkdir/TempExtDistShape/
# -----  Set figure prior to looping over each city and adding to each subplot
# -----  Large subplot 111 added to display overall x and y labels properly in plotting
fig = mplt.figure(figsize=(9,10))
ax_lg = fig.add_subplot(111)
for statind in numpy.arange(0,len(freq_data["citynames"])):

    # ======================================================================
    ### Calculate seasonal anomalies for two-meter temperature
    Tanom_data,lon,lat=Seasonal_Anomalies(T2Mfile,freq_data["LON_VAR"],freq_data["LAT_VAR"],freq_data["T2M_VAR"],freq_data["TIME_VAR"],freq_data["monthsub"],freq_data["yearbeg"],freq_data["yearend"],statind)

    # ======================================================================
    ### Estimate Gaussian fit to two-meter temperature distribution at specified location
    bin_centers_gauss,bin_centers,bin_counts,gauss_fit,Tanom_stat=Gaussfit_Est(Tanom_data,lat,lon,statind,freq_data["statlats"],freq_data["statlons"],freq_data["citynames"],freq_data["binwidth"])

    # ======================================================================
    ### Plot two-meter temperature distribution and estimated Gaussian fit computed above at specified location, save to wkdir/TempExtDistShape
    Gaussfit_Plot(fig,bin_centers,bin_counts,bin_centers_gauss,gauss_fit,Tanom_stat,freq_data["ptile"],freq_data["citynames"],freq_data["monthstr"],statind,freq_data["plotrows"],freq_data["plotcols"])

### Turn off axis lines and ticks of the big subplot and set x & y labels
ax_lg.spines['top'].set_color('none')
ax_lg.spines['bottom'].set_color('none')
ax_lg.spines['left'].set_color('none')
ax_lg.spines['right'].set_color('none')
ax_lg.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
ax_lg.set_ylabel('Normalized Frequency',fontsize=14,labelpad=30)
ax_lg.set_xlabel('Temperature Anomaly ('+u"\u00b0"+'C)',fontsize=14,labelpad=16)

### Format subplot spacing
fig.subplots_adjust(wspace=0.2, hspace=0.25)

### Save figure to PDF
fig.savefig(freq_data["FIG_OUTPUT_DIR"]+"/"+freq_data["FIG_OUTPUT_FILENAME"],bbox_inches='tight')
print("      Figure saved as "+freq_data["FIG_OUTPUT_DIR"]+'/'+freq_data["FIG_OUTPUT_FILENAME"]+"!")

# ======================================================================

print("**************************************************")
print("Frequency Distributions at Non-Gaussian Tail Locations (TempExtDistShape_FreqDist.py) Executed!")
print("**************************************************")
