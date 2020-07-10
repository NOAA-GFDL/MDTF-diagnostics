# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# temp_extremes_distshape.py
#
#   Surface Temperature Extremes and Distribution Shape Diagnostic Package
#
#   Version 1 07-Jul-2020 Arielle J. Catalano (PSU)
#   PI: J. David Neelin (UCLA; neelin@atmos.ucla.edu)
#   Science lead: Paul C. Loikith (PSU; ploikith@pdx.edu)
#   Current developer: Arielle J. Catalano (PSU; a.j.catalano@pdx.edu)
#
#   This package and the MDTF code package are distributed under the LGPLv3 license (see LICENSE.txt)
#
#   Currently consists of following functionalities:
#   (1) Moments of Surface Temperature Probability Distribution (TempExtDistShape_Moments.py)
#   (2) Shifted Underlying-to-Gaussian Distribution Tail Exceedances Ratio (TempExtDistShape_ShiftRatio.py)
#   (3) Frequency Distributions at Non-Gaussian Tail locations (TempExtDistShape_FreqDist.py)
#   (4) Composite Circulation at Non-Gaussian Tail locations (TempExtDistShape_CircComps.py)
#
#   As a module of the MDTF code package, all scripts of this package can be found under /diagnostics/temp_extremes_distshape/**
#   and observational data under /inputdata/obs_data/temp_extremes_distshape/**
#
#   This package is written in Python 3, and requires the following Python packages:
#    os,json,numpy,scipy,matplotlib,mpl_toolkits,h5py,netcdf4,netcdftime,cftime,cartopy
#   Use Anaconda:
#    These Python packages are already included in the standard installation
#
#   The following 3-D (lat-lon-time) model fields at a daily resolution are required:
#    (1) Two-meter temperature (units: K or degrees C)
#    (2) Sea level pressure (units: hPa or Pa)
#    (3) Geopotential height (units: m)
#
#   References:
#    Catalano, A. J., P. C. Loikith, and J. D. Neelin, 2020: Evaluating CMIP6
#      model fidelity at simulating non-Gaussian temperature distribution tails.
#      Environ. Res. Lett., https://doi.org/10.1088/1748-9326/ab8cd0
#    Loikith, P. C., and J. D. Neelin, 2019: Non-Gaussian cold-side temperature
#      distribution tails and associated synoptic meteorology. J. Climate, 32,
#      8399-8414, https://doi.org/10.1175/JCLI-D-19-0344.1.
#    Loikith, P. C., J. D. Neelin, J. Meyerson, and J. S. Hunter (2018): Short
#      warm-side temperature distribution tails drive hot spots of warm temperature
#      extreme increases under near-future warming. J. Climate, 31, 9469-9487,
#      doi:10.1175/JCLI-D-17-0878.1.
#    Loiktih, P. C., and J. D. Neelin (2015): Short-tailed temperature distributions
#      over North America and implications for future changes in extremes,
#      Geophys. Res. Lett., 42, 8577-8585, doi:10.1002/2015GL065602.
#    Ruff, T. W., and J. D. Neelin (2012): Long tails in regional surface temperature
#      probability distributions with implications for extremes under global
#      warming. Geophys. Res. Lett., 39, L04704, doi:10.1029/2011GL050610.
#
# ======================================================================
# Import standard Python packages
import os
import glob

##### Functionalities in Surface Temperature Extremes and Distribution Shape Package #####

## ======================================================================
##  Moments of Surface Temperature Probability Distribution
##  See TempExtDistShape_Moments.py for detailed info
try:
    os.system("python "+os.environ["POD_HOME"]+"/TempExtDistShape_Moments.py")
except OSError as e:
    print(('WARNING',e.errno,e.strerror))
    print("**************************************************")
    print("Moments of Surface Temperature Probability Distribution (TempExtDistShape_Moments.py) is NOT Executed as Expected!")		
    print("**************************************************")

## ======================================================================
##  Shifted Underlying-to-Gaussian Distribution Tail Exceedances Ratio 
##  See TempExtDistShape_ShiftRatio.py for detailed info
try:
    os.system("python "+os.environ["POD_HOME"]+"/TempExtDistShape_ShiftRatio.py")
except OSError as e:
    print(('WARNING',e.errno,e.strerror))
    print("**************************************************")
    print("Shifted Underlying-to-Gaussian Distribution Tail Exceedances ratio (TempExtDistShape_ShiftRatio.py) is NOT Executed as Expected!")		
    print("**************************************************")

## ======================================================================
##  Frequency Distributions at Non-Gaussian Tail Locations
##  See TempExtDistShape_FreqDist.py for detailed info
try:
    os.system("python "+os.environ["POD_HOME"]+"/TempExtDistShape_FreqDist.py")
except OSError as e:
    print(('WARNING',e.errno,e.strerror))
    print("**************************************************")
    print("Frequency Distributions at Non-Gaussian Tail Locations (TempExtDistShape_FreqDist.py) is NOT Executed as Expected!")
    print("**************************************************")

## ======================================================================
##  Composite Circulation at Non-Gaussian Tail Locations
##  See TempExtDistShape_CircComps.py for detailed info
try:
    os.system("python "+os.environ["POD_HOME"]+"/TempExtDistShape_CircComps.py")
except OSError as e:
    print(('WARNING',e.errno,e.strerror))
    print("**************************************************")
    print("Composite Circulation at Non-Gaussian Tail Locations (TempExtDistShape_CircComps.py) is NOT Executed as Expected!")
    print("**************************************************")

print("**************************************************")
print("Surface Temperature Extremes and Distribution Shape Package (TempExtDistShape.py) Executed!")
print("**************************************************")
