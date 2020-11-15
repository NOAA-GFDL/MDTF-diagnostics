#!/usr/bin/env python

# CMEMS Sea Level data IO


"""
Data is downloaded from CMEMS (the original AVISO dataset)

Ftp server is the fastest way to manage download
http://marine.copernicus.eu/services-portfolio/access-to-products/?option=com_csw&view=details&product_id=SEALEVEL_GLO_PHY_L4_REP_OBSERVATIONS_008_047 

The daily data is preprocessed to monthly data in this script

"""

import xarray as xr
import numpy as np
import os
import cftime



basedir=os.getcwd()
datadir_parent='../data/CMEMS/'
dataname_begin='dt_global_allsat_phy_l4_'
var='adt'        # adt/sla 
start_year=1993
start_month=1
end_year=2018
end_month=9

# initialization
path=os.path.join(basedir,datadir_parent,'%0.4i'%start_year)
file=[ff for ff in os.listdir(path) if ff.startswith(dataname_begin)][0]
inidataset=os.path.join(path,file)
da_ini=xr.open_dataset(inidataset).sla

time=xr.cftime_range(start=cftime.datetime(start_year,start_month,1),end=cftime.datetime(end_year,end_month,31),freq='MS')
time=time.to_datetimeindex()

nt=len(time)
nlon=da_ini.shape[2]
nlat=da_ini.shape[1]

da_sla_mon=xr.DataArray(np.zeros([nt,nlat,nlon])
             ,coords={'time':time,'latitude':da_ini.latitude,'longitude':da_ini.longitude}
             ,dims=['time','latitude','longitude'])


for yind,year in enumerate(np.arange(start_year,end_year+1,1)):
    datasets=[]
    path=os.path.join(basedir,datadir_parent,'%0.4i'%year)
    print(path)
    if os.path.isdir(path):
        for file in os.listdir(path):
            if file.startswith(dataname_begin):
                datasets.append(os.path.join(basedir,datadir_parent,'%0.4i'%year,file))

    # open dask dataset
    da=xr.open_mfdataset(datasets,combine='by_coords',chunks={'latitude':50,'longitude':50})['%s'%var]

    # calculate monthly mean of each year
    da_mon=da.groupby('time.month').mean('time')

    # assign to the monthly xr.DataArray
    if year == start_year :
        da_sla_mon = da_mon.copy()
    else:
        da_sla_mon = xr.merge([da_sla_mon,da_mon])


    
ds_sla_mon=xr.Dataset()
ds_sla_mon['%s'%var]=da_sla_mon
outputname=dataname_begin+'monthly_%s.nc'%var
ds_sla_mon.to_netcdf(os.path.join(basedir,datadir_parent,outputname))