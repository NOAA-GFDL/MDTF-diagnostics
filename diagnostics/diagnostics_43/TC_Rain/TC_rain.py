# This file is part of the TC Rain Diagnostic POD of the MDTF code package (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# Azimuthal Average of TC Rain Rate POD
#
#   Last update: 5/27/2022
#

#
#   Version & Contact info
#
#   Last Update: 07/27/2022
#
#   - Version/revision information: version 1 (07/27/2022)
#   - PI Daehyun Kim, University of Washington, daehyun@uw.edu
#   - Developer/point of contact Nelly Emlaw, University of Washington, gnemlaw@uw.edu
#
#   Open source copyright agreement
#
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
#   Unless you've distirbuted your script elsewhere, you don't need to change this.
#
# #   Functionality

# This POD calculates and plots azimuthal averages for tropical cyclone (TC) rain rates
# from TC track data and model output precipitation.

# This POD does not pull track data from model output precip. The TC track data required
# snapshots of latitude and longitude coordinates of the center of a storm, and the date
# and time of those snapshots. An option addition are storm traits of each snapshot such
# as maximum wind, central pressure, etc through which snapshots can be filtered for
# inclusion of the azimuthal rain rate average. For the azimuthal average calculation,
# the track data is organized into the form of a dictionary:

# track_dict[date in datetime64 format][key for storm identifier, and required data
# (coordinate/wind/etc)]

# In this example code, the model output is interpolated and regridded to 0.25 x 0.25
# degree arrays and the average is calcuated from 0 to 600 km from the center of the
# storm in 25 km discrete sections. Here we only take the average of snaphots where the
# max wind speed is between 35 and 45 kt. The output of this diagnostic is a plot in the
# form of an .eps file with distance from the center of the storm along the horizonal
# average and precip rate along the vertical axis.

#
#
#
#   Required programming language and libraries
#
#   Python version 3, xarray, numpy, scipy and matplotlib.
#
#   Required model output variables
#
#   Total Precipitation
#   Model Track Output (required: storm center latitude and longitude, time of snapshot,
#   optional: max wind, central surface pressure, sst, etc)
#
#   References
#   1. Kim, D., Y. Moon, S. Camargo, A. Sobel, A. Wing, H. Murakami, G. Vecchi, M. Zhao,
#   and E. Page, 2018: Process-oriented diagnosis of tropical cyclones in high-resolution
#   climate models. J. Climate, 31, 1685–1702, https://doi.org/10.1175/JCLI-D-17-0269.1.
#
#   2. Moon, Y., D. Kim, S. Camargo, A. Wing, A. Sobel, H. Murakami, K. Reed, G. Vecchi,
#   M. Wehner, C. Zarzycki, and M. Zhao, 2020: Azimuthally averaged wind and
#   thermodynamic structures of tropical cyclones in global climate models and their
#   sensitivity to horizontal resolution. J. Climate, 33, 1575–1595,
#   https://doi.org/10.1175/JCLI-D-19-0172.1
#
#   3. Moon, Y., D. Kim, A. A. Wing, S. J. Camargo, M. Zhao, L. R. Leung, M. J. Roberts,
#   D.-H. Cha, and J. Moon: An evaluation of global climate model-simulated tropical
#   cyclone rainfall structures in the HighResMIP against the satellite observations,
#   J. Climate, Accepted.
#
#

import os
import xarray as xr  # python library we use to read netcdf files
import matplotlib.pyplot as plt  # python library we use to make plots
from scipy.interpolate import interp2d  # used to interpolate the output model data
import numpy as np

# ## 1) Loading model data files: ###############################################
#
basin = os.getenv("basin")  # specifying the basin of TC Track input data
thresh = [np.float(os.getenv("minthresh")), np.float(os.getenv("maxthresh"))]


# load precip netcdf data
pr_path = os.environ["TP_FILE"]
pr = xr.open_dataset(pr_path)

