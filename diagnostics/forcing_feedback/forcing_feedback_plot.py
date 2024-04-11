# This file is part of the forcing_feedback module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

# ======================================================================
# forcing_feedback_plot.py
#
#  Called by forcing_feedback.py
#   Reads in observations and temporary model results of individual 2D feedbacks and IRF, produces maps of each and
#   a bar graph summarizing global-mean values. Also creates a dotplot, comparing results against CMIP6 suite of models
#
#  Forcing Feedback Diagnositic Package
#
#  This file is part of the Forcing and Feedback Diagnostic Package
#    and the MDTF code package. See LICENSE.txt for the license.
#
#

import os
import numpy as np
import xarray as xr
import matplotlib as mpl

mpl.use('Agg')
import matplotlib.pyplot as plt

from forcing_feedback_util import globemean_2D
from forcing_feedback_util import bargraph_plotting
from forcing_feedback_util import map_plotting_4subs
from forcing_feedback_util import map_plotting_2subs

# Read in observational data
nc_obs = xr.open_dataset(os.environ["OBS_DATA"] + "/forcing_feedback_obs.nc")
lat_obs = nc_obs.lat.values
lon_obs = nc_obs.lon.values
llons_obs, llats_obs = np.meshgrid(lon_obs, lat_obs)

# Read in model results

nc_pl = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_Planck.nc")
nc_lr = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_LapseRate.nc")
nc_lw_q = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_LW_WaterVapor.nc")
nc_sw_q = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_SW_WaterVapor.nc")
nc_alb = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_SfcAlbedo.nc")
nc_lw_c = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_LW_Cloud.nc")
nc_sw_c = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_SW_Cloud.nc")
nc_lw_irf = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_LW_IRF.nc")
nc_sw_irf = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_SW_IRF.nc")
nc_lw_netrad = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_LW_Rad.nc")
nc_sw_netrad = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_SW_Rad.nc")
nc_strat = xr.open_dataset(os.environ["WORK_DIR"] + "/model/netCDF/fluxanom2D_StratFB.nc")

lat_model = nc_sw_irf.lat.values
weights_model = np.cos(np.deg2rad(lat_model))
weights_obs = np.cos(np.deg2rad(lat_obs))

# Global-mean barplot comparison
# Figure 1: Total Radiation
LW_RA_Model = globemean_2D(nc_lw_netrad.LW_Rad.values, weights_model)
SW_RA_Model = globemean_2D(nc_sw_netrad.SW_Rad.values, weights_model)
Net_RA_Model = LW_RA_Model + SW_RA_Model
bars1 = [Net_RA_Model, LW_RA_Model, SW_RA_Model]
LW_RA_Obs = globemean_2D(nc_obs.LW_Rad.values, weights_obs)
SW_RA_Obs = globemean_2D(nc_obs.SW_Rad.values, weights_obs)
Net_RA_Obs = LW_RA_Obs + SW_RA_Obs
bars2 = [Net_RA_Obs, LW_RA_Obs, SW_RA_Obs]
units = 'W/$m^2$/K'
legendnames = ['Net Radiation', 'LW Rad', 'SW Rad']
filename = 'Rad'
bargraph_plotting(bars1, bars2, units, legendnames, filename)

# Figure 2: IRF
LW_IRF_Model = 12 * globemean_2D(nc_lw_irf.LW_IRF.values, weights_model)  # converting from W/m2/month to W/m2/yr
SW_IRF_Model = 12 * globemean_2D(nc_sw_irf.SW_IRF.values, weights_model)
Net_IRF_Model = LW_IRF_Model + SW_IRF_Model
bars1 = [Net_IRF_Model, LW_IRF_Model, SW_IRF_Model]
LW_IRF_Obs = 12 * globemean_2D(nc_obs.LW_IRF.values, weights_obs)
SW_IRF_Obs = 12 * globemean_2D(nc_obs.SW_IRF.values, weights_obs)
Net_IRF_Obs = LW_IRF_Obs + SW_IRF_Obs
bars2 = [Net_IRF_Obs, LW_IRF_Obs, SW_IRF_Obs]
units = 'W/$m^2/yr$'
legendnames = ['Net IRF', 'LW IRF', 'SW IRF']
filename = 'IRF'
bargraph_plotting(bars1, bars2, units, legendnames, filename)

