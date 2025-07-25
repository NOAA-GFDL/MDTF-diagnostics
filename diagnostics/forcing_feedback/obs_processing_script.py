import sys
import xarray as xr
import pandas as pd
import numpy as np

np.set_printoptions(threshold=sys.maxsize)
import numpy.ma as ma


# ======================================================================
# globemean_3D
#
# Compute cosine weighted global-mean
def globemean_3D(var, w):
    var_mask = ma.masked_array(var, ~np.isfinite(var))
    var_mean = np.squeeze(np.average(np.nanmean(var_mask, axis=2), axis=1, weights=w))

    return var_mean


def globemean_2D(var, w):
    var_mask = ma.masked_array(var, ~np.isfinite(var))
    var_mean = np.squeeze(np.average(np.nanmean(var_mask, axis=1), weights=w))

    return var_mean


# ======================================================================
# feedback_regress
#
# Regeresses radiative flux anomalies with global-mean dTs to compute 2D feedback
def feedback_regress(fluxanom, tspert, tsclimo, lat, lon, fbname):
    sp = tspert.shape
    sc = tsclimo.shape

    tsclimo_re = np.squeeze(np.nanmean(np.reshape(tsclimo, (np.int(sc[0] / 12), 12, sc[1], sc[2])), axis=0))

    tsanom = tspert - np.reshape(np.repeat(tsclimo_re[np.newaxis, ...], np.int(sp[0] / 12),
                                           axis=0), (sp[0], sp[1], sp[2]))

    weights = np.repeat(np.cos(np.deg2rad(lat))[np.newaxis, :], sp[0], axis=0)
    tsanom_globemean = globemean_3D(tsanom, weights)
    tsanom_re = np.repeat(np.repeat(tsanom_globemean[:, np.newaxis], sp[1], axis=1)[..., np.newaxis], sp[2], axis=2)

    tsanom_re_timemean = np.nanmean(tsanom_re, axis=0)
    tsanom_re_std = np.nanstd(tsanom_re, axis=0)
    fluxanom_timemean = np.nanmean(fluxanom, axis=0)

    n = np.sum(~np.isnan(tsanom_re), axis=0)
    cov = np.nansum((tsanom_re - tsanom_re_timemean) * \
                    (fluxanom - fluxanom_timemean), axis=0) / n
    slopes = cov / (tsanom_re_std ** 2)

    slopes = xr.DataArray(slopes, coords=[lat, lon], dims=['lat', 'lon'], name=fbname)

    return slopes


kname = 'CloudSat'
regime = 'TOA'

# Read in reanalysis data and kernel-derived radiative anomalies and forcing,
# which were computed using a slightly modified version of the MDTF "Forcing and Feedback"
# module code. Then, regress against global-mean surface temperature, when applicable,
# to compute radiative feedbacks using the "feedback_regress" function detailed above.
# For Instantaneous Radiative Forcing, we just regress against time (trend)

# Surface temperature

ts_GISS_anoms = xr.open_dataset(
    '/discover/nobackup/projects/geos5rad/rjkramer/GISStemp/gistemp1200_GHCNv4_ERSSTv5_MDTF.nc')
ts_GISS_anoms = ts_GISS_anoms.assign_coords(
    time=pd.date_range('1880-01', periods=len(ts_GISS_anoms.time.values), freq='M'))
ts_GISS_anoms = ts_GISS_anoms.sel(time=slice('2003-01', '2014-12'))
ts_GISS_anoms_climo = ts_GISS_anoms_climo = ts_GISS_anoms.sel(time=slice('2003-01', '2014-12'))
ts_GISS_anoms_climo_climatology = ts_GISS_anoms_climo.groupby('time.month').mean('time')
ts_GISS_anoms_anoms = ts_GISS_anoms.groupby('time.month') - ts_GISS_anoms_climo_climatology
ts_pert = ts_GISS_anoms_anoms.tempanomaly.values
ts_climo = ts_GISS_anoms_anoms.tempanomaly.values

# Planck radiative anomalies
inputfile = ('/gpfsm/dnb32/rjkramer/MERRAfb/results/' + regime + '_Fluxanom_planck_Results_K' + kname +
             '_MERRAfb_wCERES_retry.nc')
