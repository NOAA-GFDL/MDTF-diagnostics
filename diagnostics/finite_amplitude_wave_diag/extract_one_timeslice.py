"""
Extract one time slice from model data from OTC
"""
import os
import xarray as xr

data_path = f"{os.environ['HOME']}/GitHub/mdtf/inputdata/model/CMIP5/output1/NOAA-GFDL/GFDL-CM3/historical/day/" + \
            "atmos/day/r1i1p1/v20120227/*a/[uvt]a_day_GFDL-CM3_historical_r1i1p1_20050101-20051231.nc"
data_file = xr.open_mfdataset(data_path).isel(time=0)
print(data_file)
data_file.to_netcdf("GFDL-CM3_historical_r1i1p1_20050101-20051231_1tslice.nc")
print("Finish")
