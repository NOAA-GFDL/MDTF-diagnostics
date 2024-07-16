# This file is part of the forcing_feedback module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

# ======================================================================
# forcing_feedback_util_tropseperate.py
#
# Provide functions called by forcing_feedback.py
#
# This file is part of the Forcing Feedback Diagnostic Package and the
# MDTF code package. See LICENSE.txt for the license.
#
# Including:
#  (1) fluxanom_calc_4D
#  (2) fluxanom_calc_3D
#  (3) esat_coef
#  (4) latlonr3_3D4D
#  (5) globemean_2D
#  (6) globemean_3D
#  (7) fluxanom_nc_create
#  (8) feedback_regress
#  (9) bargraph_plotting
#  (10) map_plotting_4subs
#  (11) map_plotting_2subs
#
# ======================================================================
# Import standard Python packages

import os
import numpy as np
import numpy.ma as ma
import dask.array as da
import xarray as xr
from scipy.interpolate import griddata
import matplotlib as mpl

mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LATITUDE_FORMATTER
from cartopy.util import add_cyclic_point


# =======================================================
# var_anom4D

def var_anom4D(var_pert, var_base):
    sp = var_pert.shape
    sb = var_base.shape

    if len(sp) != 4 or len(sb) != 4:
        print("An input variable is not 4D! Function will not execute")
    else:

        # Prep variable to analyze on a monthly-basis

        var_pert_re = np.reshape(var_pert, (int(sp[0] / 12), 12, sp[1], sp[2], sp[3]))
        var_base_re = np.reshape(var_base, (int(sb[0] / 12), 12, sb[1], sb[2], sb[3]))
        var_base_tmean = np.repeat(np.squeeze(np.nanmean(var_base_re, axis=0))[np.newaxis, :, :, :], \
                                   int(sp[0] / 12), axis=0)
        var_anom = da.from_array(var_pert_re - var_base_tmean, chunks=(5, 5, sp[1], sp[2], sp[3]))

    return var_anom


# ======================================================================
# fluxanom_calc_4D