nc_pl_era = xr.open_dataset(inputfile)
nc_pl_era = nc_pl_era.assign_coords(time=pd.date_range('2003-01', periods=len(nc_pl_era.time.values), freq='M')).sel(
    time=slice('2003-01', '2014-12'))
inputfile = None

varhold = nc_pl_era.fluxanom_pl_sfc_tot.values + nc_pl_era.fluxanom_pl_trop_tot.values + nc_pl_era.fluxanom_pl_strat_tot.values
fb_pl_era = feedback_regress(varhold, ts_pert, ts_climo, nc_pl_era.latitude.values, nc_pl_era.longitude.values,
                             'Planck')
varhold = None

# Lapse Rate radiative anomalies
inputfile = ('/gpfsm/dnb32/rjkramer/MERRAfb/results/' + regime + '_Fluxanom_lapserate_Results_K' + kname +
             '_MERRAfb_wCERES_retry.nc')
nc_lr_era = xr.open_dataset(inputfile)
nc_lr_era = nc_lr_era.assign_coords(time=pd.date_range('2003-01', periods=len(nc_lr_era.time.values), freq='M')).sel(
    time=slice('2003-01', '2014-12'))
inputfile = None

varhold = nc_lr_era.fluxanom_lr_trop_tot.values + nc_lr_era.fluxanom_lr_strat_tot.values
fb_lr_era = feedback_regress(varhold, ts_pert, ts_climo, nc_lr_era.latitude.values, nc_lr_era.longitude.values,
                             'LapseRate')
varhold = None

# Water vapor radiative anomalies
inputfile = ('/gpfsm/dnb32/rjkramer/MERRAfb/results/' + regime + '_Fluxanom_watervapor_Results_K' + kname +
             '_MERRAfb_wCERES_retry.nc')
nc_wv_era = xr.open_dataset(inputfile)
nc_wv_era = nc_wv_era.assign_coords(time=pd.date_range('2003-01', periods=len(nc_wv_era.time.values),
                                                       freq='M')).sel(time=slice('2003-01', '2014-12'))
inputfile = None

varhold = nc_wv_era.fluxanom_lw_q_trop_tot.values + nc_wv_era.fluxanom_lw_q_strat_tot.values
fb_lw_q_era = feedback_regress(varhold, ts_pert, ts_climo, nc_wv_era.latitude.values, nc_wv_era.longitude.values,
                               'LW_WaterVapor')
varhold = None
varhold = nc_wv_era.fluxanom_sw_q_trop_tot.values + nc_wv_era.fluxanom_sw_q_strat_tot.values
fb_sw_q_era = feedback_regress(varhold, ts_pert, ts_climo, nc_wv_era.latitude.values, nc_wv_era.longitude.values,
                               'SW_WaterVapor')
varhold = None

# Cloud radiative anomalies
inputfile = ('/gpfsm/dnb32/rjkramer/MERRAfb/results/' + regime + '_Fluxanom_clouds_Results_K' + kname +
             '_MERRAfb_wCERES_retry.nc')
nc_c_era = xr.open_dataset(inputfile)
nc_c_era = nc_c_era.assign_coords(time=pd.date_range('2003-01', periods=len(nc_c_era.time.values), freq='M')).sel(
    time=slice('2003-01', '2014-12'))
inputfile = None

varhold = nc_c_era.fluxanom_lw_c.values
fb_lw_c_era = feedback_regress(varhold, ts_pert, ts_climo, nc_c_era.latitude.values, nc_c_era.longitude.values,
                               'LW_Cloud')
varhold = None
varhold = nc_c_era.fluxanom_sw_c.values
fb_sw_c_era = feedback_regress(varhold, ts_pert, ts_climo, nc_c_era.latitude.values, nc_c_era.longitude.values,
                               'SW_Cloud')
varhold = None

# Surface Albedo radiative anomalies
inputfile = ('/gpfsm/dnb32/rjkramer/MERRAfb/results/' + regime + '_Fluxanom_albedo_Results_K' + kname +
             '_MERRAfb_wCERES_retry.nc')
nc_a_era = xr.open_dataset(inputfile)
nc_a_era = nc_a_era.assign_coords(time=pd.date_range('2003-01', periods=len(nc_a_era.time.values), freq='M')).sel(
    time=slice('2003-01', '2014-12'))
