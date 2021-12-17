#!/usr/bin/env python
# coding: utf-8
"""
# MDTF tool


The script generate the tropical Pacific dynamic sea level
and wind stress curl scatter plots at different time scale
due to their strong dependency from Ekman pumping/suction
and barotropic response over the ocean

input files
============
Ocean model : tauuo, tauvo, zos

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
 - spherical_area
      da_area     : generate area array based on the lon lat of data
 - dynamical_balance2
      curl_var_3d : calculate wind stress curl in obs (for Dataset with time dim)
      curl_var    : calculate wind stress curl in obs (for Dataset without time dim)
      curl_tau_3d : calculate wind stress curl in model (for Dataset with time dim)
      curl_tau    : calculate wind stress curl in model (for Dataset without time dim)
 - xr_ufunc
      da_linregress : linregress for Dataset with time dim


"""
import os
import warnings
import cftime
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt


import spherical_area as sa
from xr_ufunc import da_linregress
from dynamical_balance2 import curl_tau, curl_tau_3d
from dynamical_balance2 import curl_var, curl_var_3d




warnings.simplefilter("ignore")

print("--------------------------")
print("Start reading set parameter (pod_env_vars)")
print("--------------------------")

# constant setting
syear = np.int(os.getenv("FIRSTYR"))  # crop model data from year
fyear = np.int(os.getenv("LASTYR"))  # crop model data to year
predef_obs = os.getenv("predef_obs")
obs_start_year = np.int(os.getenv("obs_start_year"))  # crop obs data from year
obs_end_year = np.int(os.getenv("obs_end_year"))  # crop obs data to year

# regional average box
lon_range_list = [np.float(os.getenv("lon_min")), np.float(os.getenv("lon_max"))]
lat_range_list = [np.float(os.getenv("lat_min")), np.float(os.getenv("lat_max"))]

# Model label
Model_name = [os.getenv("CASENAME")]  # model name in the dictionary
Model_legend_name = [os.getenv("CASENAME")]  # model name appeared on the plot legend

# initialization
modelin = {}
path = {}

#####################

modelfile = [
    [os.getenv("TAUUO_FILE")],
    [os.getenv("TAUVO_FILE")],
    [os.getenv("ZOS_FILE")],
]
areafile = os.getenv("AREACELLO_FILE")


Model_varname = [os.getenv("tauuo_var"), os.getenv("tauvo_var"), os.getenv("zos_var")]
Model_coordname = [os.getenv("lat_coord_name"), os.getenv("lon_coord_name")]

xname = os.getenv("x_axis_name")
yname = os.getenv("y_axis_name")

print("Ocean model axis name:", xname, yname)
print("Ocean model coord name:", Model_coordname[1], Model_coordname[0])


print("--------------------------")
print("Start processing model outputs")
print("--------------------------")


ds_model_mlist = {}
mean_mlist = {}
season_mlist = {}
linear_mlist = {}

#### models
for nmodel, model in enumerate(Model_name):
    ds_model_list = {}
    mean_list = {}
    season_list = {}
    linear_list = {}

    # read input data into three xr.Datasets

    ds_tau = xr.open_mfdataset(
        [os.getenv("TAUUO_FILE"), os.getenv("TAUVO_FILE")], use_cftime=True
    )

    ds_zos = xr.open_mfdataset([os.getenv("ZOS_FILE")], use_cftime=True)

    ds_areacello = xr.open_mfdataset([os.getenv("AREACELLO_FILE")], use_cftime=True)

    # make a list of all datasets
    all_datasets = [ds_tau, ds_zos, ds_areacello]

    for nvar, var in enumerate(Model_varname):
        print("read %s %s" % (model, var))

        # search for the requested variable among the input datasets
        da_model = None
        for ds_model in all_datasets:
            if var in ds_model.variables:
                da_model = ds_model[var]
                break

        if da_model is None:
            raise ValueError(f"Unable to find {var} in input files")

        da_model = ds_model[var]

        # remove land value
        da_model[Model_coordname[1]] = da_model[Model_coordname[1]].where(
            da_model[Model_coordname[1]] < 1000.0, other=np.nan
        )
        da_model[Model_coordname[0]] = da_model[Model_coordname[0]].where(
            da_model[Model_coordname[0]] < 1000.0, other=np.nan
        )

        # store all model data
        ds_model_list[var] = da_model

        # calculate mean
        mean_list[var] = ds_model_list[var].mean(dim="time").compute()
        ds_model_list[var] = ds_model_list[var] - mean_list[var]

        # calculate seasonality
        season_list[var] = (
            ds_model_list[var].groupby("time.month").mean(dim="time").compute()
        )
        ds_model_list[var] = ds_model_list[var].groupby("time.month") - season_list[var]

        # remove linear trend
        linear_list[var] = da_linregress(ds_model_list[var], stTconfint=0.99)

    linear_mlist[model] = linear_list
    mean_mlist[model] = mean_list
    season_mlist[model] = season_list
    ds_model_mlist[model] = ds_model_list