def fluxanom_calc_4D(var_anom, tot_kern, clr_kern, dpsfc, levs, lats, psk):
    """
    Computes anomalies of radiatively-relevant 4D climate variables and multiplies
    by radiative kernel to convert to radiative flux change. Performs clear- and
    all-sky calculations

    """

    # Pressure of upper boundary of each vertical layer
    pt = (levs[1:] + levs[:-1]) / 2
    pt = np.append(pt, 0)
    # Pressure of lower boundary of each vertical layer
    pb = pt[:-1]
    pb = np.insert(pb, 0, 1000)
    # Pressure thickness of each vertical level
    dp = pb - pt

    sp = var_anom.shape

    # Create indices to seperate troposphere from stratosphere
    frac_tropo = np.zeros((sp[0], sp[1], sp[2] - 1, sp[3], sp[4]))
    frac_strato = np.zeros((sp[0], sp[1], sp[2] - 1, sp[3], sp[4]))
    tropopause = (100 + np.absolute(lats) * 200 / 90)
    tropopause_mat = np.tile(tropopause, (sp[0], sp[1], sp[2] - 1, sp[4], 1)).transpose(0, 1, 2, 4, 3)
    ptop_mat = np.tile(pt[1:], (sp[0], sp[1], sp[3], sp[4], 1)).transpose(0, 1, 4, 2, 3)
    pbot_mat = np.tile(pb[1:], (sp[0], sp[1], sp[3], sp[4], 1)).transpose(0, 1, 4, 2, 3)
    psk_mat = np.tile(psk, (sp[0], sp[2] - 1, 1, 1, 1)).transpose(0, 2, 1, 3, 4)

    frac_tropo[(pbot_mat <= psk_mat) & (ptop_mat >= tropopause_mat)] = 1
    frachold = (pbot_mat - tropopause_mat) / (pbot_mat - ptop_mat)
    frac_tropo[(pbot_mat >= tropopause_mat) & (ptop_mat <= tropopause_mat)] = frachold[
        (pbot_mat >= tropopause_mat) & (ptop_mat <= tropopause_mat)]
    frachold = (psk_mat - ptop_mat) / (pbot_mat - ptop_mat)
    frac_tropo[(pbot_mat >= psk_mat) & (ptop_mat <= psk_mat)] = frachold[(pbot_mat >= psk_mat) & (ptop_mat <= psk_mat)]

    frachold = (tropopause_mat - ptop_mat) / (pbot_mat - ptop_mat)
    frac_strato[(pbot_mat >= tropopause_mat) & (ptop_mat <= tropopause_mat)] = frachold[
        (pbot_mat >= tropopause_mat) & (ptop_mat <= tropopause_mat)]
    frac_strato[(pbot_mat <= tropopause_mat) & (ptop_mat <= tropopause_mat)] = 1
    frachold, tropopause_mat, ptop_mat, pbot_mat, psk_mat = None, None, None, None, None

    if len(sp) != 5:
        print("An input variable is not 4D! Function will not execute")
    else:

        tot_kern = da.from_array(np.squeeze(np.repeat(tot_kern[np.newaxis, ...], sp[0], axis=0)),
                                 chunks=(5, 5, sp[2], sp[3], sp[4]))
        clr_kern = da.from_array(np.squeeze(np.repeat(clr_kern[np.newaxis, ...], sp[0], axis=0)),
                                 chunks=(5, 5, sp[2], sp[3], sp[4]))
        dp_mat = da.from_array(np.squeeze(np.repeat(np.repeat(np.repeat(np.repeat( \
            dp[np.newaxis, 1:], 12, axis=0)[np.newaxis, ...], sp[0], axis=0)[:, :, :, np.newaxis], \
                                                              sp[3], axis=3)[:, :, :, :, np.newaxis], sp[4], axis=4)),
                               chunks=(5, 5, sp[2], sp[3], sp[4]))
        frac_tropo = da.from_array(frac_tropo, chunks=(5, 5, sp[2], sp[3], sp[4]))
        frac_strato = da.from_array(frac_strato, chunks=(5, 5, sp[2], sp[3], sp[4]))
        dpsfc = da.from_array(dpsfc, chunks=(5, 5, sp[3], sp[4]))

        # Calculate flux anomaly for all levels except first level above surface - total-sky, troposphere
        flux_tot_tropo = (tot_kern[:, :, 1:, :, :] * frac_tropo * dp_mat * var_anom[:, :, 1:, :, :] / 100)
        flux_tot_strato = (tot_kern[:, :, 1:, :, :] * frac_strato * dp_mat * var_anom[:, :, 1:, :, :] / 100)

        # Calculate flux anomaly for level above surface

        flux_tot_tropo_bottom = (tot_kern[:, :, 0, :, :] \
                                 * dpsfc * var_anom[:, :, 0, :, :] / 100)

        flux_tot_strato_bottom = (tot_kern[:, :, 0, :, :] \
                                  * dpsfc * var_anom[:, :, 0, :, :] / 100)

        # Calculate flux anomaly for all levels except first level above surface - clear-sky, troposphere
        flux_clr_tropo = (clr_kern[:, :, 1:, :, :] * frac_tropo * dp_mat * var_anom[:, :, 1:, :, :] / 100)

        flux_clr_strato = (clr_kern[:, :, 1:, :, :] * frac_tropo * dp_mat * var_anom[:, :, 1:, :, :] / 100)

        # Calculate flux anomaly for level above surface
        flux_clr_tropo_bottom = (clr_kern[:, :, 0, :, :] \
                                 * dpsfc * var_anom[:, :, 0, :, :] / 100)

        flux_clr_strato_bottom = (clr_kern[:, :, 0, :, :] \
                                  * dpsfc * var_anom[:, :, 0, :, :] / 100)

    frac_tropo, frac_strato = None, None

    # Reshape fluxanom variables and vertically integrate
    flux_tot_tropo = da.append(flux_tot_tropo, flux_tot_tropo_bottom[:, :, np.newaxis, ...], axis=2)
    flux_tot_strato = da.append(flux_tot_strato, flux_tot_strato_bottom[:, :, np.newaxis, ...], axis=2)
    flux_tot_strato = da.append(flux_tot_strato, flux_tot_strato_bottom[:, :, np.newaxis, ...], axis=2)
    flux_tot_strato = da.append(flux_tot_strato, flux_tot_strato_bottom[:, :, np.newaxis, ...], axis=2)

    flux_tot_tropo = np.reshape(np.squeeze(np.nansum(flux_tot_tropo, axis=2)), (sp[0] * sp[1], sp[3], sp[4]))
    flux_clr_tropo = np.reshape(np.squeeze(np.nansum(flux_clr_tropo, axis=2)), (sp[0] * sp[1], sp[3], sp[4]))
    flux_tot_strato = np.reshape(np.squeeze(np.nansum(flux_tot_strato, axis=2)), (sp[0] * sp[1], sp[3], sp[4]))
    flux_clr_strato = np.reshape(np.squeeze(np.nansum(flux_clr_strato, axis=2)), (sp[0] * sp[1], sp[3], sp[4]))

    return np.asarray(flux_tot_tropo), np.asarray(flux_clr_tropo), np.asarray(flux_tot_strato), np.asarray(
        flux_clr_strato)


