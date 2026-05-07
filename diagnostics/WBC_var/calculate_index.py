#!/usr/bin/env python
# coding: utf-8

import numpy as np
import xarray as xr
import warnings
import statsmodels.api as sm
from scipy.interpolate import interp1d
from scipy.optimize import minimize_scalar
from eofs.xarray import Eof

def smooth_data(t_series, window=12):
    if len(t_series) < window: return np.full_like(t_series, np.nan)
    kernel = np.ones(window) / window
    smoothed = np.convolve(t_series, kernel, mode='same')
    smoothed[:window//2] = np.nan
    smoothed[-window//2:] = np.nan
    return smoothed

def get_acf(t_series):
    if np.isnan(t_series).all(): return np.full(10, np.nan), np.full(len(t_series), np.nan), np.nan
    try:
        nlags = min(59, len(t_series)//2)
        acf_val = sm.tsa.stattools.acf(t_series, adjusted=False, nlags=nlags, missing='drop')
    except: return np.full(10, np.nan), np.full(len(t_series), np.nan), np.nan
    crossings = np.where(np.diff(np.sign(acf_val)))[0]
    tau = crossings[0] + 1 if len(crossings) > 0 else len(acf_val)
    confint = acf_val[1] if len(acf_val) > 1 else 0
    t_indices = np.arange(len(t_series))
    n_eff = (len(t_series) - t_indices) / tau
    return acf_val, n_eff, confint

def damping_time_scale(acf):
    if np.isnan(acf).all(): return np.nan
    efold = 1/np.exp(1)
    find_crossing = acf - efold
    crossings = np.where(np.diff(np.sign(find_crossing)))[0]
    damping_t = crossings[0]+1 if len(crossings) > 0 else len(acf)
    return damping_t

def calc_eofs(da, num_modes=1):
    if da.isnull().all():
        shape = (num_modes, da.shape[1]) if len(da.shape) > 1 else (num_modes,)
        return np.full(shape, np.nan), np.full((da.shape[0], num_modes), np.nan), np.full(num_modes, np.nan)
    try:
        solver = Eof(da)
        eofs = solver.eofs(neofs=num_modes)
        pcs = solver.pcs(npcs=num_modes, pcscaling=1)
        per_var = solver.varianceFraction(neigs=num_modes)
        for i in range(eofs.shape[0]):
            if np.nansum(eofs[i].values) < 0:
                eofs[i] *= -1
                pcs[:, i] *= -1
        return eofs.values, pcs.values, per_var.values
    except:
        return np.full((num_modes, da.shape[1]), np.nan), np.full((da.shape[0], num_modes), np.nan), np.full(num_modes, np.nan)

def eof_crossings(eofs, per_var):
    results = []
    vars_expl = []
    if np.isnan(eofs).all(): return np.full(3, np.nan), np.full(3, np.nan)
    for i in range(min(3, len(eofs))):
        zero_crossings = ((eofs[i][:-1] * eofs[i][1:]) < 0).sum()
        results.append(zero_crossings)
        vars_expl.append(per_var[i])
    while len(results) < 3:
        results.append(np.nan)
        vars_expl.append(np.nan)
    return np.array(results), np.array(vars_expl)

def damping_spatial_scale(acf):
    return damping_time_scale(acf)

# -----------------------------------------------------------------------------
# Main Calculation Functions
# -----------------------------------------------------------------------------

def new_gsi_index(ds):
    """
    Finds the GSI Path.
    [Fix] Robust logic: Falls back to nearest point if exact crossing is missing.
    """
    # 1. Climatology
    if 'sla' not in ds:
        clim = ds['zos'].groupby('time.month').mean('time')
        ssh_anom = ds['zos'].groupby('time.month') - clim
    else:
        ssh_anom = ds['sla']
        
    clim_ssh = ds['zos'].mean(dim='time')

    # 2. Find Latitude of Max Variability (L_max)
    std_ssh = ssh_anom.std(dim='time')
    std_ssh_filled = std_ssh.fillna(-1.0)
    idx_max = std_ssh_filled.argmax(dim='lat')
    
    L_max = std_ssh.lat.isel(lat=idx_max).values
    valid_mask = std_ssh.notnull().any(dim='lat').values
    L_max[~valid_mask] = np.nan

    lons = std_ssh.lon.values

    # 3. Find Optimal Isoline (C_opt)
    clim_ssh_vals = clim_ssh.values 
    clim_lats = clim_ssh.lat.values
    
    def get_isoline_lats_robust(C, target_lats_arr=None):
        iso_lats = []
        for i in range(len(lons)):
            col_ssh = clim_ssh_vals[:, i]
            col_lat = clim_lats
            
            valid = np.isfinite(col_ssh)
            if not np.any(valid):
                iso_lats.append(np.nan)
                continue
                
            y = col_ssh[valid]
            x = col_lat[valid]
            
            # Zero Crossing
            diff = y - C
            cross_idxs = np.where(np.diff(np.sign(diff)))[0]
            
            candidates = []
            
            if len(cross_idxs) > 0:
                for idx in cross_idxs:
                    y0, y1 = y[idx], y[idx+1]
                    x0, x1 = x[idx], x[idx+1]
                    if (y1 - y0) == 0: lat_cross = x0
                    else: lat_cross = x0 + (C - y0) * (x1 - x0) / (y1 - y0)
                    candidates.append(lat_cross)
            
            else:
                min_idx = np.argmin(np.abs(diff))
                candidates.append(x[min_idx])
            
            candidates = np.array(candidates)
            
            ref_lat = None
            if target_lats_arr is not None:
                ref_lat = target_lats_arr[i]
            
            if ref_lat is not None and np.isfinite(ref_lat):
                best_idx = np.argmin(np.abs(candidates - ref_lat))
                iso_lats.append(candidates[best_idx])
            else:
                iso_lats.append(candidates[0])
                
        return np.array(iso_lats)

    def objective(C):
        L_iso = get_isoline_lats_robust(C, target_lats_arr=L_max)
        mask = np.isfinite(L_iso) & np.isfinite(L_max)
        if mask.sum() == 0: return 1e9
        return np.mean((L_iso[mask] - L_max[mask])**2)

    vmin, vmax = np.nanmin(clim_ssh_vals), np.nanmax(clim_ssh_vals)
    if np.isnan(vmin) or np.isnan(vmax):
         return np.full(len(lons), np.nan), lons, np.full(len(ds.time), np.nan)
         
    res = minimize_scalar(objective, bounds=(vmin, vmax), method='bounded')
    C_opt = res.x
    
    L_path = get_isoline_lats_robust(C_opt, target_lats_arr=L_max)
    
    # Interpolate Anomaly along Path
    target_lats = xr.DataArray(L_path, dims="gsi_points")
    target_lons = xr.DataArray(lons, dims="gsi_points")
    path_anomalies = ssh_anom.interp(lat=target_lats, lon=target_lons, method='linear')
    gulf_stream_index = path_anomalies.mean(dim='gsi_points') 
    
    return L_path, lons, gulf_stream_index


def gs_index(dataset, region):
    gsi_lon_list, gsi_lat_list = [], []
    sla_ts_list, sla_ts_std_list = [], []
    gsi_norm_list, gsi_annual_list = [], []

    # Use regional_boundary (Tight calculation box)
    from calculate_index import regional_boundary 
    bounds = regional_boundary(region)
    ds_reg = dataset.sel(lon=bounds["lon"], lat=bounds["lat"])

    for ens in range(ds_reg.sizes['ensemble']):
        ds_ens = ds_reg.isel(ensemble=ens).compute()
        
        L_path, lons, gsi_ts_da = new_gsi_index(ds_ens)
        
        target_lats = xr.DataArray(L_path, dims="gsi_points")
        target_lons = xr.DataArray(lons, dims="gsi_points")
        
        path_data = ds_ens['sla'].interp(lat=target_lats, lon=target_lons, method='linear')
        
        sla_ts = gsi_ts_da.values 
        sla_ts_std = path_data.std(dim='gsi_points', skipna=True).values

        mean_val = np.nanmean(sla_ts)
        std_val = np.nanstd(sla_ts)
        if std_val != 0 and not np.isnan(std_val):
            gsi_norm = (sla_ts - mean_val) / std_val
        else:
            gsi_norm = np.zeros_like(sla_ts)
        
        gsi_annual = smooth_data(gsi_norm, window=12)

        gsi_lon_list.append(lons)
        gsi_lat_list.append(L_path)
        sla_ts_list.append(sla_ts)
        sla_ts_std_list.append(sla_ts_std)
        gsi_norm_list.append(gsi_norm)
        gsi_annual_list.append(gsi_annual)

    dataset['gsi_lon'] = (('ensemble', 'gsi_points'), np.array(gsi_lon_list))
    dataset['gsi_lat'] = (('ensemble', 'gsi_points'), np.array(gsi_lat_list))
    dataset['sla_ts'] = (('ensemble', 'time'), np.array(sla_ts_list))
    dataset['sla_ts_std'] = (('ensemble', 'time'), np.array(sla_ts_std_list))
    dataset['gsi_norm'] = (('ensemble', 'time'), np.array(gsi_norm_list))
    dataset['gsi_annual'] = (('ensemble', 'time'), np.array(gsi_annual_list))

    return dataset

def gsp_index(dataset, region):
    alt_gsi_sd_list, acf_list, n_eff_list, confint_list, alt_damp_t_list = [], [], [], [], [] 
    
    from calculate_index import regional_boundary
    bounds = regional_boundary(region)
    ds_reg = dataset.sel(lon=bounds["lon"], lat=bounds["lat"])

    for ens in range(ds_reg.sizes['ensemble']):
        gsi_lon = dataset['gsi_lon'].isel(ensemble=ens).values
        gsi_lat = dataset['gsi_lat'].isel(ensemble=ens).values
        
        ds_ens = ds_reg.isel(ensemble=ens).compute()
        std_map = ds_ens['sla'].std(dim='time')
        
        target_lats = xr.DataArray(gsi_lat, dims="gsi_points")
        target_lons = xr.DataArray(gsi_lon, dims="gsi_points")
        
        path_std = std_map.interp(lat=target_lats, lon=target_lons, method='nearest')
        alt_gsi_sd = path_std.mean().item()

        gsi_norm = dataset['gsi_norm'].isel(ensemble=ens).values
        acf, n_eff, confint = get_acf(gsi_norm)
        alt_damp_t = damping_time_scale(acf)

        alt_gsi_sd_list.append(alt_gsi_sd)
        acf_list.append(acf)
        n_eff_list.append(n_eff)
        confint_list.append(confint)
        alt_damp_t_list.append(alt_damp_t)

    dataset['alt_gsi_sd'] = (('ensemble'), np.array(alt_gsi_sd_list))
    dataset['acf'] = (('ensemble', 'n_lags'), np.array(acf_list))
    dataset['n_eff'] = (('ensemble', 'time'), np.array(n_eff_list))
    dataset['confint'] = (('ensemble'), np.array(confint_list))
    dataset['alt_damp_t'] = (('ensemble'), np.array(alt_damp_t_list))
    
    return dataset

def EOF_index(dataset, region):
    eofs_gsi_list, pcs_gsi_list, per_var_gsi_list = [], [], []
    alt_cross_list, alt_var_list = [], []
    acf_spatial_list, n_eff_spatial_list, confint_spatial_list, alt_damp_s_list = [], [], [], []

    num_modes = 3
    from calculate_index import regional_boundary
    bounds = regional_boundary(region)
    ds_reg = dataset.sel(lon=bounds["lon"], lat=bounds["lat"])

    for ens in range(ds_reg.sizes['ensemble']):
        ds_ens = ds_reg.isel(ensemble=ens).compute()
        gsi_lon = dataset['gsi_lon'].isel(ensemble=ens).values
        gsi_lat = dataset['gsi_lat'].isel(ensemble=ens).values
        
        target_lats = xr.DataArray(gsi_lat, dims="gsi_points")
        target_lons = xr.DataArray(gsi_lon, dims="gsi_points")
        
        sla_gsi_array = ds_ens['sla'].interp(lat=target_lats, lon=target_lons, method='linear')
        
        sla_gsi_filled = sla_gsi_array.fillna(0)
        eofs, pcs, per_var = calc_eofs(sla_gsi_filled, num_modes)
        
        alt_cross, alt_var = eof_crossings(eofs, per_var)
        
        mean_profile = sla_gsi_array.mean(dim='time', skipna=True).values
        acf_s, n_eff_s, conf_s = get_acf(mean_profile)
        alt_damp_s = damping_spatial_scale(acf_s)

        eofs_gsi_list.append(eofs)
        pcs_gsi_list.append(pcs)
        per_var_gsi_list.append(per_var)
        alt_cross_list.append(alt_cross)
        alt_var_list.append(alt_var)
        acf_spatial_list.append(acf_s)
        n_eff_spatial_list.append(n_eff_s)
        confint_spatial_list.append(conf_s)
        alt_damp_s_list.append(alt_damp_s)

    dataset['eofs_gsi'] = (('ensemble','mode','gsi_points'), np.array(eofs_gsi_list))
    dataset['pcs_gsi'] = (('ensemble','time','mode'), np.array(pcs_gsi_list))
    dataset['per_var_gsi'] = (('ensemble','mode'), np.array(per_var_gsi_list)) 
    dataset['alt_cross'] = (('ensemble','mode'), np.array(alt_cross_list))
    dataset['alt_var'] = (('ensemble','mode'), np.array(alt_var_list))
    dataset['acf_spatial'] = (('ensemble','spatial_lags'), np.array(acf_spatial_list))
    dataset['n_eff_spatial'] = (('ensemble','gsi_points'), np.array(n_eff_spatial_list))
    dataset['confint_spatial'] = (('ensemble'), np.array(confint_spatial_list))
    dataset['alt_damp_s'] = (('ensemble'), np.array(alt_damp_s_list))
    
    return dataset

# Region definitions
def regional_boundary(region):
    region_bounds = {
        "gulf": {"lon": slice(360-70, 309),"lat": slice(33, 42)},
        "kuroshio": {"lon": slice(145, 157),"lat": slice(31, 45)},
        "australia": {"lon": slice(157, 168), "lat": slice(-40, -30)},
        "agulhas": {"lon": slice(25, 36), "lat": slice(-45, -37)},
        "brazil": {"lon": slice(360-45, 360-30),"lat": slice(-44, -33)},
        }
    return region_bounds[region]

def region_define(region):
    region_bounds = {
        "gulf": {"lon": slice(270, 315), "lat": slice(32, 46)},
        "kuroshio": {"lon": slice(133, 160), "lat": slice(31, 43)},
        "australia": {"lon": slice(145, 180), "lat": slice(-40, -23)},
        "agulhas": {"lon": slice(18, 42), "lat": slice(-46, -35)},
        "brazil": {"lon": slice(360-60, 360-15), "lat": slice(-49, -32)},
    }
    return region_bounds[region]

def current_name(region):
    names = {
        "gulf": 'Gulf Stream', "kuroshio": 'Kuroshio Current',
        "australia": 'East Australia Current', "agulhas": 'Agulhas Current',
        "brazil": 'North Brazil Current',
    }
    return names[region]

def alias_name(region):
    names = {"gulf": 'GSI', "kuroshio": 'KCI', "australia": 'EACI', "agulhas": 'ACI', "brazil": 'NBCI'}
    return names[region]

def model_resolution(region):
    return ""