# # Observation
if predef_obs != "True":

    # constant setting
    obs_year_range = [[1950, 2011], [1993, 2018, 9]]
    Obs_varname = [["tx", "ty"], ["adt"]]
    Obs_name = ["WASwind", "CMEMS"]

    # inputs
    obsin = {}
    obspath = {}

    OBS = Obs_name[0]
    OBSDIR = str(os.getenv("OBS_DATA"))
    obsfile = [["waswind_v1_0_1.monthly.nc"], ["waswind_v1_0_1.monthly.nc"]]
    obspath[OBS] = [OBSDIR, obsfile]

    OBS = Obs_name[1]
    OBSDIR = str(os.getenv("OBS_DATA"))
    obsfile = [["dt_global_allsat_phy_l4_monthly_adt.nc"]]
    obspath[OBS] = [OBSDIR, obsfile]

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
                SKIPNA = False

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
                SKIPNA = True

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
            ds_obs_list[var] = (
                ds_obs_list[var].groupby("time.month") - obs_season_list[var]
            )

            # remove linear trend
            obs_linear_list[var] = da_linregress(
                ds_obs_list[var],
                xname="lon",
                yname="lat",
                stTconfint=0.99,
                skipna=SKIPNA,
            )

        obs_linear_mlist[obs] = obs_linear_list
        obs_mean_mlist[obs] = obs_mean_list
        obs_season_mlist[obs] = obs_season_list
        ds_obs_mlist[obs] = ds_obs_list


# # Derive wind stress curl
#########
# Model
#########
for nmodel, model in enumerate(Model_name):
    linear_mlist[model]["curl_tauuo"], linear_mlist[model]["curl_tauvo"] = curl_tau(
        linear_mlist[model]["tauuo"].slope,
        linear_mlist[model]["tauvo"].slope,
        xname=xname,
        yname=yname,
    )

    linear_mlist[model]["curl_tau"] = (
        linear_mlist[model]["curl_tauuo"] + linear_mlist[model]["curl_tauvo"]
    )

    mean_mlist[model]["curl_tauuo"], mean_mlist[model]["curl_tauvo"] = curl_tau(
        mean_mlist[model]["tauuo"], mean_mlist[model]["tauvo"], xname=xname, yname=yname
    )

    mean_mlist[model]["curl_tau"] = (
        mean_mlist[model]["curl_tauuo"] + mean_mlist[model]["curl_tauvo"]
    )

    season_mlist[model]["curl_tauuo"], season_mlist[model]["curl_tauvo"] = curl_tau_3d(
        season_mlist[model]["tauuo"],
        season_mlist[model]["tauvo"],
        xname=xname,
        yname=yname,
        tname="month",
    )

    season_mlist[model]["curl_tau"] = (
        season_mlist[model]["curl_tauuo"] + season_mlist[model]["curl_tauvo"]
    )

