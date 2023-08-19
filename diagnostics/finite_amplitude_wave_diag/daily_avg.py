"""
Compute daily average from sample files
"""
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots


u_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.ua.nc"
v_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.va.nc"
t_path = "/home/clare/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.ta.nc"
wk_dir = "/home/clare/GitHub/mdtf/wkdir/"


u_file = xr.open_dataset(u_path)  # xarray.Dataset
print(u_file)
print("================")
u_daily_avg = u_file['ua'].groupby("time.day").mean(dim='time')
print(u_daily_avg)
print("================")
print(f"u_daily_avg.shape:\n{u_daily_avg.shape}")
output_file = f"{wk_dir}u_daily_avg.nc"
print(f"Start outputing file: {output_file}")
u_daily_avg.to_netcdf(f"{wk_dir}u_daily_avg.nc")
print(f"Finished outputing file: {output_file}")