# ======================================================================
# fluxanom_calc_3D

def fluxanom_calc_3D(var_pert_tot, var_base_tot, tot_kern, clr_kern, var_pert_clr=None, var_base_clr=None):
    """

    Computes anomalies of radiatively-relevant 3D climate variable and multiplies
    by radiative kernel to convert to radiative flux change. Clear- and all-sky calculations
    Note var_*_clr not always used. Specifically an option for clear-sky albedo calculations.

    """

    sp = var_pert_tot.shape
    sb = var_base_tot.shape
    skt = tot_kern.shape
    skc = clr_kern.shape

    flux_sfc_tot = np.zeros((int(sp[0] / 12), 12, sp[1], sp[2]))
    flux_sfc_clr = np.zeros((int(sp[0] / 12), 12, sp[1], sp[2]))
    if len(skt) != 3 or len(skc) != 3 or len(sp) != 3 or len(sb) != 3:
        print("An input variable is not 3D! Function will not execute")
    else:

        # Prep variable to analyze on a monthly-basis
        var_pert_tot_re = np.reshape(var_pert_tot, (int(sp[0] / 12), 12, sp[1], sp[2]))
        var_base_tot_re = np.reshape(var_base_tot, (int(sb[0] / 12), 12, sb[1], sb[2]))

        if var_pert_clr is not None:
            var_pert_clr_re = np.reshape(var_pert_clr, (int(sp[0] / 12), 12, sp[1], sp[2]))
        if var_base_clr is not None:
            var_base_clr_re = np.reshape(var_base_clr, (int(sb[0] / 12), 12, sb[1], sb[2]))

        for m in range(0, 12):

            # Conduct calculations by month, using m index to isolate data accordingly
            # Create climatology by average all timesteps in the var_base variable
            var_base_tot_m_tmean = np.squeeze(np.nanmean(var_base_tot_re[:, m, :, :], axis=0))
            var_pert_tot_m = np.squeeze(var_pert_tot_re[:, m, :, :])

            if var_base_clr is not None:
                var_base_clr_m_tmean = np.squeeze(np.mean(var_base_clr_re[:, m, :, :], axis=0))
                var_pert_clr_m = np.squeeze(var_pert_clr_re[:, m, :, :])

            # Compute anomalies
            var_tot_anom = var_pert_tot_m - np.repeat(var_base_tot_m_tmean[np.newaxis, :, :], int(sp[0] / 12), axis=0)

            if var_base_clr is not None:
                var_clr_anom = var_pert_clr_m - np.repeat(var_base_clr_m_tmean[np.newaxis, :, :], int(sp[0] / 12),
                                                          axis=0)

            # Compute flux anomaly - total-sky
            flux_sfc_tot[:, m, :, :] = np.squeeze(
                np.repeat(tot_kern[np.newaxis, m, :, :], int(sp[0] / 12), axis=0)) * var_tot_anom

            # Compute flux anomaly - clear-sky
            if var_base_clr is not None:
                flux_sfc_clr[:, m, :, :] = np.squeeze(
                    np.repeat(clr_kern[np.newaxis, m, :, :], int(sp[0] / 12), axis=0)) * var_clr_anom
            else:
                flux_sfc_clr[:, m, :, :] = np.squeeze(
                    np.repeat(clr_kern[np.newaxis, m, :, :], int(sp[0] / 12), axis=0)) * var_tot_anom

    # Reshape flux anomalies
    flux_sfc_tot = np.reshape(flux_sfc_tot, (sp[0], sp[1], sp[2]))
    flux_sfc_clr = np.reshape(flux_sfc_clr, (sp[0], sp[1], sp[2]))

    return flux_sfc_tot, flux_sfc_clr


