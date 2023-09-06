import os
import sys
sys.path.insert(0, "/home/clare/Dropbox/GitHub/hn2016_falwa")
import math
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from hn2016_falwa.oopinterface import QGFieldNHN22
from hn2016_falwa.xarrayinterface import QGDataset

# 0) Get environment variables
wkdir = os.environ['wkdir']
input_u_path = os.environ["u_file"]
input_v_path = os.environ["v_file"]
input_t_path = os.environ["t_file"]
u_var_name = os.environ["u_var_name"]
v_var_name = os.environ["v_var_name"]
t_var_name = os.environ["t_var_name"]
time_coord_name = os.environ["time_coord"]
xlon_coord_name = os.environ["xlon_coord"]
ylat_coord_name = os.environ["ylat_coord"]
plev_coord_name = os.environ["plev_coord"]

# 1) Loading model data files:
u_file = xr.open_dataset(input_u_path)
v_file = xr.open_dataset(input_v_path)
t_file = xr.open_dataset(input_t_path)

# Select DJF and do daily mean
# selected_months = [1, 2, 12]
print("Start computing daily mean.")
tstep = 100
selected_months = [1]

# 2) Doing computations:
print("Set coordinates")
ntimes = u_file.time.size
time_array = u_file.time
xlon = u_file.longitude.values
# latitude has to be in ascending order
print(u_file.latitude)
ylat = u_file.latitude.values
if np.diff(ylat)[0] < 0:
    print('Flip ylat.')
    ylat = ylat[::-1]
# pressure level has to be in descending order (ascending height)
print(u_file.level)
plev = u_file.level.values
if np.diff(plev)[0] > 0:
    print('Flip plev.')
    plev = plev[::-1]
nlon = xlon.size
nlat = ylat.size
nlev = plev.size

selected_months = [1]
new_xlon = np.arange(0, 360)
new_ylat = np.arange(-90, 91)

print("Compute daily average and interp onto coarser grid.")
data_u = u_file.isel(time=np.arange(1, 11)).resample(time="1D").mean(dim="time")\
    .interp(latitude=new_ylat, longitude=new_xlon, method="linear")
data_v = v_file.isel(time=np.arange(1, 11)).resample(time="1D").mean(dim="time")\
    .interp(latitude=new_ylat, longitude=new_xlon, method="linear")
data_t = t_file.isel(time=np.arange(1, 11)).resample(time="1D").mean(dim="time")\
    .interp(latitude=new_ylat, longitude=new_xlon, method="linear")

# data_u = u_file.sel(time=u_file.time.dt.month.isin(selected_months)).resample(time="1D").mean(dim="time")\
#     .interp(latitude=new_ylat, longitude=new_xlon, method="linear")
# data_v = v_file.sel(time=u_file.time.dt.month.isin(selected_months)).resample(time="1D").mean(dim="time")\
#     .interp(latitude=new_ylat, longitude=new_xlon, method="linear")
# data_t = t_file.sel(time=u_file.time.dt.month.isin(selected_months)).resample(time="1D").mean(dim="time")\
#     .interp(latitude=new_ylat, longitude=new_xlon, method="linear")

print("Examine data_u:")
print(data_u)
print(data_u.coords['latitude'])

# 3) Saving output data:
out_path = f"{wkdir}/refstates.nc"

print("=== Start QGDataset calculation ===")
qgds = QGDataset(da_u=data_u, da_v=data_v, da_t=data_t, var_names={"u": u_var_name, "v": v_var_name, "t": t_var_name})
uvtinterp = qgds.interpolate_fields()
refstates = qgds.compute_reference_states()
print("Examine refstates:")
print(refstates)
lwadiags = qgds.compute_lwa_and_barotropic_fluxes()
lwadiags = lwadiags[["lwa_baro", "u_baro", "lwa"]]
print(f"Start outputing to the file: {out_path}")
xr.merge([refstates, lwadiags]).to_netcdf(out_path)
print("Finished")

old_interface = False
if old_interface:
    uu = data_u.u.values[::-1, :, :]
    vv = data_v.v.values[::-1, :, :]
    tt = data_t.t.values[::-1, :, :]
    qgfield_object = QGFieldNHN22(new_xlon, new_ylat, plev, uu, vv, tt, northern_hemisphere_results_only=False)
    qgfield_object.interpolate_fields(return_named_tuple=False)
    qgfield_object.compute_reference_states(return_named_tuple=False)
    qgfield_object.compute_lwa_and_barotropic_fluxes(return_named_tuple=False)
    print("Finished")



