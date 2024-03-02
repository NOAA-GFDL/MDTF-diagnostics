"""
Run this on OTC to compute reference state for 1 timestep
"""
import os
import numpy as np
import xarray as xr                # python library we use to read netcdf files
from diagnostics.finite_amplitude_wave_diag.finite_amplitude_wave_diag_utils import gridfill_each_level
from hn2016_falwa.xarrayinterface import QGDataset
import matplotlib.pyplot as plt
from hn2016_falwa.oopinterface import QGFieldNHN22


wk_dir = f"{os.environ['HOME']}/Dropbox/GitHub/mdtf/wkdir/"
data_dir = f"{os.environ['HOME']}/Dropbox/GitHub/hn2016_falwa/github_data_storage/"
u_path = f"{data_dir}atmos_inst_1tstep_u.nc"
v_path = f"{data_dir}atmos_inst_1tstep_v.nc"
t_path = f"{data_dir}atmos_inst_1tstep_t.nc"
gridfill_u_path = u_path.replace("u.nc", "u_gridfill.nc")
gridfill_v_path = v_path.replace("v.nc", "v_gridfill.nc")
gridfill_t_path = t_path.replace("t.nc", "t_gridfill.nc")

coord_file = xr.open_dataset(u_path)
xlon = coord_file.coords['lon']
ylat = coord_file.coords['lat']
plev = coord_file.coords['level']
coord_file.close()

u_file = xr.open_dataset(u_path)
v_file = xr.open_dataset(v_path)
t_file = xr.open_dataset(t_path)

# *** Examine data first ***
to_examine_data = False
if to_examine_data:
    zonal_mean_u = np.ma.masked_invalid(u_file.ua.values).mean(axis=-1)
    zonal_mean_v = np.ma.masked_invalid(v_file.va.values).mean(axis=-1)
    zonal_mean_t = np.ma.masked_invalid(t_file.ta.values).mean(axis=-1)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 3))
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
    plt.show()
    print("Stop here")


