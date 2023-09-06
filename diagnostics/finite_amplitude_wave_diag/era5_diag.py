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
data_u = xr.load_dataset(input_u_path).sel(season='DJF').resample(time="1D").mean(dim="time")
data_v = xr.load_dataset(input_v_path).sel(season='DJF').resample(time="1D").mean(dim="time")
data_t = xr.load_dataset(input_t_path).sel(season='DJF').resample(time="1D").mean(dim="time")

# 2) Doing computations:
qgds = QGDataset(data_u, data_v, data_t, var_names={"u": u_var_name, "v": v_var_name, "t": t_var_name})
uvtinterp = qgds.interpolate_fields()
refstates = qgds.compute_reference_states()
lwadiags = qgds.compute_lwa_and_barotropic_fluxes()
print("Finished")
