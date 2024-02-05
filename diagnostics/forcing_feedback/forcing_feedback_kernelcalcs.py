# This file is part of the forcing_feedback module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

# ======================================================================
# forcingfluxanom_kernelcalcs_final.py
#
#  Called by forcingfluxanom_xr_final.py
#   Reads in and (as needed) regrids radiative kernels, reads in model data, computes radiative flux kernel calculations
#
#  Forcing Feedback Diagnositic Package
#
#  This file is part of the Forcing and Feedback Diagnostic Package
#    and the MDTF code package. See LICENSE.txt for the license.
#

import os
import numpy as np
import xarray as xr
from scipy.interpolate import interp1d

# Import functions specific to this toolkit
from forcing_feedback_util import var_anom4D
from forcing_feedback_util import fluxanom_calc_4D
from forcing_feedback_util import fluxanom_calc_3D
from forcing_feedback_util import esat_coef
from forcing_feedback_util import latlonr3_3D4D
from forcing_feedback_util import feedback_regress

# ======================================================================

# Read in radiative kernels
kernnc = xr.open_dataset(os.environ["OBS_DATA"] + "/forcing_feedback_kernels.nc")
lat_kern = kernnc['latitude'].values
lon_kern = kernnc['longitude'].values
lev_kern = kernnc['plev'].values
time_kern_TOA = kernnc['time'].values
lw_t_kern_TOA = kernnc['lw_t'].values  # LW all-sky air temperature kernel
lwclr_t_kern_TOA = kernnc['lwclr_t'].values  # LW clear-sky air temperature kernel
lw_ts_kern_TOA = kernnc['lw_ts'].values  # LW all-sky surface temperature kernel
lwclr_ts_kern_TOA = kernnc['lwclr_ts'].values  # LW clear-sky surface temperature kernel
lw_q_kern_TOA = kernnc['lw_q'].values  # LW all-sky water vapor radiative kernel
lwclr_q_kern_TOA = kernnc['lwclr_q'].values  # LW clear-sky water vapor radiative kernel
sw_q_kern_TOA = kernnc['sw_q'].values  # SW all-sky water vapor radiative kernel
swclr_q_kern_TOA = kernnc['swclr_q'].values  # SW clear-sky water vapor radiative kernel
sw_a_kern_TOA = kernnc['sw_a'].values  # SW all-sky surface albedo radiative kernel
swclr_a_kern_TOA = kernnc['swclr_a'].values  # SW clear-sky surface albedo radiative kernel
ps_kern_TOA = kernnc['PS'].values  # Radiative kernel surface pressure

# close kernel file
kernnc.close()

# Read in model output

varnames = ["ta", "ts", "hus", "rsus", "rsds", "rsuscs", "rsdscs", "rsdt", "rsut", "rsutcs", "rlut", "rlutcs"]
model_mainvar_pert = {}
i = 0
for varname in varnames:
    nc = xr.open_dataset(os.environ[varname.upper() + "_FILE"])
    model_mainvar_pert[os.environ[varname + "_var"]] = nc[os.environ[varname + "_var"]]
    if i == 0:
        lat_model = nc[os.environ["lat_coord"]].values
        lon_model = nc[os.environ["lon_coord"]].values
        lev_model = nc[os.environ["plev_coord"]].values
        time_model = nc[os.environ["time_coord"]].values
    nc.close()
    i += 1
i = None

model_mainvar_climo = model_mainvar_pert

# To avoid issues with interpreting different model time formats, just create new variable.
time_model = np.arange(len(time_model)) + 1

# Regrid kernels using function to match horizontal grid of model/observational data
lw_t_kern_TOA = latlonr3_3D4D(lw_t_kern_TOA, lat_kern, lon_kern, lat_model, lon_model,
                              model_mainvar_climo[os.environ["ta_var"]])
lwclr_t_kern_TOA = latlonr3_3D4D(lwclr_t_kern_TOA, lat_kern, lon_kern, lat_model, lon_model,
                                 model_mainvar_climo[os.environ["ta_var"]])
lw_ts_kern_TOA = latlonr3_3D4D(lw_ts_kern_TOA, lat_kern, lon_kern, lat_model, lon_model,
                               model_mainvar_climo[os.environ["ts_var"]])