# ======================================================================
# esat_coef

def esat_coef(temp):
    """

    Computes the saturation vapor pressure coefficient necessary for water vapor
    radiative flux calculations

    """

    tc = temp - 273
    aw = np.array([6.11583699, 0.444606896, 0.143177157e-01,
                   0.264224321e-03, 0.299291081e-05, 0.203154182e-07,
                   0.702620698e-10, 0.379534310e-13, -0.321582393e-15])
    ai = np.array([6.11239921, 0.443987641, 0.142986287e-01,
                   0.264847430e-03, 0.302950461e-05, 0.206739458e-07,
                   0.640689451e-10, -0.952447341e-13, -0.976195544e-15])
    esat_water = aw[0]
    esat_ice = ai[0]

    for z in range(1, 9):
        esat_water = esat_water + aw[z] * (tc ** (z))
        esat_ice = esat_ice + ai[z] * (tc ** (z))

    esat = esat_ice
    b = np.where(tc > 0)
    esat[b] = esat_water[b]

    return esat


# ======================================================================
# latlonr3_3D4D
#

def latlonr3_3D4D(variable, lat_start, lon_start, lat_end, lon_end, kern):
    """

    Reformats, reorders and regrids lat,lon so model data matches kernel data grid

    """

    # Check of start and end lat is in similar order. If not, flip.
    if ((lat_start[0] > lat_start[-1]) and (lat_end[0] < lat_end[-1])) or \
            ((lat_start[0] < lat_start[-1]) and (lat_end[0] > lat_end[-1])):
        lat_start = np.flipud(lat_start)
        variable = variable[..., ::-1, :]

    # Check if start and end lon both are 0-360 or both -180-180.  If not, make them the same
    if ((np.max(lon_start) >= 300) and (np.max(lon_end) > 100 and np.max(lon_end) < 300)):

        lon1 = np.mod((lon_start + 180), 360) - 180

        lon1a = lon1[0:len(lon1) / 2]
        lon1b = lon1[len(lon1) / 2:]
        start1a = variable[..., 0:len(lon1) / 2]
        start1b = variable[..., len(lon1) / 2:]
        lon_start = np.concatenate((lon1b, lon1a))
        variable = np.concatenate((start1b, start1a), axis=-1)
    elif ((np.max(lon_start) > 100 and np.max(lon_start) < 300) and (np.max(lon_end) >= 300)):
        lon1 = np.mod(lon_start, 360)

        lon1a = lon1[0:len(lon1) / 2]
        lon1b = lon1[len(lon1) / 2:]
        start1a = variable[..., 0:len(lon1) / 2]
        start1b = variable[..., len(lon1) / 2:]
        lon_start = np.concatenate((lon1b, lon1a))
        variable = np.concatenate((start1b, start1a), axis=-1)

    # If, after above change (or after skipping that step), start and lat are in different order, flip.
    if ((lon_start[0] > lon_start[-1]) and (lon_end[0] < lon_end[-1])) or \
            ((lon_start[0] < lon_start[-1]) and (lon_end[0] > lon_end[-1])):
        lon_start = np.flipud(lon_start)
        variable = variable[..., ::-1]

    # Now that latitudes and longitudes have similar order and format, regrid.
    Y_start, X_start = np.meshgrid(lat_start, lon_start)
    Y_kern, X_kern = np.meshgrid(lat_end, lon_end)

    if len(variable.shape) == 3:  # For 3D data
        shp_start = variable.shape
        shp_kern = kern.shape
        variable_new = np.empty((shp_start[0], shp_kern[1], shp_kern[2])) * np.nan
        for kk in range(shp_start[0]):
            variable_new[kk, :, :] = griddata((Y_start.flatten(), \
                                               X_start.flatten()), np.squeeze(variable[kk, :, :]).T.flatten(), \
                                              (Y_kern.flatten(), X_kern.flatten()), fill_value=np.nan).reshape(
                shp_kern[2], shp_kern[1]).T
    elif len(variable.shape) == 4:  # For 4D data
        shp_start = variable.shape
        shp_kern = kern.shape
        variable_new = np.empty((shp_start[0], shp_start[1], shp_kern[2], shp_kern[3])) * np.nan
        for ll in range(shp_start[1]):
            for kk in range(shp_start[0]):
                variable_new[kk, ll, :, :] = griddata((Y_start.flatten(),
                                                       X_start.flatten()),
                                                      np.squeeze(variable[kk, ll, :, :]).T.flatten(),
                                                      (Y_kern.flatten(), X_kern.flatten()), fill_value=np.nan).reshape(
                    shp_kern[3], shp_kern[2]).T

    return variable_new


