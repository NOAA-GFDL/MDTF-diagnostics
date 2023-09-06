import os
import sys
sys.path.insert(0, "/home/clare/Dropbox/GitHub/hn2016_falwa")
import math
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from hn2016_falwa.oopinterface import QGFieldNHN22
import hn2016_falwa.utilities as utilities

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
# u_file = u_file.sel(time=u_file.time.dt.month.isin(selected_months)).resample(time="1D").mean(dim="time")
# v_file = v_file.sel(time=v_file.time.dt.month.isin(selected_months)).resample(time="1D").mean(dim="time")
# t_file = t_file.sel(time=t_file.time.dt.month.isin(selected_months)).resample(time="1D").mean(dim="time")
u_file = u_file.isel(time=tstep)
v_file = v_file.isel(time=tstep)
t_file = t_file.isel(time=tstep)

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

print("Start QGDataset calculation.")

# 3) Saving output data:
out_path = f"{wkdir}/refstates.nc"
uu = u_file.u.values[::-1, ::-1, :]
vv = v_file.v.values[::-1, ::-1, :]
tt = t_file.t.values[::-1, ::-1, :]
qgfield_object = QGFieldNHN22(xlon, ylat, plev, uu, vv, tt, northern_hemisphere_results_only=False)
qgfield_object.interpolate_fields(return_named_tuple=False)
qgfield_object.compute_reference_states(return_named_tuple=False)
qgfield_object.compute_lwa_and_barotropic_fluxes(return_named_tuple=False)
print("Finished")



