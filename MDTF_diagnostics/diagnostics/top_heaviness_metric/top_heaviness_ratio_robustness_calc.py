# Last update: 28 June top_heaviness_ratio_robustness_calc.py
import os
import xarray as xr
import numpy as np
import scipy
from scipy import interpolate
from scipy import integrate
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.mpl.ticker as cticker

# Setting variables equal to environment variables set by the diagnostic
time_coord = os.environ["time_coord"]
lat_coord = os.environ["lat_coord"]
lon_coord = os.environ["lon_coord"]
lev_coord = os.environ["lev_coord"]
omega_var = os.environ["omega_var"]
WK_DIR = os.environ["WORK_DIR"]
OBS_DATA = os.environ["OBS_DATA"]
CASENAME = os.environ["CASENAME"]


# from numba import jit
# @jit(nopython=True)
def corr2d(a1, a2):
    ij = np.shape(a1[:])
    mid_corr = np.zeros(ij[1:])
    for i in np.arange(ij[1]):
        for j in np.arange(ij[2]):
            mid_corr[i, j] = np.corrcoef(a1[:, i, j], a2[:, i, j])[0, 1]
    return mid_corr


# ====================== deriving model output =======================
def top_heaviness_ratio_robustness_calc_model(reanalysis_path, reanalysis_var):
    # read omega and land-sea fraction data
    ds = xr.open_dataset(reanalysis_path)
    lev_model = ds[lev_coord].values
    lat_model = ds[lat_coord].values
    lon_model = ds[lon_coord].values
    isort = np.argsort(lev_model)[::-1]  # descending
    mid_omega_model = ds[reanalysis_var].values  # mon x lev x lat x lon; for the sample data (JAS over 2000-2019)
    mid_omega_model = mid_omega_model[:, isort]
    mid_omega_model_ltm = np.nanmean(mid_omega_model, axis=0)  # lev x lat x lon
    # ======================Interpolation=======================
    dp = lev_model[-1] - lev_model[0]
    levs_interp = np.linspace(lev_model[0], lev_model[-1], num=len(lev_model))
    f = interpolate.interp1d(lev_model, mid_omega_model_ltm, kind='cubic',
                             axis=0)  # you can choose linear which consumes less time
    mid_omega_model_ltm = f(levs_interp)
    # ======================deriving O1 and O2=======================
    # construct Q1_model as half a sine wave and Q2_model as a full sine wave
    # two base functions; Q1: idealized deep convection profile; Q2: Deep stratiform profile (Back et al. 2017)
    Q1_model = np.zeros(len(levs_interp))
    Q2_model = np.zeros(len(levs_interp))
    for i in range(len(levs_interp)):
        Q1_model[i] = -np.sin(np.pi * (levs_interp[i] - levs_interp[0]) / dp)
        Q2_model[i] = np.sin(2 * np.pi * (levs_interp[i] - levs_interp[0]) / dp)
    # Normalize
    factor = integrate.trapz(Q1_model * Q1_model, lev_model) / dp
    Q1_model = Q1_model / np.sqrt(factor)
    factor = integrate.trapz(Q2_model * Q2_model, lev_model) / dp
    Q2_model = Q2_model / np.sqrt(factor)
    # ======================calculate explained variance over the globe=======================
    # Often times, the pres level is not equally distributed. People tend to increase density in the 
    # ... upper and lower atmopshere, leaving a less dense distribution in the mid atmosphere. 
    # ... Thus, it is important to weight Q1 and Q2 before we calculate R2
    # Remember, we already take weights into account when calculating O1 and O2
    mid_Q1_model = Q1_model / np.sqrt(np.sum(Q1_model ** 2))  # unitize Q1
    mid_Q2_model = Q2_model / np.sqrt(np.sum(Q2_model ** 2))  # unitize Q2
    # calc ltm O1 and O2, because calculating correlation is not a linear operation
    OQ1_model_ltm = np.nansum(mid_Q1_model[:, None, None] * mid_omega_model_ltm, axis=0)
    OQ2_model_ltm = np.nansum(mid_Q2_model[:, None, None] * mid_omega_model_ltm, axis=0)
    OQQ1_model = OQ1_model_ltm[None, :, :] * mid_Q1_model[:, None, None]  # reconstruct Q1 field
    OQQ2_model = OQ2_model_ltm[None, :, :] * mid_Q2_model[:, None, None]  # reconstruct Q2 field
    OQQ_sum = OQQ1_model + OQQ2_model
    corr2d_model = corr2d(mid_omega_model_ltm, OQQ_sum)
    R2_model = corr2d_model ** 2
    # ====================== setting up figures =======================
    ilat = np.argsort(lat_model)
    ilon = np.argsort(lon_model)
    # ====================== R2 =======================
    # R2 measures the proportion of ltm omega profile explained by Q1 and Q2  
    fig, axes = plt.subplots(figsize=(8, 4))
    mmid = R2_model
    axes = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    clevs = np.arange(0, 1., 0.1)
    im0 = axes.contourf(lon_model, lat_model, mmid, clevs, cmap=plt.get_cmap('RdBu_r'), extend='both',
                        transform=ccrs.PlateCarree())
    axes.coastlines()
    lon_grid = np.arange(lon_model[ilon][0], lon_model[ilon][-1], 60)
    lat_grid = np.arange(lat_model[ilat][0], lat_model[ilat][-1], 30)
    # set x labels
    axes.set_xticks(lon_grid, crs=ccrs.PlateCarree())
    axes.set_xticklabels(lon_grid, rotation=0, fontsize=14)
    lon_formatter = cticker.LongitudeFormatter()
    axes.xaxis.set_major_formatter(lon_formatter)
    # set y labels
    axes.set_yticks(lat_grid, crs=ccrs.PlateCarree())
    axes.set_yticklabels(lat_grid, rotation=0, fontsize=14)
    lat_formatter = cticker.LatitudeFormatter()
    axes.yaxis.set_major_formatter(lat_formatter)
    # colorbar
    fig.colorbar(im0, ax=axes, orientation="horizontal", pad=0.15, shrink=.9, aspect=45)
    axes.set_title('$R^{2}$ Between Recon. Omega & Original', loc='center', fontsize=18)
    fig.savefig(WK_DIR + "/model/" + CASENAME + "_R2.png", format='png', bbox_inches='tight')

    print("Plotting Completed")


