#!/usr/bin/env python

import numpy as np 
import xarray as xr
import matplotlib.pyplot as plt
import os


# fn = '/localdrive/drive10/mcms_tracker/FIXME_slp_converts/era5/topo.nc'
# out_fn = '/localdrive/drive10/mcms_tracker/FIXME_slp_converts/era5/era5.hgt.nc'

# fn = '/localdrive/drive10/mcms_tracker/FIXME_slp_converts/era5/topo_2deg.nc'
# out_fn = '/localdrive/drive10/mcms_tracker/FIXME_slp_converts/era5/era5.hgt_2deg.nc'

fn = '/localdrive/drive6/era5/invariants.nc'
out_fn = '/localdrive/drive6/era5/convert_invariants.nc'
# out_fn = '/localdrive/drive10/mcms_tracker/FIXME_slp_converts/era5/era5.hgt.nc'

# # Standard sample output that is used by the tracker
# tmp = '/localdrive/drive10/mcms_tracker/RUNDIR/TOPO365/rwcntrl_hgt.nc'
# ds_tmp = xr.open_dataset(tmp)
# print('STANDARD')
# print(ds_tmp.hgt)
# # ds_tmp.hgt.where(ds_tmp.hgt > 50).plot()
# # plt.pcolormesh(ds_tmp.hgt)
# # plt.colorbar()
# # plt.show()
# print('\n ================================== \n')
# print('\n ================================== \n')
# print('\n ================================== \n')

ds = xr.open_dataset(fn)
# ds = ds.isel(time=0)
ds = ds.rename({'z': 'hgt', 'latitude': 'lat', 'longitude': 'lon'})
ds['hgt'] = ds['hgt']/9.8
ds.hgt.attrs['units'] = 'm'
ds.to_netcdf(out_fn)
