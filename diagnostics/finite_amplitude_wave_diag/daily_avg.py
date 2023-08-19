"""
Compute daily average from sample files
"""
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots


u_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.ua.nc"
v_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.va.nc"
t_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.ta.nc"

u_file = xr.open_dataset(u_path)  # xarray.Dataset
print(u_file)
u_field = u_file['ua'].isel(time=slice(0, 500))
print(u_field)
ans = u_field.groupby("time.month").mean(dim='time')
print(ans)
print(ans.shape)