# Figure 3: Longwave Radiative Feedbacks
PL_Model = globemean_2D(nc_pl.Planck.values, weights_model)
LR_Model = globemean_2D(nc_lr.LapseRate.values, weights_model)
LWWV_Model = globemean_2D(nc_lw_q.LW_WaterVapor.values, weights_model)
LWC_Model = globemean_2D(nc_lw_c.LW_Cloud.values, weights_model)
bars1 = [PL_Model, LR_Model, LWWV_Model, LWC_Model]
PL_Obs = globemean_2D(nc_obs.Planck.values, weights_obs)
LR_Obs = globemean_2D(nc_obs.LapseRate.values, weights_obs)
LWWV_Obs = globemean_2D(nc_obs.LW_WaterVapor.values, weights_obs)
LWC_Obs = globemean_2D(nc_obs.LW_Cloud.values, weights_obs)
bars2 = [PL_Obs, LR_Obs, LWWV_Obs, LWC_Obs]
units = 'W/$m^2$/K'
legendnames = ['Planck', 'Lapse Rate', 'LW Water Vapor', ' LW Cloud']
filename = 'LWFB'
bargraph_plotting(bars1, bars2, units, legendnames, filename)

# Figure 4: Shortwave Radiative Feedbacks
Alb_Model = globemean_2D(nc_alb.SfcAlbedo.values, weights_model)
SWWV_Model = globemean_2D(nc_sw_q.SW_WaterVapor.values, weights_model)
SWC_Model = globemean_2D(nc_sw_c.SW_Cloud.values, weights_model)
bars1 = [Alb_Model, SWWV_Model, SWC_Model]
Alb_Obs = globemean_2D(nc_obs.SfcAlbedo.values, weights_obs)
SWWV_Obs = globemean_2D(nc_obs.SW_WaterVapor.values, weights_obs)
SWC_Obs = globemean_2D(nc_obs.SW_Cloud.values, weights_obs)
bars2 = [Alb_Obs, SWWV_Obs, SWC_Obs]
units = 'W/$m^2$/K'
legendnames = ['Sfc. Albedo', 'SW Water Vapor', ' SW Cloud']
filename = 'SWFB'
bargraph_plotting(bars1, bars2, units, legendnames, filename)

Strat_Model = globemean_2D(nc_strat.StratFB.values, weights_model)
# Strat_Obs = globemean_2D(nc_obs.StratFB.values,weights_obs)

# CMIP6 values. IRF already multiplied by 12
CMIP6vals = np.loadtxt(os.environ["OBS_DATA"] + "/CldFB_MDTF.txt")

# Create scatter plot with CMIP6 data. One iteration only
plt.figure(1)
f, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})
# Add in each CMIP6 value model-by-model
for m in range(CMIP6vals.shape[0] - 1):
    ax1.scatter(np.arange(CMIP6vals.shape[1] - 1), CMIP6vals[m, :-1], c='k', label='_nolegend_')
# For legend purposes, add in last CMIP6 model separately
ax1.scatter(np.arange(CMIP6vals.shape[1] - 1), CMIP6vals[m + 1, :-1], c='k', label='CMIP6 (Hist. 2003-2014)')
# Add in values from POD user's model
ax1.scatter(np.arange(CMIP6vals.shape[1] - 1), np.asarray([Net_RA_Model, LWC_Model + SWC_Model,
                                                           PL_Model + LR_Model + LWWV_Model + SWWV_Model + Alb_Model]),
            c='b', label='Your Model')
# Add in Observational Values
ax1.scatter(np.arange(CMIP6vals.shape[1] - 1), np.asarray([Net_RA_Obs,
                                                           LWC_Obs + SWC_Obs,
                                                           PL_Obs + LR_Obs + LWWV_Obs + SWWV_Obs + Alb_Obs]), c='r',
            label='Obs.')
# Creating axis labels for dotplot
ax1.set_ylabel('W/$m^2$/K')
xterms = ['$\Delta{R}_{tot}$', '$\lambda_{cloud}$', '$\lambda_{noncloud}$']
ax1.set_xticks([r for r in range(CMIP6vals.shape[1] - 1)], xterms)
ax1.legend(loc='lower center')
for m in range(CMIP6vals.shape[0]):
    ax2.scatter(1, CMIP6vals[m, -1], c='k', label='_nolegend_')
ax2.scatter(1, Net_IRF_Model, c='b', label='_nolegend_')
ax2.scatter(1, Net_IRF_Obs, c='r', label='_nolegend_')
ax2.set_ylabel('W/$m^2$/yr')
xterms = ['', 'IRF', '']
ax2.set_xticks([r for r in range(len(xterms))], xterms)
plt.tight_layout()
plt.savefig(os.environ['WORK_DIR'] + '/model/PS/forcing_feedback_CMIP6scatter.eps')
plt.close()

if np.max(nc_sw_irf.lon.values) >= 300:  # convert 0-360 lon to -180-180 lon for plotting
    lon1 = np.mod((nc_sw_irf.lon.values + 180), 360) - 180
    lon1a = lon1[0:int(len(lon1) / 2)]
    lon1b = lon1[int(len(lon1) / 2):]
    lon_model = np.concatenate((lon1b, lon1a))
else:
    lon_model = nc_sw_irf.lon.values
llons_model, llats_model = np.meshgrid(lon_model, lat_model)

lon_originalmodel = nc_sw_irf.lon.values

# Produce maps of the radiative feedbacks and IRF tends, comparing model results to observations

