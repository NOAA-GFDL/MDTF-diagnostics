"""
Run this on OTC to compute reference state for 1 timestep
"""
import os
import xarray as xr                # python library we use to read netcdf files


wk_dir = f"{os.environ['HOME']}/GitHub/mdtf/wkdir/"
data_dir = f"{os.environ['HOME']}/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/"
u_path = f"{data_dir}atmos_inst.1984010100-1984123123.ua.nc"
v_path = f"{data_dir}atmos_inst.1984010100-1984123123.va.nc"
t_path = f"{data_dir}atmos_inst.1984010100-1984123123.ta.nc"

# Extract just one timestamp
data = xr.open_mfdataset(f"{data_dir}atmos_inst.1984010100-1984123123.[uvt]a.nc")
print(data)