# ======================================================================
# globemean_2D
#

def globemean_2D(var, w):
    """

    Compute cosine weighted global-mean over a 2D variable

    """

    var_mask = ma.masked_array(var, ~np.isfinite(var))
    var_mean = np.squeeze(np.average(np.nanmean(var_mask, axis=1), weights=w))

    return var_mean


# ======================================================================
# globemean_3D
#

def globemean_3D(var, w):
    """

    Compute cosine weighted global-mean over a 3D variable

    """

    var_mask = ma.masked_array(var, ~np.isfinite(var))
    var_mean = np.squeeze(np.average(np.nanmean(var_mask, axis=2), axis=1, weights=w))

    return var_mean


# ======================================================================
# fluxanom_nc_create
#

def fluxanom_nc_create(variable, lat, lon, fbname):
    """

    Saves 2D feedback or forcing variables into a NetCDF

    """
    var = xr.DataArray(variable, coords=[lat, lon], dims=['lat', 'lon'], name=fbname)
    var.to_netcdf(os.environ['WORK_DIR'] + '/model/netCDF/fluxanom2D_' + fbname + '.nc')

    return None


# ======================================================================
# feedback_regress
#
# Regeresses radiative flux anomalies with global-mean dTs to compute 2D feedback
def feedback_regress(fluxanom, tspert, tsclimo, lat, lon, fbname):
    """

    Regresses radiative flux anomalies with global-mean dTs to compute 2D feedback


    """

    sp = tspert.shape
    sc = tsclimo.shape

    tsclimo_re = np.squeeze(np.nanmean(np.reshape(tsclimo, \
                                                  (int(sc[0] / 12), 12, sc[1], sc[2])), axis=0))

    tsanom = tspert - np.reshape(np.repeat(tsclimo_re[np.newaxis, ...], int(sp[0] / 12), \
                                           axis=0), (sp[0], sp[1], sp[2]))

    weights = np.repeat(np.cos(np.deg2rad(lat))[np.newaxis, :], sp[0], axis=0)
    tsanom_globemean = globemean_3D(tsanom, weights)
    tsanom_re = np.repeat(np.repeat(tsanom_globemean[:, np.newaxis], \
                                    sp[1], axis=1)[..., np.newaxis], sp[2], axis=2)

    tsanom_re_timemean = np.nanmean(tsanom_re, axis=0)
    tsanom_re_std = np.nanstd(tsanom_re, axis=0)
    fluxanom_timemean = np.nanmean(fluxanom, axis=0)

    n = np.sum(~np.isnan(tsanom_re), axis=0)
    cov = np.nansum((tsanom_re - tsanom_re_timemean) * \
                    (fluxanom - fluxanom_timemean), axis=0) / n
    slopes = cov / (tsanom_re_std ** 2)

    fluxanom_nc_create(slopes, lat, lon, fbname)

    return slopes


# ======================================================================
# bargraph_plotting
#

