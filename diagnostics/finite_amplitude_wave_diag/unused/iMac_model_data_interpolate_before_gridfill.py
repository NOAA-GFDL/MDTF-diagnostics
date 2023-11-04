"""
Run this on OTC to compute reference state for 1 timestep
Seems it is working on a coarse grid...
Continue from here next time
"""
import os
import numpy as np
import xarray as xr                # python library we use to read netcdf files
from diagnostics.finite_amplitude_wave_diag.finite_amplitude_wave_diag_zonal_mean import gridfill_each_level
from hn2016_falwa.xarrayinterface import QGDataset
import matplotlib.pyplot as plt
from hn2016_falwa.oopinterface import QGFieldNHN22, QGFieldNH18
from hn2016_falwa.xarrayinterface import hemisphere_to_globe


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

run_gridfill = True

all_files = xr.open_dataset("../GFDL-CM3_historical_r1i1p1_20050101-20051231_1tslice.nc")
all_files = all_files\
    .assign_coords({'plev': all_files.plev // 100})\
    .interp(
    coords={
        "lat": np.arange(-90, 91, 1.5),
        "lon": np.arange(0, 361, 1.5)},
    method="linear")
    # kwargs={"fill_value": "extrapolate"})  # installed package bottleneck
gridfill_file = "GFDL-CM3_historical_r1i1p1_20050101-20051231_1tslice_gridfill_{var}.nc"
gridfill_file_all = gridfill_file.format(var="[uvt]a")
# *** First do poisson solver ***
if run_gridfill:
    args_tuple = ['ua', 'va', 'ta']
    field_list = []
    for var_name in args_tuple:
        field_at_all_level = xr.apply_ufunc(
            gridfill_each_level,
            *[all_files[var_name].load()],
            input_core_dims=(('lat', 'lon'),),
            output_core_dims=(('lat', 'lon'),),
            vectorize=True, dask="forbidden")
        gridfill_file_path = gridfill_file.format(var=var_name)
        field_at_all_level.to_netcdf(gridfill_file_path)
        print(f"Finished outputing {gridfill_file_path}")
    all_files = xr.open_mfdataset(gridfill_file_all)
else:
    all_files = all_files.fillna(10)

# *** Create symmetric data ***
# all_files = hemisphere_to_globe(all_files)

# *** Interpolate onto regular grid ***
qgds = QGDataset(
    all_files,
    var_names={"u": "ua", "v": "va", "t": "ta"},
    qgfield=QGFieldNH18,
    qgfield_kwargs={"kmax": 33})
uvtinterp = qgds.interpolate_fields()
plt.contourf(
    uvtinterp['interpolated_u'].ylat,
    uvtinterp['interpolated_u'].height,
    uvtinterp['interpolated_u'].mean(axis=-1),
    40,
    cmap='rainbow')
plt.title("Zonal mean zonal wind")
plt.colorbar()
plt.show()
print("Finished interpolate_fields")
refstates = qgds.compute_reference_states()  # Error arises when solving reference state
plt.contourf(refstates['uref'].ylat[2:-2],
             refstates['uref'].height,
             refstates['uref'][:, 2:-2],
             40,
             cmap='rainbow')
plt.title("Uref")
plt.colorbar()
plt.show()
print("Finished compute_reference_states")
refstates = qgds.compute_lwa_and_barotropic_fluxes()  # Error arises when solving reference state
plt.contourf(refstates['lwa'].ylat,
             refstates['lwa'].height,
             refstates['lwa'].mean(axis=-1), 40, cmap='rainbow')
plt.title("Zonal mean FAWA")
plt.colorbar()
plt.show()
print("Finished compute_lwa_and_barotropic_fluxes")

plt.contourf(refstates['lwa_baro'].xlon,
             refstates['lwa_baro'].ylat,
             refstates['lwa_baro'],
             40, cmap='rainbow')
plt.title("Barotropic LWA")
plt.colorbar()
plt.show()

height_level_index = 10

plt.contourf(uvtinterp['qgpv'].xlon,
             uvtinterp['qgpv'].ylat[3:-3],
             uvtinterp['qgpv'].isel(height=height_level_index)[3:-3, :],
             40, cmap='rainbow')
plt.title(f"QGPV at k={height_level_index}")
plt.colorbar()
plt.show()

plt.contourf(refstates['lwa'].xlon,
             refstates['lwa'].ylat,
             refstates['lwa'].isel(height=height_level_index),
             40, cmap='rainbow')
plt.title(f"LWA at k={height_level_index}")
plt.colorbar()
plt.show()