#########
# Obs
#########
if predef_obs != "True":
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
        obs_season_mlist[obs]["tx"],
        obs_season_mlist[obs]["ty"],
        xname="lon",
        yname="lat",
        tname="month",
    )

    obs_season_mlist[obs]["curl_tau"] = (
        obs_season_mlist[obs]["curl_tx"] + obs_season_mlist[obs]["curl_ty"]
    )

else:
    # for pre-defined period 1993-2011
    Obs_name = ["WASwind", "CMEMS"]

    # initialization of dict and list
    obs_mean_mlist = {}
    obs_season_mlist = {}
    obs_linear_mlist = {}

    obs_linear_mlist["CMEMS"] = {}
    obs_mean_mlist["CMEMS"] = {}
    obs_season_mlist["CMEMS"] = {}

    obs_linear_mlist["WASwind"] = {}
    obs_mean_mlist["WASwind"] = {}
    obs_season_mlist["WASwind"] = {}

    PREFILE_DIR = str(os.getenv("OBS_DATA"))

    obs_linear_mlist["CMEMS"]["adt"] = xr.open_dataset(
        os.path.join(PREFILE_DIR, "cmems_ssh_linear.nc")
    )
    obs_mean_mlist["CMEMS"]["adt"] = xr.open_dataset(
        os.path.join(PREFILE_DIR, "cmems_ssh_mean.nc")
    ).adt
    obs_season_mlist["CMEMS"]["adt"] = xr.open_dataset(
        os.path.join(PREFILE_DIR, "cmems_ssh_season.nc")
    ).adt

    obs_linear_mlist["WASwind"]["curl_tau"] = xr.open_dataset(
        os.path.join(PREFILE_DIR, "waswind_curltau_linear.nc")
    ).curl_tau
    obs_mean_mlist["WASwind"]["curl_tau"] = xr.open_dataset(
        os.path.join(PREFILE_DIR, "waswind_curltau_mean.nc")
    ).curl_tau
    obs_season_mlist["WASwind"]["curl_tau"] = xr.open_dataset(
        os.path.join(PREFILE_DIR, "waswind_curltau_season.nc")
    ).curl_tau


# # Regional averaging
#### setting regional range
lon_range = lon_range_list
lat_range = lat_range_list

# correct the lon range
lon_range_mod = np.array(lon_range)
lonmin = ds_model_mlist[model]["zos"].lon.min()
ind1 = np.where(lon_range_mod < np.float(0))[0]
lon_range_mod[ind1] = lon_range_mod[ind1] + 360.0  # change Lon range to 0-360



#####################
# MODEL
#####################
regionalavg_mlist = {}
for nmodel, model in enumerate(Model_name):
    regionalavg_list = {}
    for nvar, var in enumerate(["curl_tau", "zos"]):

        # read areacello
        da_area = ds_areacello[os.getenv("areacello_var")]
        da_area_temp = da_area.copy()
        da_area_temp['lon'] = xr.where(da_area_temp.lon<0,
                                       da_area_temp.lon+360.,
                                       da_area_temp.lon)  

        # crop region
        ds_mask = (
            da_area
            .where(
                  (da_area_temp[Model_coordname[1]] >= np.min(lon_range_mod))
                & (da_area_temp[Model_coordname[1]] <= np.max(lon_range_mod))
                & (da_area_temp[Model_coordname[0]] >= np.min(lat_range))
                & (da_area_temp[Model_coordname[0]] <= np.max(lat_range)),
                drop=True,
            )
            .compute()
        )
        
        
        ds_mask = ds_mask / ds_mask

        # calculate regional mean
        regionalavg_list[
            "%s_%i_%i_%i_%i_season"
            % (var, lon_range[0], lon_range[1], lat_range[0], lat_range[1])
        ] = (
            (season_mlist[model][var] * ds_mask * da_area).sum(dim=[xname, yname])
            / (ds_mask * da_area).sum(dim=[xname, yname])
        ).compute()

        regionalavg_list[
            "%s_%i_%i_%i_%i_mean"
            % (var, lon_range[0], lon_range[1], lat_range[0], lat_range[1])
        ] = (
            (mean_mlist[model][var] * ds_mask * da_area).sum(dim=[xname, yname])
            / (ds_mask * da_area).sum(dim=[xname, yname])
        ).compute()

        regionalavg_list[
            "%s_%i_%i_%i_%i_linear"
            % (var, lon_range[0], lon_range[1], lat_range[0], lat_range[1])
        ] = (
            (linear_mlist[model][var] * ds_mask * da_area).sum(dim=[xname, yname])
            / (ds_mask * da_area).sum(dim=[xname, yname])
        ).compute()
        

    regionalavg_mlist[model] = regionalavg_list