# Temperature Feedback
levels_1 = np.arange(-6, 6.0001, 1)
variablename_1 = 'Planck'
modelvariable_1 = nc_pl.Planck.values
obsvariable_1 = nc_obs.Planck.values
levels_2 = np.arange(-6, 6.0001, 1)
variablename_2 = 'Lapse Rate'
modelvariable_2 = nc_lr.LapseRate.values
obsvariable_2 = nc_obs.LapseRate.values
units = 'W/$m^2$/K'
filename = 'Temperature'
map_plotting_4subs(levels_1, levels_2, variablename_1, modelvariable_1, lon_originalmodel,
                   lon_model, lat_model, lon_obs, lat_obs, obsvariable_1, variablename_2,
                   modelvariable_2, obsvariable_2, units, filename)

# Water Vapor Feedback
levels_1 = np.arange(-6, 6.0001, 1)
variablename_1 = 'LW Water Vapor'
modelvariable_1 = nc_lw_q.LW_WaterVapor.values
obsvariable_1 = nc_obs.LW_WaterVapor.values
levels_2 = np.arange(-1, 1.0001, 0.2)
variablename_2 = 'SW Water Vapor'
modelvariable_2 = nc_sw_q.SW_WaterVapor.values
obsvariable_2 = nc_obs.SW_WaterVapor.values
units = 'W/$m^2$/K'
filename = 'WaterVapor'
map_plotting_4subs(levels_1, levels_2, variablename_1, modelvariable_1, lon_originalmodel,
                   lon_model, lat_model, lon_obs, lat_obs, obsvariable_1,
                   variablename_2, modelvariable_2, obsvariable_2, units, filename)

# Surface Albedo Feedback
levels_1 = np.arange(-6, 6.0001, 1)
variablename_1 = 'Sfc. Albedo'
modelvariable_1 = nc_alb.SfcAlbedo.values
obsvariable_1 = nc_obs.SfcAlbedo.values
units = 'W/$m^2$/K'
filename = 'SfcAlbedo'
map_plotting_2subs(levels_1, variablename_1, modelvariable_1, lon_originalmodel,
                   lon_model, lat_model, lon_obs, lat_obs, obsvariable_1, units, filename)

# Cloud Feedback
levels_1 = np.arange(-16, 16.0001, 2)
variablename_1 = 'LW Cloud'
modelvariable_1 = nc_lw_c.LW_Cloud.values
obsvariable_1 = nc_obs.LW_Cloud.values
levels_2 = np.arange(-16, 16.0001, 2)
variablename_2 = 'SW Cloud'
modelvariable_2 = nc_sw_c.SW_Cloud.values
obsvariable_2 = nc_obs.SW_Cloud.values
units = 'W/$m^2$/K'
filename = 'Cloud'
map_plotting_4subs(levels_1, levels_2, variablename_1, modelvariable_1, lon_originalmodel,
                   lon_model, lat_model, lon_obs, lat_obs, obsvariable_1,
                   variablename_2, modelvariable_2, obsvariable_2, units, filename)

# Rad Feedback
levels_1 = np.arange(-24, 24.0001, 2)
variablename_1 = 'LW Total Rad'
modelvariable_1 = nc_lw_netrad.LW_Rad.values
obsvariable_1 = nc_obs.LW_Rad.values
levels_2 = np.arange(-24, 24.0001, 2)
variablename_2 = 'SW Total Rad'
modelvariable_2 = nc_sw_netrad.SW_Rad.values
obsvariable_2 = nc_obs.SW_Rad.values
units = 'W/$m^2$/K'
filename = 'Rad'
map_plotting_4subs(levels_1, levels_2, variablename_1, modelvariable_1, lon_originalmodel,
                   lon_model, lat_model, lon_obs, lat_obs, obsvariable_1,
                   variablename_2, modelvariable_2, obsvariable_2, units, filename)

# IRF Trend
# levels_1 = np.arange(-0.015,0.0150001,0.0015)
levels_1 = np.arange(-0.030, 0.0300001, 0.0030)
variablename_1 = 'LW IRF'
modelvariable_1 = 12 * nc_lw_irf.LW_IRF.values
obsvariable_1 = 12 * nc_obs.LW_IRF.values
# levels_2 = np.arange(-0.015,0.0150001,0.0015)
levels_2 = np.arange(-0.030, 0.0300001, 0.0030)
variablename_2 = 'SW IRF'
modelvariable_2 = 12 * nc_sw_irf.SW_IRF.values
obsvariable_2 = 12 * nc_obs.SW_IRF.values
units = 'W/$m^2$/yr'
filename = 'IRF'
map_plotting_4subs(levels_1, levels_2, variablename_1, modelvariable_1, lon_originalmodel,
                   lon_model, lat_model, lon_obs, lat_obs, obsvariable_1,
                   variablename_2, modelvariable_2, obsvariable_2, units, filename)