lwclr_ts_kern_TOA = latlonr3_3D4D(lwclr_ts_kern_TOA, lat_kern, lon_kern, lat_model, lon_model,
                                  model_mainvar_climo[os.environ["ts_var"]])
lw_q_kern_TOA = latlonr3_3D4D(lw_q_kern_TOA, lat_kern, lon_kern, lat_model, lon_model,
                              model_mainvar_climo[os.environ["ta_var"]])
lwclr_q_kern_TOA = latlonr3_3D4D(lwclr_q_kern_TOA, lat_kern, lon_kern, lat_model, lon_model,
                                 model_mainvar_climo[os.environ["ta_var"]])
sw_q_kern_TOA = latlonr3_3D4D(sw_q_kern_TOA, lat_kern, lon_kern, lat_model, lon_model,
                              model_mainvar_climo[os.environ["ta_var"]])
swclr_q_kern_TOA = latlonr3_3D4D(swclr_q_kern_TOA, lat_kern, lon_kern, lat_model, lon_model, \
                                 model_mainvar_climo[os.environ["ta_var"]])
sw_a_kern_TOA = latlonr3_3D4D(sw_a_kern_TOA, lat_kern, lon_kern, lat_model, lon_model, \
                              model_mainvar_climo[os.environ["ts_var"]])
swclr_a_kern_TOA = latlonr3_3D4D(swclr_a_kern_TOA, lat_kern, lon_kern, lat_model, lon_model, \
                                 model_mainvar_climo[os.environ["ts_var"]])
ps_kern_TOA = latlonr3_3D4D(ps_kern_TOA, lat_kern, lon_kern, lat_model, lon_model, \
                            model_mainvar_climo[os.environ["ts_var"]])

# Kernels have now been regridded to the model/observation grid
lat_kern = lat_model
lon_kern = lon_model

# If necessary, conduct vertical interpolation
for varname in varnames:
    if len(model_mainvar_pert[os.environ[varname + "_var"]].shape) == 4:
        # If vertical coordinates for kernel and model data differ, check if just a difference in units,
        # check if one is flipped and finally, flip or interpolate as needed.
        if not np.array_equal(lev_model, lev_kern) and not np.array_equal(lev_model / 100, lev_kern) \
                and not np.array_equal(lev_model * 100, lev_kern):
            if np.array_equal(lev_model, lev_kern[::-1]) or np.array_equal(lev_model / 100, lev_kern[::-1]) \
                    or np.array_equal(lev_model * 100, lev_kern[::-1]):
                model_mainvar_pert[os.environ[varname + "_var"]] = \
                    model_mainvar_pert[os.environ[varname + "_var"]][:, ::-1, ...]
                model_mainvar_climo[os.environ[varname + "_var"]] = \
                    model_mainvar_climo[os.environ[varname + "_var"]][:, ::-1, ...]
            else:
                if np.max(lev_model) / np.max(lev_kern) > 10:
                    lev_model = lev_model / 100  # scale units down
                if np.max(lev_model) / np.max(lev_kern) < 0.1:
                    lev_model = lev_model * 100  # scale units up
                f = interp1d(np.log(lev_model), model_mainvar_pert[os.environ[varname + "_var"]],
                             axis=1, bounds_error=False, fill_value='extrapolate')
                model_mainvar_pert[os.environ[varname + "_var"]] = f(np.log(lev_kern))
                f = None
                f = interp1d(np.log(lev_model), model_mainvar_climo[os.environ[varname + "_var"]],
                             axis=1, bounds_error=False, fill_value='extrapolate')
                model_mainvar_climo[os.environ[varname + "_var"]] = f(np.log(lev_kern))

# Pressure of upper boundary of each vertical layer
pt = (lev_kern[1:] + lev_kern[:-1]) / 2
pt = np.append(pt, 0)
# Pressure of lower boundary of each vertical layer
pb = pt[:-1]
pb = np.insert(pb, 0, 1000)
# Pressure thickness of each vertical level
dp = pb - pt

sk = lw_t_kern_TOA.shape
sp = model_mainvar_pert[os.environ["ta_var"]].shape

# Determine thickness of lowest layer, dependent on local surface pressure
dp_sfc = dp[0] + (ps_kern_TOA - pb[0])
dp_sfc[ps_kern_TOA >= pt[0]] = 0