def bargraph_plotting(model_bar, obs_bar, var_units, var_legnames, var_filename):
    """

    Used for plotting the first four figures generated by forcing_feedback_plots.py.
    Shows global-mean results from the model and observations

    """

    barWidth = 0.125
    r1 = np.arange(len(model_bar))
    r2 = [x + barWidth for x in r1]
    plt.bar(r1, model_bar, color='blue', width=barWidth, edgecolor='white', \
            label='Model')
    plt.bar(r2, obs_bar, color='red', width=barWidth, edgecolor='white', \
            label='Observations')
    plt.axhline(0, color='black', lw=1)
    plt.ylabel(var_units)
    plt.xticks([r + barWidth for r in range(len(model_bar))], var_legnames)
    plt.legend(loc="upper right")
    plt.savefig(os.environ['WORK_DIR'] + '/model/PS/forcing_feedback_globemean_' + var_filename + '.eps')
    plt.close()

    return None


# ======================================================================
# map_plotting_4subs
#
# Function for producing figured with 4 subplot maps generated by
# forcing_feedback_plots.py

def map_plotting_4subs(cbar_levs1, cbar_levs2, var1_name, var1_model, \
                       model_origlon, lon_m, lat_m, lon_o, lat_o, var1_obs, var2_name, \
                       var2_model, var2_obs, var_units, var_filename):
    """

    Function for producing figured with 4 subplot maps generated by
    forcing_feedback_plots.py


    """

    fig, axs = plt.subplots(2, 2, subplot_kw=dict(projection= \
                                                      ccrs.PlateCarree(central_longitude=180)), figsize=(8, 8))

    axs[0, 0].set_title(var1_name + ' - Model')
    if np.max(model_origlon) > 300:  # convert 0-360 lon to -180-180 lon for plotting
        start1a = var1_model[..., 0:int(len(model_origlon) / 2)]
        start1b = var1_model[..., int(len(model_origlon) / 2):]
        var1_model = np.concatenate((start1b, start1a), axis=1)
    var1_model, lon_m180 = add_cyclic_point(var1_model, coord=lon_m)
    cs = axs[0, 0].contourf(lon_m180, lat_m, var1_model, cmap=plt.cm.RdBu_r, \
                            transform=ccrs.PlateCarree(), vmin=cbar_levs1[0], \
                            vmax=cbar_levs1[-1], levels=cbar_levs1, extend='both')
    axs[0, 0].coastlines()
    g1 = axs[0, 0].gridlines(linestyle=':')
    g1.xlines = False
    g1.ylabels_left = True
    g1.ylocator = mticker.FixedLocator(np.arange(-60, 61, 30))
    g1.yformatter = LATITUDE_FORMATTER
    if not np.all(cbar_levs1 == cbar_levs2):
        cbar = plt.colorbar(cs, ax=axs[0, 0], orientation='horizontal', aspect=25)
        cbar.set_label(var_units)

    axs[0, 1].set_title(var1_name + ' - Obs.')
    var1_obs, lon_o180 = add_cyclic_point(var1_obs, coord=lon_o)
    cs = axs[0, 1].contourf(lon_o180, lat_o, var1_obs, cmap=plt.cm.RdBu_r, \
                            transform=ccrs.PlateCarree(), vmin=cbar_levs1[0], \
                            vmax=cbar_levs1[-1], levels=cbar_levs1, extend='both')
    axs[0, 1].coastlines()
    g1 = axs[0, 1].gridlines(linestyle=':')
    g1.xlines = False
    if np.all(cbar_levs1 == cbar_levs2) == False:
        cbar = plt.colorbar(cs, ax=axs[0, 1], orientation='horizontal', aspect=25)
        cbar.set_label(var_units)

    axs[1, 0].set_title(var2_name + ' - Model')
    if np.max(model_origlon) > 300:  # convert 0-360 lon to -180-180 lon for plotting
        start1a = var2_model[..., 0:int(len(model_origlon) / 2)]
        start1b = var2_model[..., int(len(model_origlon) / 2):]
        var2_model = np.concatenate((start1b, start1a), axis=1)
    var2_model, lon_m180 = add_cyclic_point(var2_model, coord=lon_m)
    cs = axs[1, 0].contourf(lon_m180, lat_m, var2_model, cmap=plt.cm.RdBu_r, \
                            transform=ccrs.PlateCarree(), vmin=cbar_levs2[0], \
                            vmax=cbar_levs2[-1], levels=cbar_levs2, extend='both')
    axs[1, 0].coastlines()
    g1 = axs[1, 0].gridlines(linestyle=':')
    g1.xlines = False
    g1.ylabels_left = True
    g1.ylocator = mticker.FixedLocator(np.arange(-60, 61, 30))
    g1.yformatter = LATITUDE_FORMATTER
    if not np.all(cbar_levs1 == cbar_levs2):
        cbar = plt.colorbar(cs, ax=axs[1, 0], orientation='horizontal', aspect=25)
        cbar.set_label(var_units)

    axs[1, 1].set_title(var2_name + ' - Obs.')
    var2_obs, lon_o180 = add_cyclic_point(var2_obs, coord=lon_o)
    cs = axs[1, 1].contourf(lon_o180, lat_o, var2_obs, cmap=plt.cm.RdBu_r, \
                            transform=ccrs.PlateCarree(), vmin=cbar_levs2[0], \
                            vmax=cbar_levs2[-1], levels=cbar_levs2, extend='both')
    axs[1, 1].coastlines()
    g1 = axs[1, 1].gridlines(linestyle=':')
    g1.xlines = False
    if not np.all(cbar_levs1 == cbar_levs2):
        cbar = plt.colorbar(cs, ax=axs[1, 1], orientation='horizontal', aspect=25)
        cbar.set_label(var_units)

    if np.all(cbar_levs1 == cbar_levs2):
        cbar = plt.colorbar(cs, ax=axs.ravel(), orientation='horizontal', aspect=25)
        cbar.set_label(var_units)
    plt.savefig(os.environ['WORK_DIR'] + '/model/PS/forcing_feedback_maps_' + \
                var_filename + '.eps', bbox_inches='tight')
    plt.close()

    return None