# basin regions
regions = {
    "atl": [[0, 30], [260, 350]],  # atlantic basin
    "enp": [[0, 30], [180, 280]],  # eastern central pacific basin
    "wnp": [[0, 30], [100, 180]],  # western north pacific basin
    "nin": [[0, 30], [40, 100]],  # indian ocean basin
    "sin": [[-30, 0], [30, 90]],  # south indian ocean basin
    "aus": [[-30, 0], [90, 160]],  # australian basin
    "spc": [[-30, 0], [160, 240]],  # south pacific central basin
}

# get only field of view for basin storm is in
pr_basin = pr.where(
    (
        (pr.latitude >= regions[basin][0][0])
        & (pr.latitude <= regions[basin][0][1])
        & (pr.longitude >= regions[basin][1][0])
        & (pr.longitude <= regions[basin][1][1])
    )
)

# Organizing Track Data
# This code does not have a TC tracking mechanism of its own an needs to be fed TC
# track data which includes:
# Required: snapshops of storm center coordinates (latitude, longitude),
# time of snapshot
# Optional: some means of filtering which snapshots to average over (max wind,
# central surface pressure, etc)
#
# The data is organized within the code as a dictionary of the form:
# track_dict[basin][stormID (here latlon)][keys for required and optional data]
# the example data was tracked with the ECMWF tracker and includes a small sample
# of western north pacific storm tracks from hindecast data of 2002.


track_fname_path = os.path.join(os.environ["OBS_DATA"], basin)

tracks = open(track_fname_path)

track_dict = {}

for line in tracks:
    if "SNBR" in line:  # formatting of data.
        n_snap = float(line[19:21])  # number of storm days
        start_line_num = line[0:6]
        track_dict[start_line_num] = {}
        x = 0
    if "SNBR" not in line and len(line) > 10:
        if x < n_snap:
            date = line[6:16]
            datesplit = date.split("/")
            d = datesplit[2]
            m = datesplit[1]
            y = datesplit[0]
            dt64 = (
                y + "-" + m + "-" + d + "T" + "12"
            )  # I'm setting the track date64s at 12z
            # rather than 00z where the model output says the track points are
            # are so that when we take the rain rate (accum_rain_day - accum_rain_yesterday)/24
            # the lat lon center of the storm is between the todays feild and yesterdays feild.
            lat = float(line[20:23]) / 10
            lon = float(line[23:27]) / 10
            char = float(line[29:31])
            track_dict[start_line_num][dt64] = {
                "ID": start_line_num,
                "date": date,
                "date64": dt64,
                "lat": lat,
                "lon": lon,
                "char": char,
                "index": x,
            }
            x = x + 1

#  2) Doing azimuthal average computations: #####################################################


# dist function calculates the distancing between two points on a sphere
def dist(p1, p2, radius):

    import numpy as np

    phi1 = p1[0]
    phi2 = p2[0]
    lam1 = p1[1]
    lam2 = p2[1]

    sins = (np.sin((phi2 - phi1) / 2)) ** 2
    coscossin = np.cos(phi1) * np.cos(phi2) * (np.sin((lam2 - lam1) / 2) ** 2)

    d = 2 * np.arcsin((sins + coscossin) ** 0.5)
    dis = d * radius
    return dis


# list of all snapshot averages
allazaverages = []
# list of snapshot averages which meet the threshold characteristic
azaverage_plot = []


