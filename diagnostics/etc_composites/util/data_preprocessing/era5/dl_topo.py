#!/usr/bin/env python
import cdsapi

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': ['orography', 'land_sea_mask'],
        'year': '2000',
        'month': '01',
        'day': '01',
        'time': '00:00',
        'format': 'netcdf',
        'grid': '1.0/1.0', 
        # 'grid': '2.0/2.0', 
    },
    'invariants.nc')

c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': 'land_sea_mask',
        'year': '2000',
        'month': '01',
        'day': '01',
        'time': '00:00',
        'format': 'netcdf',
        'grid': '1.0/1.0', 
        # 'grid': '2.0/2.0', 
    },
    'lm_2deg.nc')