#####################
# OBS
#####################
obs_regionalavg_mlist = {}
for nobs, obs in enumerate(Obs_name):
    obs_regionalavg_list = {}
    if obs in ["CMEMS"]:
        var = "adt"
        obs_xname = "lon"
        obs_yname = "lat"

    elif obs in ["WASwind"]:
        var = "curl_tau"
        obs_xname = "lon"
        obs_yname = "lat"

    da_area = sa.da_area(
        obs_mean_mlist[obs][var],
        lonname="lon",
        latname="lat",
        xname=obs_xname,
        yname=obs_yname,
        model=None,
    )

    # crop region
    ds_obs_mask = (
        obs_mean_mlist[obs][var]
        .where(
            (obs_mean_mlist[obs][var].lon >= np.min(lon_range_mod))
            & (obs_mean_mlist[obs][var].lon <= np.max(lon_range_mod))
            & (obs_mean_mlist[obs][var].lat >= np.min(lat_range))
            & (obs_mean_mlist[obs][var].lat <= np.max(lat_range)),
            drop=True,
        )
        .compute()
    )
    ds_obs_mask = ds_obs_mask / ds_obs_mask

    # calculate regional mean
    obs_regionalavg_list[
        "%s_%i_%i_%i_%i_season"
        % (var, lon_range[0], lon_range[1], lat_range[0], lat_range[1])
    ] = (
        (obs_season_mlist[obs][var] * ds_obs_mask * da_area).sum(
            dim=[obs_xname, obs_yname]
        )
        / (ds_obs_mask * da_area).sum(dim=[obs_xname, obs_yname])
    ).compute()

    obs_regionalavg_list[
        "%s_%i_%i_%i_%i_mean"
        % (var, lon_range[0], lon_range[1], lat_range[0], lat_range[1])
    ] = (
        (obs_mean_mlist[obs][var] * ds_obs_mask * da_area).sum(
            dim=[obs_xname, obs_yname]
        )
        / (ds_obs_mask * da_area).sum(dim=[obs_xname, obs_yname])
    ).compute()

    obs_regionalavg_list[
        "%s_%i_%i_%i_%i_linear"
        % (var, lon_range[0], lon_range[1], lat_range[0], lat_range[1])
    ] = (
        (obs_linear_mlist[obs][var] * ds_obs_mask * da_area).sum(
            dim=[obs_xname, obs_yname]
        )
        / (ds_obs_mask * da_area).sum(dim=[obs_xname, obs_yname])
    ).compute()

    obs_regionalavg_mlist[obs] = obs_regionalavg_list


#### plotting
fig = plt.figure(1)


#######
# mean
#######
ax1 = fig.add_axes([0, 0, 1, 1])

all_wsc = []
all_ssh = []

wsc = obs_regionalavg_mlist["WASwind"][
    f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_mean"
]
ssh = obs_regionalavg_mlist["CMEMS"][
    f"adt_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_mean"
]
ax1.scatter(wsc, ssh, c="k", label="Observation")
all_wsc.append(wsc)
all_ssh.append(ssh)

for nmodel, model in enumerate(Model_name):
    wsc = regionalavg_mlist[model][
        f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_mean"
    ]

    ssh = regionalavg_mlist[model][
        f"zos_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_mean"
    ]
    
    ax1.scatter(wsc, ssh, label="%s" % (Model_legend_name[nmodel]))
    all_wsc.append(wsc)
    all_ssh.append(ssh)

