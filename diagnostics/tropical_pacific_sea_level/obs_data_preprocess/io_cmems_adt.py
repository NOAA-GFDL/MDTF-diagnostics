#!/usr/bin/env python

# CMEMS Sea Level data IO


"""
Data is downloaded from CMEMS (the original AVISO dataset)

Ftp server is the fastest way to manage download

http://marine.copernicus.eu/services-portfolio/access-to-products/

search for product ID :
SEALEVEL_GLO_PHY_L4_REP_OBSERVATIONS_008_047 

Need to download the daily data with adt (absolute dynamic topography) available 

The daily data is preprocessed to monthly data in this script

"""

import xarray as xr
import numpy as np
import os
import cftime



# absolute path to the data directory
basedir='/storage1/home1/chiaweih/Research/proj3_omip_sl/data/CMEMS/'   

# data file name starts with 
dataname_begin='dt_global_allsat_phy_l4_'

# variable name
var='adt'        

# time period for processing the daily output
#  this can be changed based on used download period

start_year=1993
start_month=1
end_year=2018
end_month=9

for yind,year in enumerate(np.arange(start_year,end_year+1,1)):
    datasets=[]
    path=os.path.join(basedir,'%0.4i'%year)
    print(path)
    if os.path.isdir(path):
        for file in os.listdir(path):
            if file.startswith(dataname_begin):
                datasets.append(os.path.join(basedir,'%0.4i'%year,file))

    # open dataset
    datasets = sorted(datasets)
    for nfile,file in enumerate(datasets):
        da = xr.open_dataset(file)[var]
        if nfile == 0 :
            da_concat = da.copy()
        else :
            da_concat = xr.concat([da_concat,da],dim='time')
    del da
    da = da_concat
#     da=xr.open_mfdataset(datasets,combine='by_coords',chunks={'latitude':50,'longitude':50})[var]

    # calculate monthly mean of each year
    da_mon = da.groupby('time.month').mean('time')
    time=xr.cftime_range(start=cftime.datetime(year,1,1),end=cftime.datetime(year,12,1),freq='MS',calendar='standard')
    time=time.to_datetimeindex()
    da_mon['month'] = time
    da_mon = da_mon.rename({'month':'time'})

    # assign to the monthly xr.DataArray
    if year == start_year :
        da_mon_total = da_mon.copy()
    else:
        da_mon_total = xr.concat([da_mon_total,da_mon],dim='time')
        
ds_total = xr.Dataset()
ds_total[var]=da_mon_total
outputname=dataname_begin+'monthly_%s.nc'%var
ds_total.to_netcdf(os.path.join(basedir,outputname))