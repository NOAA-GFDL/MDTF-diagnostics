#!/usr/bin/env python
import numpy as np 
import xarray as xr
import os, glob
import pdb

folder = '/localdrive/drive6/era5/data/hrly/converts/'
out_folder = '/localdrive/drive6/era5/data/tmp_3hrly/'

for fn in glob.glob(os.path.join(folder, 'slp.*.nc')):
  ds = xr.open_dataset(fn)
  ds_sel = ds.isel(time=np.arange(0, len(ds.time), 3))
  fname = fn.split('/')[-1]

  print('Converting %s...'%(fn))
  out_file = os.path.join(out_folder, fname)
  year = fname.split('.')[1]

  time = np.arange(0, len(ds_sel.time)*3, 3)
  out_da = xr.DataArray(ds_sel.slp.values, coords={'time': time, 'lat': ds_sel.lat.values, 'lon': ds_sel.lon.values}, dims=['time', 'lat', 'lon'])

  # creating dataset
  out_ds = xr.Dataset({'slp': out_da})
  out_ds.slp.attrs['units'] = 'mb'

  out_ds.time.attrs['delta_t'] = '0000-00-00 03:00:00'
  out_ds.time.attrs['units'] = 'hours since %s-01-01 00:00:00'%(year)

  out_ds.lat.attrs['units'] = 'degrees_north'
  out_ds.lon.attrs['units'] = 'degrees_east'

  out_ds.to_netcdf(out_file)