all_wsc = np.array(all_wsc)
all_ssh = np.array(all_ssh)

#### setting the plotting format
ax1.set_ylabel("SSH (m)", {"size": "20"}, color="k")
ax1.set_ylim([all_ssh.min() - all_ssh.min() / 5.0, all_ssh.max() + all_ssh.max() / 5.0])
ax1.set_xlabel("WSC (N/m$^3$)", {"size": "20"}, color="k")
ax1.set_xlim([all_wsc.min() - all_wsc.min() / 5.0, all_wsc.max() + all_wsc.max() / 5.0])
ax1.tick_params(axis="y", labelsize=20, labelcolor="k", rotation=0)
ax1.tick_params(axis="x", labelsize=20, labelcolor="k", rotation=0)
ax1.set_title("Mean state", {"size": "24"}, pad=24)
ax1.grid(linestyle="dashed", alpha=0.5, color="grey")

#########
# Linear
#########
ax1 = fig.add_axes([1.3, 0, 1, 1])

all_wsc = []
all_ssh = []

wsc = obs_regionalavg_mlist["WASwind"][
f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_linear"
]
ssh = obs_regionalavg_mlist["CMEMS"][
f"adt_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_linear"
].slope
ax1.scatter(wsc, ssh, c="k", label="Observation")
all_wsc.append(wsc)
all_ssh.append(ssh)

for nmodel, model in enumerate(Model_name):
    wsc = regionalavg_mlist[model][
    f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_linear"
    ]
    ssh = regionalavg_mlist[model][
    f"zos_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_linear"
    ].slope
    ax1.scatter(wsc, ssh, label="%s" % (Model_legend_name[nmodel]))
    all_wsc.append(wsc)
    all_ssh.append(ssh)

all_wsc = np.array(all_wsc)
all_ssh = np.array(all_ssh)


#### setting the plotting format
ax1.set_ylabel("SSH (m)", {"size": "20"}, color="k")
ax1.set_ylim(
    [
        all_ssh.min() - np.abs(all_ssh.min() / 5.0),
        all_ssh.max() + np.abs(all_ssh.max() / 5.0),
    ]
)
ax1.set_xlabel("WSC (N/m$^3$)", {"size": "20"}, color="k")
ax1.set_xlim(
    [
        all_wsc.min() - np.abs(all_wsc.min() / 5.0),
        all_wsc.max() + np.abs(all_wsc.max() / 5.0),
    ]
)
ax1.tick_params(axis="y", labelsize=20, labelcolor="k", rotation=0)
ax1.tick_params(axis="x", labelsize=20, labelcolor="k", rotation=0)
ax1.set_title("Linear trend", {"size": "24"}, pad=24)
ax1.legend(loc="upper left", bbox_to_anchor=(1.05, 1), fontsize=14, frameon=False)
ax1.grid(linestyle="dashed", alpha=0.5, color="grey")


#########
# Annual amp
#########
ax1 = fig.add_axes([0, -1.5, 1, 1])

all_wsc = []
all_ssh = []

wsc = (
    obs_regionalavg_mlist["WASwind"][
    f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
    ].max()
    - obs_regionalavg_mlist["WASwind"][
    f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
    ].min()
)
ssh = (
    obs_regionalavg_mlist["CMEMS"][
    f"adt_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
    ].max()
    - obs_regionalavg_mlist["CMEMS"][
    f"adt_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
    ].min()
)
wsc = np.abs(wsc)
ssh = np.abs(ssh)
ax1.scatter(wsc, ssh, c="k", label="Observation")
all_wsc.append(wsc)
all_ssh.append(ssh)

for nmodel, model in enumerate(Model_name):
    wsc = (
        regionalavg_mlist[model][
        f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
        ].max()
        - regionalavg_mlist[model][
        f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
        ].min()
    )
    ssh = (
        regionalavg_mlist[model][
        f"zos_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
        ].max()
        - regionalavg_mlist[model][
        f"zos_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
        ].min()
    )
    ax1.scatter(wsc, ssh, label="%s" % (Model_legend_name[nmodel]))
    wsc = np.abs(wsc)
    ssh = np.abs(ssh)
    all_wsc.append(wsc)
    all_ssh.append(ssh)


