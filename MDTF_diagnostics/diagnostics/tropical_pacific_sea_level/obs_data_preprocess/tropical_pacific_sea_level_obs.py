#!/usr/bin/env python
# coding: utf-8
"""
# Observational data preprocessing


The script generate the tropical Pacific dynamic sea level
and wind stress curl mean, trend, annual amplitude and phase

input files
============
Observational data : adt, tx, ty
- adt (absolute dynamic topography from CMEMS)
    preprocessing from daily to monthly mean is needed (use 'io_cmems_adt.py')
- tx (surface wind stress in the x direction from WASwind)
    no preprocessing needed
- ty (surface wind stress in the y direction from WASwind)
    no preprocessing needed
    
    data access :
    **********************

    - adt : 
        Ftp server is the fastest way to manage download
        http://marine.copernicus.eu/services-portfolio/access-to-products/
        search for product ID - "SEALEVEL_GLO_PHY_L4_REP_OBSERVATIONS_008_047"
        Need to download the daily data with adt (absolute dynamic topography) available 

    - tx,ty :
        https://www.riam.kyushu-u.ac.jp/oed/tokinaga/waswind.html


 function used
 ==================
 - spherical_area.da_area     : generate area array based on the lon lat of data
 - dynamical_balance2.curl_var_3d : calculate wind stress curl in obs (for Dataset with time dim)
 - dynamical_balance2.curl_var    : calculate wind stress curl in obs (for Dataset without time dim)
 - xr_ufunc.da_linregress : linregress for Dataset with time dim


"""
import os
import cftime
import xarray as xr
import spherical_area as sa
from xr_ufunc import da_linregress
from dynamical_balance2_obs import curl_var, curl_var_3d


import warnings

warnings.simplefilter("ignore")

# longest overlapping period of the two observational data
obs_start_year = 1993
obs_end_year = 2011

inputdir = (
    "/storage1/home1/chiaweih/mdtf/inputdata/obs_data/tropical_pacific_sea_level/"
)
outputdir = (
    "/storage1/home1/chiaweih/mdtf/inputdata/obs_data/tropical_pacific_sea_level/"
)

# # Observation
# constant setting
obs_year_range = [[1950, 2011], [1993, 2018, 9]]
Obs_varname = [["tx", "ty"], ["adt"]]
Obs_name = ["WASwind", "CMEMS"]

# inputs
obsin = {}
obspath = {}

obs = Obs_name[0]
obsdir = inputdir
obsfile = [["waswind_v1_0_1.monthly.nc"], ["waswind_v1_0_1.monthly.nc"]]
obspath[obs] = [obsdir, obsfile]

obs = Obs_name[1]
obsdir = inputdir
obsfile = [["dt_global_allsat_phy_l4_monthly_adt.nc"]]
obspath[obs] = [obsdir, obsfile]


for nobs, obs in enumerate(Obs_name):
    obsdir = obspath[obs][0]
    obsfile = obspath[obs][1]
    multivar = []
    for file in obsfile:
        if len(file) == 1:
            multivar.append([os.path.join(obsdir, file[0])])
        elif len(file) > 1:
            multifile = []
            for ff in file:
                multifile.append(os.path.join(obsdir, ff))
            multivar.append(multifile)
    obsin[obs] = multivar


# initialization of dict and list
ds_obs_mlist = {}
obs_mean_mlist = {}
obs_season_mlist = {}
obs_linear_mlist = {}