for storm in track_dict:
    for snapshot in track_dict[storm]:
        index = track_dict[storm][snapshot]["index"]
        if index == 0:  # getting initial snapshot for calculating rain rate for storm
            initial_Z = pr_basin.sel(time=snapshot)
            initial_Z = initial_Z.tp
        if index > 0:
            # storm center
            latitude = track_dict[storm][snapshot]["lat"]
            longitude = track_dict[storm][snapshot]["lon"]
            # calculating rain rate
            Z = pr.sel(time=snapshot)
            Z = Z["tp"]
            Z_anom = Z - initial_Z
            Z_anom = Z_anom / 24
            # interpdataset
            latrange = pr_basin.latitude.values
            lonrange = pr_basin.longitude.values
            x = lonrange
            y = latrange
            interp_pr_basin = interp2d(x, y, Z_anom, kind="cubic")
            lonnew = np.arange(regions[basin][0][1], regions[basin][1][1], 0.25)
            latnew = np.arange(regions[basin][0][0], regions[basin][0][1], 0.25)
            pr_basin25 = interp_pr_basin(lonnew, latnew)

            initial_Z = (
                Z  # updating intial accumulated rate to calculate next snaps rain rate
            )

            # putting together new rainrate dataset
            ds_pr_rate_snap = xr.Dataset(
                data_vars=dict(p_r=(["lat", "lon"], pr_basin25)),
                coords=dict(lon=(["lon"], lonnew), lat=(["lat"], latnew),),
                attrs=dict(description="precip rate for snapshot"),
            )

            # get azimuthals
            az_avrs = []
            r_dists = [
                [0, 25, 12.5],
                [25, 50, 37.5],
                [50, 75, 62.5],
                [75, 100, 87.5],
                [100, 125, 112.5],
                [125, 150, 137.5],
                [150, 175, 162.5],
                [175, 200, 187.5],
                [200, 225, 212.5],
                [225, 250, 237.5],
                [250, 275, 262.5],
                [275, 300, 287.5],
                [300, 325, 312.5],
                [325, 350, 337.5],
                [350, 375, 362.5],
                [375, 400, 387.5],
                [400, 425, 412.5],
                [425, 450, 437.5],
                [450, 475, 462.5],
                [475, 500, 487.5],
                [500, 525, 512.5],
                [525, 550, 537.5],  # over
                [550, 575, 562.5],
                [575, 600, 587.5],
            ]

            storm_center_rad = (
                np.deg2rad(longitude),
                np.deg2rad(latitude),
            )  # center of storm in radians

            pr_rates = {}

            for r in r_dists:
                pr_rates[r[2]] = []

            # calculate azimuthal average for each discrete radius
            for lat_vals in ds_pr_rate_snap["p_r"]:  # going over each latitude value
                for lon_val in lat_vals:  # each longitude
                    r_latitude = lon_val["lat"].values
                    r_longitude = lon_val["lon"].values
                    pr_rate = lon_val.values  # rainrate at that lat lon
                    r_radians = [
                        np.deg2rad(r_longitude),
                        np.deg2rad(r_latitude),
                    ]  # lat lon in radians
                    d = dist(storm_center_rad, r_radians, 6371000 / 1000)
                    for r in r_dists:
                        if (
                            d >= r[0] and d <= r[1]
                        ):  # if distance matches discrete radius values in
                            # list add to list
                            pr_rates[r[2]].append(pr_rate)
            azavs = []

            for r in r_dists:
                azav_r = np.nanmean(pr_rates[r[2]])
                azavs.append(azav_r)

            allazaverages.append(azavs)

            char = latitude = track_dict[storm][snapshot]["char"]
            if char >= thresh[0] and char <= thresh[1]:
                azaverage_plot.append(azavs)


#  3) plotting and saving output: #####################################################

r = [
    12.5,
    37.5,
    62.5,
    87.5,
    112.5,
    137.5,
    162.5,
    187.5,
    212.5,
    237.5,
    262.5,
    287.5,
    312.4,
    337.5,
    362.5,
    387.5,
    412.5,
    437.5,
    462.5,
    487.5,
    512.5,
    537.5,
    562.5,
    587.5,
]

fig = plt.figure(num=None, figsize=(12, 8))
plt.scatter(r, np.nanmean(azaverage_plot, axis=0))
ymax = max(np.nanmean(azaverage_plot, axis=0)) + 1
plt.ylim(0, ymax)
plt.title("Azimuthal Average of Rain Rate (kg m**-2)", fontdict={"fontsize": 16})
plt.xlabel("Distrace From Storm Center (km)", fontsize=16)
plt.ylabel("Rain Rate (kg m**-2)", fontsize=16)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)


fname = "azimuthalaverage.eps"

output_fname = os.path.join(os.environ.get("WORK_DIR"), "model", "PS", fname)

plt.savefig(output_fname, format="eps")


#
# ### 8) Confirm POD executed sucessfully ########################################
print("Finished successfully! Azimuthal average plot eps file in working directory.")