all_wsc = np.array(all_wsc)
all_ssh = np.array(all_ssh)


#### setting the plotting format
ax1.set_ylabel("SSH (m)", {"size": "20"}, color="k")
ax1.set_ylim([all_ssh.min() - all_ssh.min() / 5.0, all_ssh.max() + all_ssh.max() / 5.0])
ax1.set_xlabel("WSC (N/m$^3$)", {"size": "20"}, color="k")
ax1.set_xlim([all_wsc.min() - all_wsc.min() / 5.0, all_wsc.max() + all_wsc.max() / 5.0])
ax1.tick_params(axis="y", labelsize=20, labelcolor="k", rotation=0)
ax1.tick_params(axis="x", labelsize=20, labelcolor="k", rotation=0)
ax1.set_title("Annual amplitude", {"size": "24"}, pad=24)
ax1.grid(linestyle="dashed", alpha=0.5, color="grey")


#########
# Annual phase
#########
ax1 = fig.add_axes([1.3, -1.5, 1, 1])


all_wsc = []
all_ssh = []

ind = obs_regionalavg_mlist["WASwind"][
f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
].argmax()
wsc = (
    obs_regionalavg_mlist["WASwind"][
    f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
    ]
    .isel(month=ind)
    .month.values
)
ind = obs_regionalavg_mlist["CMEMS"][
    f"adt_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
].argmax()
ssh = (
    obs_regionalavg_mlist["CMEMS"][
    f"adt_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
    ]
    .isel(month=ind)
    .month.values
)

ax1.scatter(wsc, ssh, c="k", label="Observation")
all_wsc.append(wsc)
all_ssh.append(ssh)

for nmodel, model in enumerate(Model_name):
    ind = regionalavg_mlist[model][
    f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
    ].argmax()
    wsc = (
        regionalavg_mlist[model][
        f"curl_tau_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
        ]
        .isel(month=ind)
        .month.values
    )
    ind = regionalavg_mlist[model][
    f"zos_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
    ].argmax()
    ssh = (
        regionalavg_mlist[model][
        f"zos_{lon_range[0]:.0f}_{lon_range[1]:.0f}_{lat_range[0]:.0f}_{lat_range[1]:.0f}_season"
        ]
        .isel(month=ind)
        .month.values
    )

    ax1.scatter(wsc, ssh, label="%s" % (Model_legend_name[nmodel]))
    all_wsc.append(wsc)
    all_ssh.append(ssh)


all_wsc = np.array(all_wsc)
all_ssh = np.array(all_ssh)


#### setting the plotting format
ax1.set_ylabel("SSH (month)", {"size": "20"}, color="k")
ax1.set_ylim([0.5, 12.5])
ax1.set_xlabel("WSC (month)", {"size": "20"}, color="k")
ax1.set_xlim([0.5, 12.5])
ax1.tick_params(axis="y", labelsize=20, labelcolor="k", rotation=0)
ax1.tick_params(axis="x", labelsize=20, labelcolor="k", rotation=0)
ax1.set_title("Annual phase", {"size": "24"}, pad=24)
ax1.grid(linestyle="dashed", alpha=0.5, color="grey")


fig.savefig(
    os.getenv("WK_DIR") + "/model/PS/example_model_plot.eps",
    facecolor="w",
    edgecolor="w",
    orientation="portrait",
    papertype=None,
    format=None,
    transparent=False,
    bbox_inches="tight",
    pad_inches=None,
    frameon=None,
)
fig.savefig(
    os.getenv("WK_DIR") + "/obs/PS/example_obs_plot.eps",
    facecolor="w",
    edgecolor="w",
    orientation="portrait",
    papertype=None,
    format=None,
    transparent=False,
    bbox_inches="tight",
    pad_inches=None,
    frameon=None,
)