for nobs, obs in enumerate(Obs_name):
    ds_obs_list = {}
    obs_mean_list = {}
    obs_season_list = {}
    obs_linear_list = {}
    for nvar, var in enumerate(Obs_varname[nobs]):
        print("read %s %s" % (obs, var))

        # read input data
        # -- single file
        if len(obsin[obs][nvar]) == 1:

            # find out dimension name
            da = xr.open_dataset(obsin[obs][nvar][0])
            obsdims = list(da[var].dims)

            ds_obs = xr.open_dataset(obsin[obs][nvar][0])

        # -- multi-file merge (same variable)
        elif len(obsin[obs][nvar]) > 1:
            for nf, file in enumerate(obsin[obs][nvar]):
                # find out dimension name
                da = xr.open_dataset(file, chunks={})
                obsdims = list(da[var].dims)

                ds_obs_sub = xr.open_dataset(file, use_cftime=True)
                if nf == 0:
                    ds_obs = ds_obs_sub
                else:
                    ds_obs = xr.concat(
                        [ds_obs, ds_obs_sub], dim="time", data_vars="minimal"
                    )

        ############## CMEMS ##############
        if obs in ["CMEMS"]:
            syear_obs = obs_year_range[nobs][0]
            fyear_obs = obs_year_range[nobs][1]
            fmon_obs = obs_year_range[nobs][2]
            #### create time axis for overlapping period
            timeax = xr.cftime_range(
                start=cftime.datetime(syear_obs, 1, 1),
                end=cftime.datetime(fyear_obs, fmon_obs, 1),
                freq="MS",
            )
            timeax = timeax.to_datetimeindex()  # cftime => datetime64

            # fix required in the event time lengths are not consistent
            # (a bit rough -- could be more intelligent)
            ds_obs = ds_obs.isel(time=slice(0, len(timeax)))

            ds_obs["time"] = timeax

            # calculate global mean sea level
            da_area = sa.da_area(
                ds_obs,
                lonname="longitude",
                latname="latitude",
                xname="longitude",
                yname="latitude",
                model=None,
            )
            da_glo_mean = (ds_obs * da_area).sum(
                dim=["longitude", "latitude"]
            ) / da_area.sum(dim=["longitude", "latitude"])
            ds_obs = ds_obs - da_glo_mean

            # rename
            ds_obs = ds_obs.rename({"longitude": "lon", "latitude": "lat"})
            skipna = False

        else:
            syear_obs = obs_year_range[nobs][0]
            fyear_obs = obs_year_range[nobs][1]
            #### create time axis for overlapping period
            timeax = xr.cftime_range(
                start=cftime.datetime(syear_obs, 1, 1),
                end=cftime.datetime(fyear_obs, 12, 31),
                freq="MS",
            )
            timeax = timeax.to_datetimeindex()  # cftime => datetime64
            ds_obs["time"] = timeax
            skipna = True

        # crop data (time)
        #  include the option to crop obs data in the pod_env_vars setting
        ds_obs[var].load()
        ds_obs = ds_obs[var].sel(
            time=slice("%i-01-01" % obs_start_year, "%i-12-31" % obs_end_year)
        )

        # store all model data
        ds_obs_list[var] = ds_obs

        # calculate mean
        obs_mean_list[var] = ds_obs_list[var].mean(dim="time").compute()
        ds_obs_list[var] = ds_obs_list[var] - obs_mean_list[var]

        # calculate seasonality
        obs_season_list[var] = (
            ds_obs_list[var].groupby("time.month").mean(dim="time").compute()
        )
        ds_obs_list[var] = ds_obs_list[var].groupby("time.month") - obs_season_list[var]

        # remove linear trend
        obs_linear_list[var] = da_linregress(
            ds_obs_list[var], xname="lon", yname="lat", stTconfint=0.99, skipna=skipna
        )

    obs_linear_mlist[obs] = obs_linear_list
    obs_mean_mlist[obs] = obs_mean_list
    obs_season_mlist[obs] = obs_season_list
    ds_obs_mlist[obs] = ds_obs_list


# # Derive wind stress curl
obs = "WASwind"
obs_linear_mlist[obs]["curl_tx"], obs_linear_mlist[obs]["curl_ty"] = curl_var(
    obs_linear_mlist[obs]["tx"].slope,
    obs_linear_mlist[obs]["ty"].slope,
    x_name="lon",
    y_name="lat",
)
obs_linear_mlist[obs]["curl_tau"] = (
    obs_linear_mlist[obs]["curl_tx"] + obs_linear_mlist[obs]["curl_ty"]
)

obs_mean_mlist[obs]["curl_tx"], obs_mean_mlist[obs]["curl_ty"] = curl_var(
    obs_mean_mlist[obs]["tx"], obs_mean_mlist[obs]["ty"], x_name="lon", y_name="lat"
)
obs_mean_mlist[obs]["curl_tau"] = (
    obs_mean_mlist[obs]["curl_tx"] + obs_mean_mlist[obs]["curl_ty"]
)

obs_season_mlist[obs]["curl_tx"], obs_season_mlist[obs]["curl_ty"] = curl_var_3d(
    obs_season_mlist[obs]["tx"], obs_season_mlist[obs]["ty"], xname="lon", yname="lat",
    tname="month"
)
obs_season_mlist[obs]["curl_tau"] = (
    obs_season_mlist[obs]["curl_tx"] + obs_season_mlist[obs]["curl_ty"]
)


# output mean,trend, and seasonal files
obs_linear_mlist["CMEMS"]["adt"].to_netcdf(outputdir + "cmems_ssh_linear.nc")
obs_mean_mlist["CMEMS"]["adt"].to_netcdf(outputdir + "cmems_ssh_mean.nc")
obs_season_mlist["CMEMS"]["adt"].to_netcdf(outputdir + "cmems_ssh_season.nc")

obs_linear_mlist["WASwind"]["curl_tau"].name = "curl_tau"
obs_mean_mlist["WASwind"]["curl_tau"].name = "curl_tau"
obs_season_mlist["WASwind"]["curl_tau"].name = "curl_tau"
obs_linear_mlist["WASwind"]["curl_tau"].to_netcdf(
    outputdir + "waswind_curltau_linear.nc"
)
obs_mean_mlist["WASwind"]["curl_tau"].to_netcdf(outputdir + "waswind_curltau_mean.nc")
obs_season_mlist["WASwind"]["curl_tau"].to_netcdf(
    outputdir + "waswind_curltau_season.nc"
)