# Repeat lowest layer thicknesses to match size of model data for kernel calculations
dp_sfc = np.repeat(dp_sfc[np.newaxis, :, :, :], int(sp[0] / 12), axis=0)

# Compute lapse rate and uniform warming
ta_pert = np.asarray(model_mainvar_pert[os.environ["ta_var"]])
ta_climo = np.asarray(model_mainvar_climo[os.environ["ta_var"]])
ts_pert = np.asarray(model_mainvar_pert[os.environ["ts_var"]])
ts_climo = np.asarray(model_mainvar_climo[os.environ["ts_var"]])
s = ta_pert.shape

pl_pert = np.repeat(ts_pert[:, np.newaxis, :, :], s[1], axis=1)
s = ta_climo.shape
pl_climo = np.repeat(ts_climo[:, np.newaxis, :, :], s[1], axis=1)

ta_anom = var_anom4D(ta_pert, ta_climo)
pl_anom = var_anom4D(pl_pert, pl_climo)
lr_anom = ta_anom - pl_anom

# Compute Planck Radiative Flux Anomalies
[fluxanom_pl_tot_TOA_tropo, fluxanom_pl_clr_TOA_tropo, fluxanom_pl_tot_TOA_strato, fluxanom_pl_clr_TOA_strato] = \
    fluxanom_calc_4D(pl_anom, lw_t_kern_TOA, lwclr_t_kern_TOA, dp_sfc, lev_kern, lat_kern, ps_kern_TOA)

# Compute Surface Temperature (surface Planck) Flux Anomalies
[fluxanom_pl_sfc_tot_TOA, fluxanom_pl_sfc_clr_TOA] = fluxanom_calc_3D(ts_pert, ts_climo, lw_ts_kern_TOA,
                                                                      lwclr_ts_kern_TOA)

# Comput Lapse Rate Radiative Flux Anomalies
[fluxanom_lr_tot_TOA_tropo, fluxanom_lr_clr_TOA_tropo, fluxanom_lr_tot_TOA_strato, fluxanom_lr_clr_TOA_strato] = \
    fluxanom_calc_4D(lr_anom, lw_t_kern_TOA, lwclr_t_kern_TOA, dp_sfc, lev_kern, lat_kern, ps_kern_TOA)

# Compute water vapor change
hus_pert = np.asarray(model_mainvar_pert[os.environ["hus_var"]])
hus_pert[hus_pert < 0] = 0
hus_climo = np.asarray(model_mainvar_climo[os.environ["hus_var"]])
hus_climo[hus_climo < 0] = 0

# Calculations necessary to convert units of water vapor change to match kernels
shp = ta_climo.shape
ta_ratio_climo = np.squeeze(np.nanmean(np.reshape(ta_climo, (int(shp[0] / 12), 12, shp[1], shp[2], shp[3])),
                                       axis=0))
es_ratio = esat_coef(ta_ratio_climo + 1) / esat_coef(ta_ratio_climo)

es_ratio_pert = np.reshape(np.repeat(es_ratio[np.newaxis, ...], int(ta_pert.shape[0] / 12), axis=0),
                           (ta_pert.shape[0], shp[1], shp[2], shp[3]))

# Log of water vapor
q_pert = np.log(hus_pert) / (es_ratio_pert - 1)
es_ratio_climo = np.reshape(np.repeat(es_ratio[np.newaxis, ...], int(shp[0] / 12), axis=0),
                            (shp[0], shp[1], shp[2], shp[3]))

q_climo = np.log(hus_climo) / (es_ratio_climo - 1)
es_ratio, ta_ratio_climo, hus_pert, hus_climo, ta_pert, ta_climo = None, None, None, None, None, None

q_anom = var_anom4D(q_pert, q_climo)

# Compute SW Water Vapor Radiative Flux Anomalies

[fluxanom_sw_q_tot_TOA_tropo, fluxanom_sw_q_clr_TOA_tropo, fluxanom_sw_q_tot_TOA_strato, fluxanom_sw_q_clr_TOA_strato] \
    = fluxanom_calc_4D(q_anom, sw_q_kern_TOA, swclr_q_kern_TOA, dp_sfc, lev_kern, lat_kern, ps_kern_TOA)

