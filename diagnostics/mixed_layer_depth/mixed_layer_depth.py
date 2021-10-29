# This file is part of the Mixed Layer Depth Diagnostic POD of the MDTF code package
# (see mdtf/MDTF-diagnostics/LICENSE.txt)
#
# This POD computes mixed layer depth from CMIP6 monthly temperature and salinity. Mixed layer depth computed from
# the EN4 reanalysis temperature and salinity is included to compare with models
#
# These figures show the mixed layer depth climatology for each month. Note that the
# colorbar varies between subplots. Users may wish to modify this.


#   Last update: 1/25/2021
#
#   - Version/revision information: version 1 (1/31/2021)
#   - PI Cecilia Bitz, University of Washington bitz@uw.edu
#   - Developer/point Lettie Roach and Cecilia Bitz
#   - Lettie Roach, University of Washington, lroach@uw.edu
#
#   Open source copyright agreement
#
#   The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).
#   Unless you've distirbuted your script elsewhere, you don't need to change this.
#
#   Functionality
#
#   Code to compute mixed layer depth from density and temperature ocean ouput
#   Displays mean of 5 years of data
#
#
#   Required programming language and libraries
#
#      Python3
#
#   Required model output variables
#
#     3D potential temperature thetao
#     3D salinity so
#     Both on depth levels (in metres)
#
#   References
#
#      Roach, L.A. and Co-authors, 2021: Process-oriented evaluation of Sea Ice
#         and Mixed Layer Depth in MDTF Special Issue
#

# from __future__ import print_function
import os

# undo these for the framework version
import matplotlib

matplotlib.use("Agg")  # non-X windows backend


# Commands to load third-party libraries. Any code you don't include that's
# not part of your language's standard library should be listed in the
# settings.jsonc file.
import xarray as xr  # python library we use to read netcdf files
import matplotlib.pyplot as plt  # python library we use to make plots
import xesmf as xe
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import gsw
import time

months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


DATADIR = os.environ["DATADIR"]
OBS_DATA = os.environ["OBS_DATA"]
WK_DIR = os.environ["WK_DIR"]
CASENAME = os.environ["CASENAME"]
modelname = CASENAME


def readinocndata(file, varname="so", firstyr="2010", lastyr="2014"):
    ds = xr.open_dataset(file)
    ds = ds.sel(
        time=slice(firstyr + "-01-01", lastyr + "-12-31")
    )  # limit to yrs of interest, maybe model dep
    print(
        "Limit domain to Arctic to match obs"
    )  # script would work fine if data were global

    if "lat" in ds:  # hacky, fix this
        ds = ds.rename({'lat': 'latitude'})
    ds = ds.where(
        ds.latitude > 30.0, drop=True # limit to arctic for now, remove later
    )
    if "lon" in ds:
        ds = ds.rename({'lon': 'longitude'})
    field = ds[varname]
    field.name = varname

    ds.close()
    return field


def xr_reshape(A, dim, newdims, coords):
    """Reshape DataArray A to convert its dimension dim into sub-dimensions given by
    newdims and the corresponding coords.
    Example: Ar = xr_reshape(A, 'time', ['year', 'month'], [(2017, 2018), np.arange(12)])"""

    # Create a pandas MultiIndex from these labels
    ind = pd.MultiIndex.from_product(coords, names=newdims)

    # Replace the time index in the DataArray by this new index,
    A1 = A.copy()

    A1.coords[dim] = ind

    # Convert multiindex to individual dims using DataArray.unstack().
    # This changes dimension order! The new dimensions are at the end.
    A1 = A1.unstack(dim)

    # Permute to restore dimensions
    i = A.dims.index(dim)
    dims = list(A1.dims)

    for d in newdims[::-1]:
        dims.insert(i, d)

    for d in newdims:
        _ = dims.pop(-1)

    return A1.transpose(*dims)


def computemld(fieldso, fieldthetao):
    """Compute mixed layer depth from so and thetao

    Parameters
    ----------
    fieldso : xarray.DataArray for so, dims must be time, space, depth (must be in metres)
    fieldthetao : xarray.DataArray for thetao, dims must be time, space, depth (must be  in metres)

    Returns
    -------
    mld: xarray.DataArray, dims of time, space

    This function developed by Dhruv Balweda, Andrew Pauling, Sarah Ragen, Lettie Roach

    """
    pressure = xr.apply_ufunc(
        gsw.p_from_z,
        -fieldthetao.lev,
        fieldthetao.latitude,
        output_dtypes=[
            float,
        ],
    ).rename("pressure")
    # absolute salinity from practical salinity
    abs_salinity = xr.apply_ufunc(
        gsw.SA_from_SP,
        fieldso,
        pressure,
        fieldso.longitude,
        fieldso.latitude,
        output_dtypes=[
            float,
        ],
    ).rename("abs_salinity")

    # calculate cthetao - conservative temperature - from potential temperature
    cthetao = xr.apply_ufunc(
        gsw.CT_from_pt,
        abs_salinity,
        fieldthetao,
        output_dtypes=[
            float,
        ],
    ).rename("cthetao")

    # calculate sigma0 - potential density anomaly with reference pressure of 0 dbar,

    # this being this particular potential density minus 1000 kg/m^3.
    sigma0 = xr.apply_ufunc(
        gsw.density.sigma0,
        abs_salinity,
        cthetao,
        output_dtypes=[
            float,
        ],
    ).rename("sigma0")

    # interpolate density data to 10m
    surf_dens = sigma0.interp(lev=10)

    # density difference between surface and whole field
    dens_diff = sigma0 - surf_dens

    # keep density differences exceeding threshold, discard other values
    dens_diff = dens_diff.where(dens_diff > 0.03)

    # level of smallest difference between (density difference to 10m) and (threshold)
    mld = (
        dens_diff.lev.where(dens_diff == dens_diff.min(["lev"]))
        .max(["lev"])
        .rename("mld")
    )

    # compute water depth
    # note: pressure.lev, cthetao.lev, and abs_salinity.lev are identical
    test = sigma0.isel(time=0) + sigma0.lev
    bottom_depth = (
        pressure.lev.where(test == test.max(dim="lev"))
        .max(dim="lev")
        .rename("bottom_depth")
    )  # units 'meters'

    # set MLD to water depth where MLD is NaN
    mld = mld.where(~xr.ufuncs.isnan(mld), bottom_depth)

    return mld


