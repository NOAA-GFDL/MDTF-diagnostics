"""
Run this on OTC to compute reference state for 1 timestep
"""
import os
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


wk_dir = f"{os.environ['HOME']}/GitHub/mdtf/wkdir/"
data_dir = f"{os.environ['HOME']}/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/"
u_path = f"{data_dir}atmos_inst.1984010100-1984123123.ua.nc"
v_path = f"{data_dir}atmos_inst.1984010100-1984123123.va.nc"
t_path = f"{data_dir}atmos_inst.1984010100-1984123123.ta.nc"

coord_file = xr.open_dataset(u_path)
xlon = coord_file.coords['lon']
ylat = coord_file.coords['lat']
plev = coord_file.coords['level']
coord_file.close()

u_file = xr.open_dataset(u_path)
v_file = xr.open_dataset(v_path)
t_file = xr.open_dataset(t_path)

# *** Examine data first ***
for tstep in np.arange(0, 8761, 50):
    zonal_mean_u = np.ma.masked_invalid(u_file.isel(time=tstep).ua.values).mean(axis=-1)
    zonal_mean_v = np.ma.masked_invalid(v_file.isel(time=tstep).va.values).mean(axis=-1)
    zonal_mean_t = np.ma.masked_invalid(t_file.isel(time=tstep).ta.values).mean(axis=-1)
    time_str = str(u_file.isel(time=tstep)['time'].values).split()[0]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 3))
    plt.suptitle(f"{time_str}")
    cs1 = ax1.contourf(ylat, plev, zonal_mean_u, 30, cmap='rainbow')
    ax1.set_title("Zonal mean zonal wind u")
    ax1.set_ylabel("Pressure [hPa]")
    ax1.set_xlabel("Longitude [deg]")
    fig.colorbar(cs1, ax=ax1, shrink=0.9)
    ax1.invert_yaxis()
    cs2 = ax2.contourf(ylat, plev, zonal_mean_v, 30, cmap='rainbow')
    ax2.set_title("Zonal mean meridional wind v")
    ax2.set_xlabel("Longitude [deg]")
    fig.colorbar(cs2, ax=ax2, shrink=0.9)
    ax2.invert_yaxis()
    cs3 = ax3.contourf(ylat, plev, zonal_mean_t, 30, cmap='rainbow')
    ax3.set_title("Zonal mean air temperature t")
    ax3.set_xlabel("Longitude [deg]")
    fig.colorbar(cs3, ax=ax3, shrink=0.9)
    ax3.invert_yaxis()
    plt.tight_layout()
    plt.savefig(f"zonal_mean_{time_str}.png")
    print(f"Finished processing {time_str}")