# Compute LW Water Vapor Radiative Flux Anomalies
[fluxanom_lw_q_tot_TOA_tropo, fluxanom_lw_q_clr_TOA_tropo, fluxanom_lw_q_tot_TOA_strato, fluxanom_lw_q_clr_TOA_strato] \
    = fluxanom_calc_4D(q_anom, lw_q_kern_TOA, lwclr_q_kern_TOA, dp_sfc, lev_kern, lat_kern, ps_kern_TOA)

fluxanom_sw_q_tot_TOA_tropo[fluxanom_sw_q_tot_TOA_tropo == float('Inf')] = np.nan
fluxanom_sw_q_clr_TOA_tropo[fluxanom_sw_q_clr_TOA_tropo == float('Inf')] = np.nan
fluxanom_lw_q_tot_TOA_tropo[fluxanom_lw_q_tot_TOA_tropo == float('Inf')] = np.nan
fluxanom_lw_q_clr_TOA_tropo[fluxanom_lw_q_clr_TOA_tropo == float('Inf')] = np.nan
fluxanom_sw_q_tot_TOA_tropo[fluxanom_sw_q_tot_TOA_tropo == -float('Inf')] = np.nan
fluxanom_sw_q_clr_TOA_tropo[fluxanom_sw_q_clr_TOA_tropo == -float('Inf')] = np.nan
fluxanom_lw_q_tot_TOA_tropo[fluxanom_lw_q_tot_TOA_tropo == -float('Inf')] = np.nan
fluxanom_lw_q_clr_TOA_tropo[fluxanom_lw_q_clr_TOA_tropo == -float('Inf')] = np.nan

fluxanom_sw_q_tot_TOA_strato[fluxanom_sw_q_tot_TOA_strato == float('Inf')] = np.nan
fluxanom_sw_q_clr_TOA_strato[fluxanom_sw_q_clr_TOA_strato == float('Inf')] = np.nan
fluxanom_lw_q_tot_TOA_strato[fluxanom_lw_q_tot_TOA_strato == float('Inf')] = np.nan
fluxanom_lw_q_clr_TOA_strato[fluxanom_lw_q_clr_TOA_strato == float('Inf')] = np.nan
fluxanom_sw_q_tot_TOA_strato[fluxanom_sw_q_tot_TOA_strato == -float('Inf')] = np.nan
fluxanom_sw_q_clr_TOA_strato[fluxanom_sw_q_clr_TOA_strato == -float('Inf')] = np.nan
fluxanom_lw_q_tot_TOA_strato[fluxanom_lw_q_tot_TOA_strato == -float('Inf')] = np.nan
fluxanom_lw_q_clr_TOA_strato[fluxanom_lw_q_clr_TOA_strato == -float('Inf')] = np.nan

# Compute surface albedo change
alb_pert_tot = np.asarray(model_mainvar_pert[os.environ["rsus_var"]] / model_mainvar_pert[os.environ["rsds_var"]])
alb_climo_tot = np.asarray(model_mainvar_climo[os.environ["rsus_var"]] / model_mainvar_climo[os.environ["rsds_var"]])
alb_pert_clr = np.asarray(model_mainvar_pert[os.environ["rsuscs_var"]] / model_mainvar_pert[os.environ["rsdscs_var"]])
alb_climo_clr = np.asarray(
    model_mainvar_climo[os.environ["rsuscs_var"]] / model_mainvar_climo[os.environ["rsdscs_var"]])

alb_pert_tot[np.isinf(alb_pert_tot)] = 0
alb_climo_tot[np.isinf(alb_climo_tot)] = 0
alb_pert_clr[np.isinf(alb_pert_clr)] = 0
alb_climo_clr[np.isinf(alb_climo_clr)] = 0
alb_pert_tot[alb_pert_tot > 1] = 0
alb_pert_tot[alb_pert_tot < 0] = 0
alb_climo_tot[alb_climo_tot > 1] = 0
alb_climo_tot[alb_climo_tot < 0] = 0
alb_pert_clr[alb_pert_clr > 1] = 0
alb_pert_clr[alb_pert_clr < 0] = 0
alb_climo_clr[alb_climo_clr > 1] = 0
alb_climo_clr[alb_climo_clr < 0] = 0
# Compute Surface Albedo Radiative Flux Anomalies


