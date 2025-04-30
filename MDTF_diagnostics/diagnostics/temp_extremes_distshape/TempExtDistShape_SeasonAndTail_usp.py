# This file is part of the temp_extremes_distshape module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)
# ======================================================================
# TempExtDistShape_SeasonAndTail_usp.py
#
#   Called by TempExtDistShape_ShiftRatio.py, TempExtDistShape_FreqDist.py,
#             TempExtDistShape_CircComps.py, TempExtDistShape_Moments.py
#    Provides User-Specified Parameters for Calculations
#
#   This file is part of the Surface Temperature Extremes and Distribution Shape Package Package
#    and the MDTF code package. See LICENSE.txt for the license.
#
import json
import os

# ======================================================================
# START USER SPECIFIED SECTION
# ======================================================================
# Set range of years, season, and tail percentile threshold for calculations
yearbeg = int(os.environ["startdate"])
yearend = int(os.environ["enddate"])
monthstr = os.environ["monthstr"]
monthsub = os.environ["monthsub"]
ptile = os.environ["ptile"]

# ======================================================================
# END USER SPECIFIED SECTION
# ======================================================================
#
#
# ======================================================================
# DO NOT MODIFY CODE BELOW UNLESS
# YOU KNOW WHAT YOU ARE DOING
# ======================================================================
data = {}
data["yearbeg"] = yearbeg
data["yearend"] = yearend
data["monthsub"] = monthsub
data["monthstr"] = monthstr
data["ptile"] = ptile

# Taking care of function arguments for calculating shift ratio
data["args1"] = [
    yearbeg,
    yearend,
    monthsub,
    monthstr,
    ptile,
]
with open(os.environ["WORK_DIR"] + "TempExtDistShape_SeasonAndTail.json", "w") as outfile:
    json.dump(data, outfile)
