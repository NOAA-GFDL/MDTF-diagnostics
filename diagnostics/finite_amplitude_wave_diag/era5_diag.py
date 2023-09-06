import os
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
from hn2016_falwa.xarrayinterface import QGDataset

# 0) Get environment variables
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
data_u = xr.open_dataset(input_u_path)
data_v = xr.open_dataset(input_v_path)
data_t = xr.open_dataset(input_t_path)

# Select DJF and do daily mean
data_u = data_u.sel(time=data_u.time.dt.month.isin([1, 2, 12])).resample(time="1D").mean(dim="time")
data_v = data_v.sel(time=data_v.time.dt.month.isin([1, 2, 12])).resample(time="1D").mean(dim="time")
data_t = data_t.sel(time=data_t.time.dt.month.isin([1, 2, 12])).resample(time="1D").mean(dim="time")

# 2) Doing computations:
qgds = QGDataset(data_u, data_v, data_t, var_names={"u": u_var_name, "v": v_var_name, "t": t_var_name})
uvtinterp = qgds.interpolate_fields()
refstates = qgds.compute_reference_states()
lwadiags = qgds.compute_lwa_and_barotropic_fluxes()
print("Finished")


data.sel(time=data.time.dt.month.isin([1, 2, 3, 10, 11, 12]))