[fluxanom_a_sfc_tot_TOA, fluxanom_a_sfc_clr_TOA] = \
    fluxanom_calc_3D(alb_pert_tot, alb_climo_tot, sw_a_kern_TOA / .01, swclr_a_kern_TOA / .01, alb_pert_clr,
                     alb_climo_clr)

# Compute NET Radiative Flux Anomalies
Rtot_LW_TOA_pert = np.asarray(-model_mainvar_pert[os.environ["rlut_var"]])
Rtot_SW_TOA_pert = np.asarray(model_mainvar_pert[os.environ["rsdt_var"]] - model_mainvar_pert[os.environ["rsut_var"]])
Rtot_LW_TOA_climo = np.asarray(-model_mainvar_climo[os.environ["rlut_var"]])
Rtot_SW_TOA_climo = np.asarray(
    model_mainvar_climo[os.environ["rsdt_var"]] - model_mainvar_climo[os.environ["rsut_var"]])
Rclr_LW_TOA_pert = np.asarray(-model_mainvar_pert[os.environ["rlutcs_var"]])
Rclr_SW_TOA_pert = np.asarray(model_mainvar_pert[os.environ["rsdt_var"]] - model_mainvar_pert[os.environ["rsutcs_var"]])
Rclr_LW_TOA_climo = np.asarray(-model_mainvar_climo[os.environ["rlutcs_var"]])
Rclr_SW_TOA_climo = np.asarray(
    model_mainvar_climo[os.environ["rsdt_var"]] - model_mainvar_climo[os.environ["rsutcs_var"]])

# TOA
[fluxanom_Rtot_LW_TOA, fluxanom_Rclr_LW_TOA] = \
    fluxanom_calc_3D(Rtot_LW_TOA_pert, Rtot_LW_TOA_climo, np.ones(lw_ts_kern_TOA.shape),
                     np.ones(lwclr_ts_kern_TOA.shape),
                     Rclr_LW_TOA_pert, Rclr_LW_TOA_climo)

[fluxanom_Rtot_SW_TOA, fluxanom_Rclr_SW_TOA] = \
    fluxanom_calc_3D(Rtot_SW_TOA_pert, Rtot_SW_TOA_climo, np.ones(lw_ts_kern_TOA.shape),
                     np.ones(lwclr_ts_kern_TOA.shape),
                     Rclr_SW_TOA_pert, Rclr_SW_TOA_climo)
# TOA CRE
fluxanom_Rcre_LW_TOA = fluxanom_Rtot_LW_TOA - fluxanom_Rclr_LW_TOA
fluxanom_Rcre_SW_TOA = fluxanom_Rtot_SW_TOA - fluxanom_Rclr_SW_TOA

# Compute Instantaneous Radiative Forcing as difference between NET Radiative Flux Anomalies and
# the sum of all individual radiative flux anomalies. Total-sky IRF computed as
# Clear-Sky IRF divided by cloud masking constant. NOTE, these cloud masking constants may not apply
# to user's specific model experiment.
IRF_lw_clr_TOA = fluxanom_Rclr_LW_TOA - fluxanom_pl_clr_TOA_tropo - fluxanom_lr_clr_TOA_tropo - \
                 fluxanom_lw_q_clr_TOA_tropo - fluxanom_pl_sfc_clr_TOA - fluxanom_pl_clr_TOA_tropo - \
                 fluxanom_lr_clr_TOA_strato - fluxanom_lw_q_clr_TOA_strato
IRF_lw_tot_TOA = IRF_lw_clr_TOA / np.double(os.environ["LW_CLOUDMASK"])
IRF_sw_clr_TOA = (fluxanom_Rclr_SW_TOA - fluxanom_sw_q_clr_TOA_tropo - fluxanom_a_sfc_clr_TOA -
                  fluxanom_sw_q_clr_TOA_strato)
IRF_sw_tot_TOA = IRF_sw_clr_TOA / np.double(os.environ["SW_CLOUDMASK"])

# Compute Cloud Radiative Flux Anomalies as dCRE minus correction for cloud masking using
# kernel-derived IRF and individual flux anomalies (See e.g. Soden et al. 2008)