inputfile = None

varhold = nc_a_era.fluxanom_a_sfc_tot.values
fb_a_era = feedback_regress(varhold, ts_pert, ts_climo, nc_a_era.latitude.values, nc_a_era.longitude.values,
                            'SfcAlbedo')
varhold = None

# Total TOA radiative imbalance
inputfile = ('/gpfsm/dnb32/rjkramer/MERRAfb/results/' + regime + '_Fluxanom_netrad_Results_K' + kname +
             '_MERRAfb_wCERES_retry.nc')
nc_netrad_era = xr.open_dataset(inputfile)
nc_netrad_era = nc_netrad_era.assign_coords(
    time=pd.date_range('2003-01', periods=len(nc_netrad_era.time.values), freq='M')).sel(
    time=slice('2003-01', '2014-12'))
inputfile = None

varhold = nc_netrad_era.netrad_lw_tot.values
fb_lw_netrad_era = feedback_regress(varhold, ts_pert, ts_climo, nc_netrad_era.latitude.values,
                                    nc_netrad_era.longitude.values, 'LW_Rad')
varhold = None
varhold = nc_netrad_era.netrad_sw_tot.values
fb_sw_netrad_era = feedback_regress(varhold, ts_pert, ts_climo, nc_netrad_era.latitude.values,
                                    nc_netrad_era.longitude.values, 'SW_Rad')
varhold = None

# Instaneous Radiative Forcing
inputfile = ('/gpfsm/dnb32/rjkramer/MERRAfb/results/' + regime + '_Fluxanom_IRF_Results_K' + kname +
             '_MERRAfb_wCERES_retry.nc')
nc_IRF_era = xr.open_dataset(inputfile)
nc_IRF_era = nc_IRF_era.assign_coords(time=pd.date_range('2003-01', periods=len(nc_IRF_era.time.values),
                                                         freq='M')).sel(time=slice('2003-01', '2014-12'))
inputfile = None

varhold = nc_IRF_era.IRF_lw_tot.values
shp = ts_pert.shape
xtime = np.repeat(np.repeat(np.arange(shp[0])[..., np.newaxis], shp[1], axis=1)[..., np.newaxis], shp[2], axis=2)
fb_lw_IRF_era = feedback_regress(varhold, xtime, xtime * 0, nc_IRF_era.latitude.values, nc_IRF_era.longitude.values,
                                 'LW_IRF')
varhold = None
varhold = nc_IRF_era.IRF_sw_tot.values
fb_sw_IRF_era = feedback_regress(varhold, xtime, xtime * 0, nc_IRF_era.latitude.values, nc_IRF_era.longitude.values,
                                 'SW_IRF')
varhold = None

# Save 2D Radiative feedbacks (W/m2/K) and IRF trends (W/m2/month) to a netcdf for use in the MDTF Module
ds = fb_pl_era.to_dataset()
ds['LapseRate'] = fb_lr_era
ds['LW_WaterVapor'] = fb_lw_q_era
ds['SW_WaterVapor'] = fb_sw_q_era
ds['SfcAlbedo'] = fb_a_era
ds['LW_Cloud'] = fb_lw_c_era
ds['SW_Cloud'] = fb_sw_c_era
ds['LW_IRF'] = fb_lw_IRF_era  # W/m2/month for now. converted to W/m2/yr later in POD
ds['SW_IRF'] = fb_sw_IRF_era  # W/m2/month for now. converted to W/m2/yr later in POD
ds['LW_Rad'] = fb_lw_netrad_era
ds['SW_Rad'] = fb_sw_netrad_era

ds.to_netcdf('forcing_feedback_obs_MERRA2.nc')

weights = np.cos(np.deg2rad(nc_IRF_era.latitude.values))
print('Rad')
print(globemean_2D(fb_lw_netrad_era + fb_sw_netrad_era, weights))
print('CldFB')
print(globemean_2D(fb_lw_c_era + fb_sw_c_era, weights))
print('LR FB')
print(globemean_2D(fb_lr_era, weights))
print('IRF')
print(globemean_2D(fb_lw_IRF_era + fb_sw_IRF_era, weights))
