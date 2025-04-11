import os
import xarray as xr
from stc_annular_modes_calc import eof_annular_mode, anomalize_geohgt


out_dir = os.environ['DATA_OUTPUT_DIR']

# BEGIN: READ INPUT FIELDS ###
# The following code/paths will have to be adapted for your own system.
# Data provided for the stc_annular_modes POD of MDTF was originally
# derived from ERA5 reanalysis zonal mean geopotential heights
print('*** Reading in zonal mean geopotential heights')
zzm_fi = os.environ['REAN_ZZM']
zzm = xr.open_dataarray(zzm_fi)

# Compute the reanalysis NAM and SAM indices
print('*** Computing the reanalysis NAM and SAM loading patterns and PC time series')
nam, nam_struc = eof_annular_mode(anomalize_geohgt(zzm, "NH", anom='gerber'))
sam, sam_struc = eof_annular_mode(anomalize_geohgt(zzm, "SH", anom='gerber'))

# Output the reanalysis PC time series for both hemispheres
print('*** Now outputting the PC time series')
am = xr.concat((sam.assign_coords({'hemi': -1}),
                nam.assign_coords({'hemi': 1})), dim='hemi')
am.name = 'pc1'
am.attrs['long_name'] = 'PC1 time series of Zonal Mean Geohgt Anomalies'
am.attrs['units'] = 'unitless'
am.hemi.attrs['long_name'] = 'hemisphere (-1 for SH, 1 for NH)'

outfile = f'{out_dir}/era5_annmodes_1979-2021.nc'
encoding = {'pc1': {'dtype': 'float32'}}
am.to_netcdf(outfile, encoding=encoding)

# Output the reanalysis NH EOF1 structure
print('*** Now saving NH EOF1 structure')
nam_struc.name = 'eof1'
nam_struc.attrs['long_name'] = 'EOF1 of NH Zonal Mean Geohgt Anomalies'

outfile = f'{out_dir}/era5_nam_lat-struc_1979-2021.nc'
encoding = {'eof1': {'dtype': 'float32'}}
nam_struc.to_netcdf(outfile, encoding=encoding)

# Output the reanalysis SH EOF1 structure
print('*** Now saving SH EOF1 structure')
sam_struc.name = 'eof1'
sam_struc.attrs['long_name'] = 'EOF1 of SH Zonal Mean Geohgt Anomalies'

outfile = f'{out_dir}/era5_sam_lat-struc_1979-2021.nc'
encoding = {'eof1': {'dtype': 'float32'}}
sam_struc.to_netcdf(outfile, encoding=encoding)
