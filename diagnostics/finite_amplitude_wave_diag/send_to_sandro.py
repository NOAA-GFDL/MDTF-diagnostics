"""
Extract some sample data and send to Sandro
"""
import os
import numpy as np
import xarray as xr                # python library we use to read netcdf files
import matplotlib.pyplot as plt    # python library we use to make plots
from hn2016_falwa.xarrayinterface import QGDataset


# *** Combine files ***
file_handle = xr.open_mfdataset(f"send_to_sandro_t*.nc")
print(file_handle)
print(file_handle.coords['time'])


to_output_step_by_step = False
if to_output_step_by_step:
    original_file_path = f"{os.environ['HOME']}/GitHub/mdtf/inputdata/model/GFDL-CM4/data/atmos_inst/ts/hourly/1yr/"+\
                         "atmos_inst.1984010100-1984123123.[uvt]a.nc"
    for tstep in np.arange(0, 8760, 730):
        file_handle = xr.open_mfdataset(original_file_path).isel(time=tstep)
        print("file_handle")
        print(file_handle)
        filename = f"send_to_sandro_t{tstep}.nc"
        print(f"Start outputting {filename}")
        file_handle.to_netcdf(filename)
        print(f"Finished outputting {filename}")
