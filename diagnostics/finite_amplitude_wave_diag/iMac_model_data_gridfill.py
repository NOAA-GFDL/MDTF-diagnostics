"""
Run this on OTC to compute reference state for 1 timestep
"""
import os
import numpy as np
import xarray as xr                # python library we use to read netcdf files
from diagnostics.finite_amplitude_wave_diag.finite_amplitude_wave_diag_zonal_mean import gridfill_each_level
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

all_file = xr.open_mfdataset("atmos_inst_t1000_[uvt].nc")
gridfill_file = "atmos_inst_t1000_gridfill_{var}.nc"

# *** First do poisson solver ***
run_poisson = True
if run_poisson:
    args_tuple = ['ua', 'va', 'ta']
    field_list = []
    for var_name in args_tuple:
        field_at_all_level = xr.apply_ufunc(
            gridfill_each_level,
            *[all_file[var_name]],
            input_core_dims=(('lat', 'lon'),),
            output_core_dims=(('lat', 'lon'),),
            vectorize=True, dask="allowed")
        gridfill_file_path = gridfill_file.format(var=var_name)
        field_at_all_level.to_netcdf(gridfill_file_path)
        print(f"Finished outputing {gridfill_file_path}")

# *** Interpolate onto regular grid ***
all_files = xr.open_mfdataset("atmos_inst_t1000_gridfill_[uvt]a.nc")
all_files = all_files.interp(
    coords={
        "lat": np.arange(-90, 91, 1.5),
        "lon": np.arange(0, 361, 1.5)},
    method="nearest",
    kwargs={"fill_value": "extrapolate"})
qgds = QGDataset(all_files, var_names={"u": "ua", "v": "va", "t": "ta"}, qgfield=QGFieldNHN22)
uvtinterp = qgds.interpolate_fields()
plt.contourf(
    uvtinterp['interpolated_u'].ylat,
    uvtinterp['interpolated_u'].height,
    uvtinterp['interpolated_u'].mean(axis=-1),
    np.arange(-50, 51, 5))
plt.colorbar()
plt.show()
print("Finished interpolate_fields")
refstates = qgds.compute_reference_states()  # Error arises when solving reference state
plt.contourf(refstates['uref'].ylat,
             refstates['uref'].height,
             refstates['uref'],
             np.arange(-50, 51, 5))
plt.colorbar()
plt.show()
print("Finished compute_reference_states")


