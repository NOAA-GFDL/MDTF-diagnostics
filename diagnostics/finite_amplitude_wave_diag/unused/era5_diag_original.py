# TODO: replace all with env variables
import os
import sys

sys.path.insert(0, "/home/clare/Dropbox/GitHub/hn2016_falwa")
import numpy as np
import xarray as xr
import datetime
from hn2016_falwa.xarrayinterface import QGDataset

def print_process_time(process, start_time):
    print(f"{process}. Time: {(datetime.datetime.now() - start_time).total_seconds()}")

start_time = datetime.datetime.now()
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

new_xlon = np.arange(0, 360)
new_ylat = np.arange(-90, 91)

print(f"Compute daily average and interp onto coarser grid. Time: {datetime.datetime.now()}")
# selected_months = [1, 2, 12]  # DJF
selected_months = [1]  # TODO testing
time_selected = u_file.time.dt.month.isin(selected_months)
data_u = u_file.sel(time=time_selected).resample(time="1D").first()\
    .interp(latitude=new_ylat, longitude=new_xlon, method="nearest")
data_v = v_file.sel(time=time_selected).resample(time="1D").first()\
    .interp(latitude=new_ylat, longitude=new_xlon, method="nearest")
data_t = t_file.sel(time=time_selected).resample(time="1D").first()\
    .interp(latitude=new_ylat, longitude=new_xlon, method="nearest")

print_process_time("Finished computing daily average and interp onto coarser grid", start_time)
print(data_u)
print(data_u.coords[ylat_coord_name])

# 3) Saving output data:
out_path = f"{wkdir}/refstates_2022Jan.nc"

print_process_time("Start QGDataset calculation", start_time)
qgds = QGDataset(da_u=data_u, da_v=data_v, da_t=data_t, var_names={"u": u_var_name, "v": v_var_name, "t": t_var_name})
uvtinterp = qgds.interpolate_fields()
refstates = qgds.compute_reference_states()
print_process_time("Examine yz_var", start_time)
print(refstates)
lwadiags = qgds.compute_lwa_and_barotropic_fluxes()
# TODO: interpolate back onto original grid?
print_process_time("Compute seasonal average", start_time)
seasonal_average = xr.merge([uvtinterp, refstates, lwadiags]).mean(dim=time_coord_name)
print(seasonal_average)
print_process_time(f"Start outputing to the file: {out_path}", start_time)
seasonal_average.to_netcdf(out_path)
print_process_time("Finished", start_time)


# 4) Saving output plots:

# 5) Loading obs data files & plotting obs figures

# 6) Cleaning up:
u_file.close()
v_file.close()
t_file.close()
