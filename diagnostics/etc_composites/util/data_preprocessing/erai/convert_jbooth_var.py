import numpy as np
import xarray as xr
import os

import pdb

year_list = [1979, 1979]
# var_list = ['Z', 'T', 'U', 'V']
var_list = ['U', 'V', 'Z', 'T']

folder = '/mnt/drive5/ERAINTERIM/'
out_folder = '/localdrive/drive6/erai/converts/'

# keep adding to this
var_map = {'Z': 'var129', 'T': 'var130', 'U': 'var131', 'V': 'var132'}

# pressure values of the levels
pressure_list = [10, 20, 30, 50, 70, 100, 150, 200, 250, 300, 400, 500, 600, 700, 775, 850, 925, 1000]

# sample format of the output
sample = xr.open_dataset('/localdrive/drive6/erai/converts/z.1979.nc')

for year in range(year_list[0], year_list[1]+1):

  var_vals = np.zeros((len(pressure_list), len(sample.time), len(sample.lat), len(sample.lon)))
  for var in var_list: 
    out_file = os.path.join(out_folder, 'jbooth.{var.lower()}.{year}.nc')
    for i_pres, pres in enumerate(pressure_list):
      if (var in ['U', 'V']):
        var_file = os.path.join(folder, f'{var}/{var}{pres:04d}_{year}.nc')
      else: 
        var_file = os.path.join(folder, f'{var}/{var}{pres:04d}/{var}{pres:04d}_{year}.nc')
      
      ds = xr.open_dataset(var_file)
      tmp = ds[var_map[var]].isel(lev=0).values
      var_vals[i_pres, :, :, :] = tmp
      ds.close()

    var_vals = np.einsum('ijkl->jikl', var_vals)

    # create an empty dataset
    out = xr.Dataset({})

    # copying over the coords
    for key in ['lat', 'lon', 'lev', 'time']:
      out[key] = ds[key]

    # prepping the pressure level coords
    out['lev'] = pressure_list
    for key in sample.lev.attrs.keys():
      out['lev'].attrs[key] = sample.lev.attrs[key]

    # copying over the variable values
    out[var.lower()] = (('time', 'lev', 'lat', 'lon'), var_vals)
    for key in ds[var_map[var]].attrs.keys():
      out[var.lower()].attrs[key] = ds[var_map[var]].attrs[key]

    # writing the outputs
    out.to_netcdf(out_file)
    print(f'Completed {var.upper()} for {year}')
    # end for pres
  # end for var
# end for year

