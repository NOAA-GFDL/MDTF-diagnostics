"""
Extract some sample data and send to Sandro
"""
import os
import numpy as np
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
from hn2016_falwa.xarrayinterface import QGDataset

original_file_path = f"{os.environ['HOME']}/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/atmos_inst.1984010100-1984123123.[uvt]a.nc"
file_handle = xr.open_mfdataset(original_file_path).isel(time=np.arange(0, 8761, 730))
print("file_handle")
print(file_handle)
