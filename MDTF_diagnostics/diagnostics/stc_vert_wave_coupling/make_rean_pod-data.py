import os

import numpy as np
import xarray as xr

from stc_vert_wave_coupling_calc import lat_avg, \
    zonal_wave_covariance, zonal_wave_coeffs

out_dir = os.environ['DATA_OUTPUT_DIR']

### BEGIN: READ INPUT FIELDS ###
# The following code/paths will have to be adapted for your own system.
# Data provided for the stc_vert_wave_coupling POD of MDTF was originally
# derived from ERA5 reanalysis regridded to 2.5x2.5 lat/lon
z10_fi = os.environ['REAN_Z10']    # era5.2p5.zg10.nc
z500_fi = os.environ['REAN_Z500']  # era5.2p5.zg500.nc
v50_fi = os.environ['REAN_V50']    # era5.2p5.va50.nc
t50_fi = os.environ['REAN_T50']    # era5.2p5.ta50.nc

z10 = xr.open_dataarray(z10_fi)
z500 = xr.open_dataarray(z500_fi)
v50 = xr.open_dataarray(v50_fi)
t50 = xr.open_dataarray(t50_fi)

# Fourier decomposition, keeping waves-13
print('*** Computing 10 and 500 hPa zonal Fourier coefficients')
z_k = xr.concat((zonal_wave_coeffs(z10, keep_waves=[1, 2, 3]).assign_coords({'lev': 10}),
                 zonal_wave_coeffs(z500, keep_waves=[1, 2, 3]).assign_coords({'lev': 500})), 'lev')

# Save the coefficients for 60lat. NetCDF can't handle
# complex data, so split things into real/imag variables
print('*** Saving the reanalysis FFT coefficients for +/- 60 lat')
tmp = z_k.sel(lat=[-60, 60])

z_k_real = np.real(tmp)
z_k_real.name = 'z_k_real'
z_k_imag = np.imag(tmp)
z_k_imag.name = 'z_k_imag'
dat2save = xr.merge([z_k_real, z_k_imag])

dat2save.z_k_real.attrs['long_name'] = 'Real part of longitudinal Fourier Transform of Geopot. Height'
dat2save.z_k_real.attrs['units'] = 'm'
dat2save.z_k_imag.attrs['long_name'] = 'Imaginary part of longitudinal Fourier Transform of Geopot. Height'
dat2save.z_k_imag.attrs['units'] = 'm'

outfile = f'{out_dir}/era5_60-lat_hgt-zonal-fourier-coeffs.nc'
encoding = {'z_k_real': {'dtype': 'float32'},
            'z_k_imag': {'dtype': 'float32'}}

dat2save.to_netcdf(outfile, encoding=encoding)


# Do similarly as above, but instead for the coefficients averaged over
# 45-80 latitude bands.
print('*** Computing the 45-80 latitude band averages of the Fourier coefficients')
z_k_4580 = xr.concat((lat_avg(z_k, -80, -45).assign_coords({'hemi': -1}),
                      lat_avg(z_k, 45, 80).assign_coords({'hemi': 1})), dim='hemi')

print('*** Saving the reanalysis FFT coefficients for 45-80 lat bands')
z_k_real = np.real(z_k_4580)
z_k_real.name = 'z_k_real'
z_k_imag = np.imag(z_k_4580)
z_k_imag.name = 'z_k_imag'
dat2save = xr.merge([z_k_real, z_k_imag])

dat2save.z_k_real.attrs['long_name'] = 'Real part of 45-80 lat band average of ' +\
                              'longitudinal Fourier Transform of Geopot. Height'
dat2save.z_k_real.attrs['units'] = 'm'
dat2save.z_k_imag.attrs['long_name'] = 'Imag part of 45-80 lat band average of ' +\
                              'longitudinal Fourier Transform of Geopot. Height'
dat2save.z_k_imag.attrs['units'] = 'm'

dat2save.hemi.attrs['long_name'] = 'hemisphere (-1 for SH, 1 for NH)'

outfile = f'{out_dir}/era5_45-80-lat_hgt-zonal-fourier-coeffs.nc'
encoding = {'z_k_real': {'dtype': 'float32'},
            'z_k_imag': {'dtype': 'float32'}}
dat2save.to_netcdf(outfile, encoding=encoding)


# Compute the wave decomposed eddy heat fluxes,
# keeping only waves 1-3
print('*** Computing the 50 hPa eddy heat flux as a function of zonal wavenumber')
vt50_k = zonal_wave_covariance(v50, t50, keep_waves=[1, 2, 3])

# Compute polar cap averages and save
print('*** Computing polar cap averages of eddy heat fluxes')
vt50_k_pcap = xr.concat((lat_avg(vt50_k, -90, -60).assign_coords({'hemi': -1}),
                         lat_avg(vt50_k, 60,   90).assign_coords({'hemi': 1})), dim='hemi')

print('*** Saving the reanalysis polar cap eddy heat fluxes')
vt50_k_pcap.name = 'ehf_pcap_50'
vt50_k_pcap.attrs['long_name'] = '50 hPa 60-90 lat polar cap eddy heat flux'
vt50_k_pcap.attrs['units'] = 'K m s-1'
vt50_k_pcap.hemi.attrs['long_name'] = 'hemisphere (-1 for SH, 1 for NH)'

outfile = f'{out_dir}/era5_50hPa_pcap_eddy-heat-flux.nc'
encoding = {'ehf_pcap_50': {'dtype': 'float32'}}
vt50_k_pcap.to_netcdf(outfile, encoding=encoding)


# Compute the eddy height fields, and provide these for
# JFM for the NH, and SON for the SH
print('*** Computing the 10 and 500 hPa eddy height fields')
zeddy = xr.concat(((z10 - z10.mean('lon')).assign_coords({'lev': 10}),
                   (z500 - z500.mean('lon')).assign_coords({'lev': 500})), dim='lev')

print('*** Saving the reanalysis eddy height fields')
outfile = f'{out_dir}/era5_zg-eddy_NH-JFM-only_2p5.nc'
zeddy_nh = zeddy.sel(lat=slice(90, 0)).where(zeddy['time.month'].isin([1, 2, 3]), drop=True)
zeddy_nh.attrs['long_name'] = 'Eddy geopotential height'
zeddy_nh.to_netcdf(outfile)

outfile = f'{out_dir}/era5_zg-eddy_SH-SON-only_2p5.nc'
zeddy_sh = zeddy.sel(lat=slice(0, -90)).where(zeddy['time.month'].isin([9, 10, 11]), drop=True)
zeddy_sh.attrs['long_name'] = 'Eddy geopotential height'
zeddy_sh.to_netcdf(outfile)