def computemean(field=None, firstyr=2010, lastyr=2014):
    """Compute mean

    Parameters
    ----------
    field : xarray.DataArray, dims must be time, space (space can be multidim)

    Returns
    -------
    field.mean
    """
    firstyr = int(firstyr)
    lastyr = int(lastyr)
    field = xr_reshape(
        field,
        "time",
        ["year", "month"],
        [np.arange(firstyr, lastyr + 1), np.arange(12)],
    )

    return field.mean(dim="year")


def monthlyplot(field, edgec=None, figfile=None, cmapname="PuBu_r", myname=modelname):
    fig = plt.figure(figsize=(12, 10))
    cmap_c = cmapname

    for m, themonth in enumerate(months):
        ax = plt.subplot(3, 4, m + 1, projection=ccrs.NorthPolarStereo())
        ax.add_feature(cfeature.LAND, zorder=100, edgecolor="k", facecolor="darkgrey")

        ax.set_extent([0.005, 360, 50, 90], crs=ccrs.PlateCarree())
        field.sel(month=m).plot(
            x="lon",
            y="lat",
            transform=ccrs.PlateCarree(),
            cmap=cmap_c,
            add_colorbar=True,
        )

        ax.set_title(themonth, fontsize=14)

    fig.suptitle(
        myname + " mean Mixed Layer Depth (m) " + str(firstyr) + "-" + str(lastyr),
        fontsize=18,
    )
    plt.tight_layout()
    plt.savefig(figfile, format="png", dpi=300)
    plt.show()
    plt.close()
    return
# 1) Loading model data files: ###############################################
print("DATADIR: ", DATADIR)
print("OBS_DATA: ", OBS_DATA)
print("---")
print("Model working directory: ", WK_DIR, "model/")

so_var = "{so_var}".format(**os.environ)
thetao_var = "{thetao_var}".format(**os.environ)
firstyr = "{FIRSTYR}".format(**os.environ)
lastyr = "{LASTYR}".format(**os.environ)

print("thetao_var, so_var, firstyr, lastyr: ", thetao_var, so_var, firstyr, lastyr)

input_file_so = DATADIR+"/mon/"+CASENAME+"."+so_var+".mon.nc"
input_file_thetao = DATADIR+"/mon/"+CASENAME+"."+thetao_var+".mon.nc"

output_dir = os.path.join(WK_DIR, "model")  # LR
figures_dir = os.path.join(WK_DIR, "model")  # LR
figures_dir_o = os.path.join(WK_DIR, "obs") # LR

print("model figures dir", figures_dir)
print("obs figures dir", figures_dir_o)

obs_file = os.path.join(OBS_DATA, "mld_computed_obs_EN4_1979-2014.nc")

proc_obs_file = os.path.join(OBS_DATA, "EN4_mld_stats.nc")
proc_mod_file = os.path.join(output_dir, "model_mld.nc")

start = time.time()

processmod = not (os.path.isfile(proc_mod_file))  # check if obs proc file exists
if processmod:
    start = time.time()
    fieldso = readinocndata(input_file_so, "so", firstyr, lastyr)
    fieldthetao = readinocndata(input_file_thetao, "thetao", firstyr, lastyr)
    end = time.time()
    print(f"Time to read in files  = {end-start}")

    start = time.time()
    field = computemld(fieldso, fieldthetao)
    end = time.time()
    print(f"Time for MLD calc  = {end-start}")

    themean = computemean(field, firstyr, lastyr)
    themean.to_netcdf(proc_mod_file)

processobs = not (os.path.isfile(proc_obs_file))  # check if obs proc file exists
if processobs:  # if no proc file then must get obs and process
    obs = readinocndata(obs_file, "mld", firstyr, lastyr)
    obs = computemean(obs, firstyr, lastyr)
    obs.to_netcdf(proc_obs_file)


# 4) Read processed data, regrid model to obs grid, plot, saving figures: #######################################

obsmean = xr.open_dataset(proc_obs_file).mld
modmean = xr.open_dataset(proc_mod_file).mld


coords = [a for a in modmean.coords]
if "longitude" in coords:
    modmean = modmean.rename({"longitude": "lon"})
if "latitude" in coords:
    modmean = modmean.rename({"latitude": "lat"})

# regrid model data to obs grid
method = "nearest_s2d"
regridder = xe.Regridder(modmean, obsmean, method, periodic=False, reuse_weights=False)
modmean = regridder(modmean)
modmean.attrs["units"] = "m"
obsmean.attrs["units"] = "m"

# plot the figures

monthlyplot(
    modmean,
    figfile=os.path.join(figures_dir, "modelmldmean.png"),
    cmapname="viridis",
    myname=modelname,
)
monthlyplot(
    obsmean,
    figfile=os.path.join(figures_dir_o,  "obsmldmean.png"),
    cmapname="viridis",
    myname="EN4 reanalysis",
)
