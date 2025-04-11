# 28 June top_heaviness_ratio_calculation.py
# Python packages/ modules imported for the diagnostic
# the sample monthly data is from ERA5 in July from 2000 to 2019 
import os
import xarray as xr
import numpy as np
from scipy import integrate
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.mpl.ticker as cticker

# Setting variables equal to environment variables set by the diagnostic
lat_coord = os.environ["lat_coord"]
lon_coord = os.environ["lon_coord"]
lev_coord = os.environ["lev_coord"]
omega_var = os.environ["omega_var"]
WK_DIR = os.environ["WORK_DIR"]
OBS_DATA = os.environ["OBS_DATA"]
CASENAME = os.environ["CASENAME"]


# ====================== deriving model output =======================
def top_heaviness_ratio_calculation_model(reanalysis_path, reanalysis_var):
    # read omega and land-sea fraction data
    ds = xr.open_dataset(reanalysis_path)
    lev_model = ds[lev_coord].values
    lat_model = ds[lat_coord].values
    lon_model = ds[lon_coord].values
    isort = np.argsort(lev_model)[::-1]  # descending
    mid_omega_model = ds[reanalysis_var].values  # mon x lev x lat x lon; for the sample data (July over 2000-2019)
    mid_omega_model = mid_omega_model[:, isort]
    # ======================deriving O1 and O2=======================
    # construct Q1_model as half a sine wave and Q2_model as a full sine wave
    # two base functions; Q1: idealized deep convection profile; Q2: Deep stratiform profile (Back et al. 2017)
    Q1_model = np.zeros(len(lev_model))
    Q2_model = np.zeros(len(lev_model))
    dp = lev_model[-1] - lev_model[0]
    for i in range(len(lev_model)):
        Q1_model[i] = -np.sin(np.pi * (lev_model[i] - lev_model[0]) / dp)
        Q2_model[i] = np.sin(2 * np.pi * (lev_model[i] - lev_model[0]) / dp)
    # Normalize
    factor = integrate.trapz(Q1_model * Q1_model, lev_model) / dp
    Q1_model = Q1_model / np.sqrt(factor)
    factor = integrate.trapz(Q2_model * Q2_model, lev_model) / dp
    Q2_model = Q2_model / np.sqrt(factor)
    # deriving O1 and O2; O1 and O2 are coefs of Q1 and Q2
    mid_omega_model_ltm = np.nanmean(mid_omega_model, axis=0)
    O1_model = integrate.trapz(mid_omega_model_ltm * Q1_model[:, None, None], lev_model, axis=0) / dp
    O2_model = integrate.trapz(mid_omega_model_ltm * Q2_model[:, None, None], lev_model, axis=0) / dp
    # ====================== set up figures =======================
    # ====================== O1 =======================
    fig, axes = plt.subplots(figsize=(8, 4))
    ilat = np.argsort(lat_model)
    ilon = np.argsort(lon_model)
    axes = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    clevs = np.arange(-0.06, 0.07, 0.01)
    im0 = axes.contourf(lon_model, lat_model, O1_model, clevs, cmap=plt.get_cmap('RdBu_r'), extend='both',
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
    axes.set_title('O1 [Pa/s]', loc='center', fontsize=16)
    fig.tight_layout()
    fig.savefig(WK_DIR + "/model/" + CASENAME + "_O1.png", format='png', bbox_inches='tight')
    # ====================== O2 =======================
    fig, axes = plt.subplots(figsize=(8, 4))
    axes = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    clevs = np.arange(-0.06, 0.07, 0.01)
    im0 = axes.contourf(lon_model, lat_model, O2_model, clevs, cmap=plt.get_cmap('RdBu_r'), extend='both',
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
    axes.set_title('O2 [Pa/s]', loc='center', fontsize=16)
    fig.tight_layout()
    fig.savefig(WK_DIR + "/model/" + CASENAME + "_O2.png", format='png', bbox_inches='tight')
    # ====================== O2/O1 top-heaviness ratio =======================
    fig, axes = plt.subplots(figsize=(8, 4))
    mmid1 = O2_model / O1_model
    midi = O1_model < 0.01  # We only investigate areas with O1 larger than zero
    mmid1[midi] = np.nan
    axes = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    clevs = np.arange(-0.6, 0.7, 0.1)
    im0 = axes.contourf(lon_model, lat_model, mmid1, clevs, cmap=plt.get_cmap('RdBu_r'), extend='both',
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
    axes.set_title('Top-heaviness Ratio (O2/O1)', loc='center', fontsize=18)
    fig.tight_layout()
    fig.savefig(WK_DIR + "/model/" + CASENAME + "_Top_Heaviness_Ratio.png", format='png', bbox_inches='tight')
    print("Plotting Completed")


top_heaviness_ratio_calculation_model(os.environ["OMEGA_FILE"], os.environ["omega_var"])


# ====================== deriving obs output =======================
# run obs data (ERA5 2000-2019 July only)

def top_heaviness_ratio_calculation_obs(obs_data_full_dir):
    # read omega 
    ds = xr.open_dataset(obs_data_full_dir)
    lev_obs = ds['lev'].values
    lat_obs = ds['lat'].values
    lon_obs = ds['lon'].values
    isort = np.argsort(lev_obs)[::-1]  # descending
    mid_omega_obs = ds['omega'].values  # mon x lev x lat x lon; for the sample data (July over 2000-2019)
    mid_omega_obs = mid_omega_obs[:, isort]
    # ======================deriving O1 and O2=======================
    # construct Q1_obs as half a sine wave and Q2_obs as a full sine wave
    # two base functions; Q1: idealized deep convection profile; Q2: Deep stratiform profile (Back et al. 2017)
    Q1_obs = np.zeros(len(lev_obs))
    Q2_obs = np.zeros(len(lev_obs))
    dp = lev_obs[-1] - lev_obs[0]
    for i in range(len(lev_obs)):
        Q1_obs[i] = -np.sin(np.pi * (lev_obs[i] - lev_obs[0]) / dp)
        Q2_obs[i] = np.sin(2 * np.pi * (lev_obs[i] - lev_obs[0]) / dp)
    # Normalize
    factor = integrate.trapz(Q1_obs * Q1_obs, lev_obs) / dp
    Q1_obs = Q1_obs / np.sqrt(factor)
    factor = integrate.trapz(Q2_obs * Q2_obs, lev_obs) / dp
    Q2_obs = Q2_obs / np.sqrt(factor)
    # deriving O1 and O2; O1 and O2 are coefs of Q1 and Q2
    mid_omega_obs_ltm = np.nanmean(mid_omega_obs, axis=0)
    O1_obs = integrate.trapz(mid_omega_obs_ltm * Q1_obs[:, None, None], lev_obs, axis=0) / dp
    O2_obs = integrate.trapz(mid_omega_obs_ltm * Q2_obs[:, None, None], lev_obs, axis=0) / dp
    # ====================== set up figures =======================
    # ====================== O1 =======================
    fig, axes = plt.subplots(figsize=(8, 4))
    ilat = np.argsort(lat_obs)
    ilon = np.argsort(lon_obs)
    axes = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    clevs = np.arange(-0.06, 0.07, 0.01)
    im0 = axes.contourf(lon_obs, lat_obs, O1_obs, clevs, cmap=plt.get_cmap('RdBu_r'), extend='both',
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
    axes.set_title('O1 [Pa/s]', loc='center', fontsize=16)
    fig.tight_layout()
    fig.savefig(WK_DIR + "/obs/ERA5_O1_2000_2019_July.png", format='png', bbox_inches='tight')
    # ====================== O2 =======================
    fig, axes = plt.subplots(figsize=(8, 4))
    axes = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    clevs = np.arange(-0.06, 0.07, 0.01)
    im0 = axes.contourf(lon_obs, lat_obs, O2_obs, clevs, cmap=plt.get_cmap('RdBu_r'), extend='both',
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
    axes.set_title('O2 [Pa/s]', loc='center', fontsize=16)
    fig.tight_layout()
    fig.savefig(WK_DIR + "/obs/ERA5_O2_2000_2019_July.png", format='png', bbox_inches='tight')
    # ====================== O2/O1 top-heaviness ratio =======================
    fig, axes = plt.subplots(figsize=(8, 4))
    mmid1 = O2_obs / O1_obs
    midi = O1_obs < 0.01  # We only investigate areas with O1 larger than zero
    mmid1[midi] = np.nan
    axes = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    clevs = np.arange(-0.6, 0.7, 0.1)
    im0 = axes.contourf(lon_obs, lat_obs, mmid1, clevs, cmap=plt.get_cmap('RdBu_r'), extend='both',
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
    axes.set_title('Top-heaviness Ratio (O2/O1)', loc='center', fontsize=18)
    fig.tight_layout()
    fig.savefig(WK_DIR + "/obs/ERA5_Top_Heaviness_Ratio_2000_2019_July.png", format='png', bbox_inches='tight')
    print("Plotting Completed")


top_heaviness_ratio_calculation_obs(OBS_DATA + '/ERA5_omega_mon_2000_2019_July.nc')