fluxanom_lw_c_TOA = fluxanom_Rcre_LW_TOA - (fluxanom_pl_tot_TOA_tropo - fluxanom_pl_clr_TOA_tropo) \
                    - (fluxanom_pl_tot_TOA_strato - fluxanom_pl_clr_TOA_strato) \
                    - (fluxanom_pl_sfc_tot_TOA - fluxanom_pl_sfc_clr_TOA) \
                    - (fluxanom_lr_tot_TOA_tropo - fluxanom_lr_clr_TOA_tropo) \
                    - (fluxanom_lr_tot_TOA_strato - fluxanom_lr_clr_TOA_strato) \
                    - (fluxanom_lw_q_tot_TOA_tropo - fluxanom_lw_q_clr_TOA_tropo) \
                    - (fluxanom_lw_q_tot_TOA_strato - fluxanom_lw_q_clr_TOA_strato) \
                    - (IRF_lw_tot_TOA - IRF_lw_clr_TOA)

fluxanom_sw_c_TOA = fluxanom_Rcre_SW_TOA - (fluxanom_sw_q_tot_TOA_tropo - fluxanom_sw_q_clr_TOA_tropo) \
                    - (fluxanom_sw_q_tot_TOA_strato - fluxanom_sw_q_clr_TOA_strato) \
                    - (fluxanom_a_sfc_tot_TOA - fluxanom_a_sfc_clr_TOA) \
                    - (IRF_sw_tot_TOA - IRF_sw_clr_TOA)

# Regress radiative flux anomalies with global-mean dTs to compute feedbacks
# within feedback_regress function, results saved to a netcdf

# Planck Feedback
feedback_regress(fluxanom_pl_tot_TOA_tropo + fluxanom_pl_sfc_tot_TOA, ts_pert, ts_climo, lat_kern, lon_kern,
                 'Planck')

# Lapse Rate Feedback
feedback_regress(fluxanom_lr_tot_TOA_tropo, ts_pert, ts_climo, lat_kern, lon_kern, 'LapseRate')

# LW Water vapor Feedback
feedback_regress(fluxanom_lw_q_tot_TOA_tropo, ts_pert, ts_climo, lat_kern, lon_kern, 'LW_WaterVapor')

# SW Water vapor Feedback
feedback_regress(fluxanom_sw_q_tot_TOA_tropo, ts_pert, ts_climo, lat_kern, lon_kern, 'SW_WaterVapor')

# Surface Albedo Feedback
feedback_regress(fluxanom_a_sfc_tot_TOA, ts_pert, ts_climo, lat_kern, lon_kern, 'SfcAlbedo')

# Total stratospheric Feedback
feedback_regress(fluxanom_pl_tot_TOA_strato + fluxanom_lr_tot_TOA_strato + fluxanom_lw_q_tot_TOA_strato + \
                 fluxanom_sw_q_tot_TOA_strato, ts_pert, ts_climo, lat_kern, lon_kern, 'StratFB')

# LW Cloud Feedback
feedback_regress(fluxanom_lw_c_TOA, ts_pert, ts_climo, lat_kern, lon_kern, 'LW_Cloud')

# SW Cloud Feedback
feedback_regress(fluxanom_sw_c_TOA, ts_pert, ts_climo, lat_kern, lon_kern, 'SW_Cloud')

# LW Total Radiative Anomalies
feedback_regress(fluxanom_Rtot_LW_TOA, ts_pert, ts_climo, lat_kern, lon_kern, 'LW_Rad')

# SW Total Radiative Anomalies
feedback_regress(fluxanom_Rtot_SW_TOA, ts_pert, ts_climo, lat_kern, lon_kern, 'SW_Rad')

shp = ts_pert.shape
xtime = np.repeat(np.repeat(np.arange(shp[0])[..., np.newaxis], shp[1], axis=1)[..., np.newaxis], shp[2], axis=2)
# LW IRF (trendlines, regressed against time)
feedback_regress(IRF_lw_tot_TOA, xtime, xtime * 0, lat_kern, lon_kern, 'LW_IRF')

# SW IRF (trendlines, regressed against time)
feedback_regress(IRF_sw_tot_TOA, xtime, xtime * 0, lat_kern, lon_kern, 'SW_IRF')