# ======================================================================
# map_plotting_2subs
#
# Function for producing figured with 2 subplot maps generated by
# forcing_feedback_plots.py

def map_plotting_2subs(cbar_levs, var_name, var_model,
                       model_origlon, lon_m, lat_m, lon_o, lat_o, var_obs,
                       var_units, var_filename):
    """

    Function for producing figured with 2 subplot maps generated by
    forcing_feedback_plots.py

    """

    fig, axs = plt.subplots(1, 2, subplot_kw=dict(projection= \
                                                      ccrs.PlateCarree(central_longitude=180)))

    axs[0].set_title(var_name + ' - Model')
    if np.max(model_origlon) > 300:  # convert 0-360 lon to -180-180 lon for plotting
        start1a = var_model[..., 0:int(len(model_origlon) / 2)]
        start1b = var_model[..., int(len(model_origlon) / 2):]
        var_model = np.concatenate((start1b, start1a), axis=1)
    var_model, lon_m180 = add_cyclic_point(var_model, coord=lon_m)
    axs[0].contourf(lon_m180, lat_m, var_model, cmap=plt.cm.RdBu_r,
                    transform=ccrs.PlateCarree(), vmin=cbar_levs[0],
                    vmax=cbar_levs[-1], levels=cbar_levs, extend='both')
    axs[0].coastlines()
    g1 = axs[0].gridlines(linestyle=':')
    g1.xlines = False
    g1.ylabels_left = True
    g1.ylocator = mticker.FixedLocator(np.arange(-60, 61, 30))
    g1.yformatter = LATITUDE_FORMATTER

    axs[1].set_title(var_name + ' - Obs.')
    var_obs, lon_o180 = add_cyclic_point(var_obs, coord=lon_o)
    cs = axs[1].contourf(lon_o180, lat_o, var_obs, cmap=plt.cm.RdBu_r,
                         transform=ccrs.PlateCarree(), vmin=cbar_levs[0],
                         vmax=cbar_levs[-1], levels=cbar_levs, extend='both')
    axs[1].coastlines()
    g1 = axs[1].gridlines(linestyle=':')
    g1.xlines = False

    cbar = plt.colorbar(cs, ax=axs.ravel(), orientation='horizontal', aspect=25)
    cbar.set_label(var_units)
    plt.savefig(os.environ['WORK_DIR'] + '/model/PS/forcing_feedback_maps_' + \
                var_filename + '.eps', bbox_inches='tight')
    plt.close()

    return None