top_heaviness_ratio_robustness_calc_model(os.environ["OMEGA_FILE"], os.environ["omega_var"])


# ====================== deriving obs output =======================
def top_heaviness_ratio_robustness_calc_obs(obs_data_full_dir):
    # read omega 
    ds = xr.open_dataset(obs_data_full_dir)
    lev_obs = ds['lev'].values
    lat_obs = ds['lat'].values
    lon_obs = ds['lon'].values
    isort = np.argsort(lev_obs)[::-1]  # descending
    mid_omega_obs = ds['omega'].values  # mon x lev x lat x lon; for the sample data (July over 2000-2019)
    mid_omega_obs = mid_omega_obs[:, isort]
    mid_omega_obs_ltm = np.nanmean(mid_omega_obs, axis=0)  # lev x lat x lon
    # ======================Interpolation=======================
    dp = lev_obs[-1] - lev_obs[0]
    levs_interp = np.linspace(lev_obs[0], lev_obs[-1], num=len(lev_obs))
    f = interpolate.interp1d(lev_obs, mid_omega_obs_ltm, kind='cubic',
                             axis=0)  # you can choose linear which consumes less time
    mid_omega_obs_ltm = f(levs_interp)
    # ======================deriving O1 and O2=======================
    # construct Q1_obs as half a sine wave and Q2_obs as a full sine wave
    # two base functions; Q1: idealized deep convection profile; Q2: Deep stratiform profile (Back et al. 2017)
    Q1_obs = np.zeros(len(levs_interp))
    Q2_obs = np.zeros(len(levs_interp))
    for i in range(len(levs_interp)):
        Q1_obs[i] = -np.sin(np.pi * (levs_interp[i] - levs_interp[0]) / dp)
        Q2_obs[i] = np.sin(2 * np.pi * (levs_interp[i] - levs_interp[0]) / dp)
    # Normalize
    factor = scipy.integrate.trapz(Q1_obs * Q1_obs, lev_obs) / dp
    Q1_obs = Q1_obs / np.sqrt(factor)
    factor = scipy.integrate.trapz(Q2_obs * Q2_obs, lev_obs) / dp
    Q2_obs = Q2_obs / np.sqrt(factor)
    # ======================calculate explained variance over the globe=======================
    # Often times, the pres level is not equally distributed. People tend to increase density in the 
    # ... upper and lower atmopshere, leaving a less dense distribution in the mid atmosphere. 
    # ... Thus, it is important to weight Q1 and Q2 before we calculate explained variance
    # Remember, we already take weights into account when calculating O1 and O2
    mid_Q1_obs = Q1_obs / np.sqrt(np.sum(Q1_obs ** 2))  # unitize Q1
    mid_Q2_obs = Q2_obs / np.sqrt(np.sum(Q2_obs ** 2))  # unitize Q2
    # calc ltm O1 and O2, because calculating correlation is not a linear operation
    OQ1_obs_ltm = np.nansum(mid_Q1_obs[:, None, None] * mid_omega_obs_ltm, axis=0)
    OQ2_obs_ltm = np.nansum(mid_Q2_obs[:, None, None] * mid_omega_obs_ltm, axis=0)
    OQQ1_obs = OQ1_obs_ltm[None, :, :] * mid_Q1_obs[:, None, None]  # reconstruct Q1 field
    OQQ2_obs = OQ2_obs_ltm[None, :, :] * mid_Q2_obs[:, None, None]  # reconstruct Q2 field
    OQQ_sum = OQQ1_obs + OQQ2_obs
    corr2d_obs = corr2d(mid_omega_obs_ltm, OQQ_sum)
    R2_obs = corr2d_obs ** 2
    # ====================== setting up figures =======================
    ilat = np.argsort(lat_obs)
    ilon = np.argsort(lon_obs)
    # ====================== R2 =======================
    # R2 measures the proportion of ltm omega profile explained by Q1 and Q2  
    fig, axes = plt.subplots(figsize=(8, 4))
    mmid = R2_obs
    axes = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    clevs = np.arange(0, 1., 0.1)
    im0 = axes.contourf(lon_obs, lat_obs, mmid, clevs, cmap=plt.get_cmap('RdBu_r'), extend='both',
                        transform=ccrs.PlateCarree())
    axes.coastlines()
    lon_grid = np.arange(lon_obs[ilon][0], lon_obs[ilon][-1], 60)
    lat_grid = np.arange(lat_obs[ilat][0], lat_obs[ilat][-1], 30)
    # set x labels
    axes.set_xticks(lon_grid, crs=ccrs.PlateCarree())
    axes.set_xticklabels(lon_grid, rotation=0, fontsize=14)
    lon_formatter = cticker.LongitudeFormatter()
    axes.xaxis.set_major_formatter(lon_formatter)
    # set y labels
    axes.set_yticks(lat_grid, crs=ccrs.PlateCarree())
    axes.set_yticklabels(lat_grid, rotation=0, fontsize=14)
    lat_formatter = cticker.LatitudeFormatter()
    axes.yaxis.set_major_formatter(lat_formatter)
    # colorbar
    fig.colorbar(im0, ax=axes, orientation="horizontal", pad=0.15, shrink=.9, aspect=45)
    axes.set_title('$R^{2}$ Between Recon. Omega & Original', loc='center', fontsize=18)
    fig.tight_layout()
    fig.savefig(WK_DIR + "/obs/ERA5_R2_Between_Recon_Omega&Original_2000_2019_July.png", format='png',
                bbox_inches='tight')

    print("Plotting Completed")


top_heaviness_ratio_robustness_calc_obs(OBS_DATA + '/ERA5_omega_mon_2000_2019_July.nc')
