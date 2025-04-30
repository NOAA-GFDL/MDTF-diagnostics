# Script to run GFDL grid functions

import numpy as np
import xarray as xr
from nch import * # saved generalized TCH function in python script for readability


def generate_reg_grid(min_lat,max_lat,min_lon, max_lon, tch_size):

    rEarth = 6378.1      # km
    # Define destgrid
    if min_lon > max_lon:
        # Wrap around prime meridian.
        if (360-min_lon)%tch_size==0:
            destgrid = xr.Dataset({'lat':np.arange(min_lat,max_lat,tch_size),
            'lon':np.concatenate((np.arange(min_lon, 360, tch_size), np.arange(max_lon,tch_size)))})

        else: 
            # Use modulo to keep correct grid spacing when wrapping around 0 longitude
            destgrid = xr.Dataset({'lat':np.arange(min_lat,max_lat,tch_size),
            'lon':np.concatenate((np.arange(min_lon, 360, tch_size), np.arange(tch_size-((360-min_lon)%tch_size),max_lon,tch_size)))})
    else:
        destgrid = xr.Dataset({'lat':np.arange(min_lat,max_lat,tch_size),'lon':np.arange(min_lon, max_lon,tch_size)})

    ny = destgrid.sizes['lat']
    nx = destgrid.sizes['lon']

    destgrid['mask'] = xr.DataArray(np.ones((ny,nx)),dims=["lat", "lon"],coords={"lat": destgrid.lat, "lon": destgrid.lon})
    destgrid['area'] = xr.DataArray(np.ones((ny,nx)),dims=["lat", "lon"],
                                    coords={"lat": destgrid.lat, "lon": destgrid.lon}) * np.cos(np.deg2rad(destgrid.lat))*rEarth**2
    destgrid['lat'] = destgrid['lat'].assign_attrs({'units':'degrees_north','long_name':'latitude'})
    destgrid['lon'] = destgrid['lon'].assign_attrs({'units':'degrees_east','long_name':'longitude'})

    tmp = destgrid.cf.add_bounds(['lon','lat']).rename({'lat_bounds':'lat_b','lon_bounds':'lon_b'})
    lonb = tmp['lon_b']
    latb = tmp['lat_b']
    dim1 = lonb.dims[0]; dim2 = lonb.dims[1]
    lonb2 = xr.concat([lonb.isel({dim1:0,dim2:0}),lonb.isel({dim2:1})],dim=dim1).drop_vars('lon').swap_dims({'lon':'lon_b'})

    if (max(destgrid['lon'].values)<=180):
        lonb2 = xr.where(lonb2<-180,lonb2+360,lonb2)
        lonb2 = xr.where(lonb2>180,lonb2-360,lonb2)
    else:
        lonb2 = xr.where(lonb2<0,lonb2+360,lonb2)
        lonb2 = xr.where(lonb2>360,lonb2-360,lonb2)

    destgrid['lon_b'] = lonb2.assign_attrs(destgrid['lon'].attrs)

    dim1 = latb.dims[0]; dim2 = latb.dims[1]
    latb2 = xr.concat([latb.isel({dim1:0,dim2:0}),latb.isel({dim2:1})],dim=dim1).drop_vars('lat').swap_dims({'lat':'lat_b'})
    latb2 = xr.where(latb2<-90,-90,latb2)
    latb2 = xr.where(latb2>90,90,latb2)
    destgrid['lat_b'] = latb2.assign_attrs(destgrid['lat'].attrs)

    return destgrid

def generate_global_grid(tch_size):

    rEarth = 6378.1      # km
    destgrid = xr.Dataset({'lat':np.arange(-90,90+tch_size,tch_size),'lon':np.arange(0,360,tch_size)})
    
    ny = destgrid.sizes['lat']
    nx = destgrid.sizes['lon']
    
    destgrid['mask'] = xr.DataArray(np.ones((ny,nx)),dims=["lat", "lon"],coords={"lat": destgrid.lat, "lon": destgrid.lon})
    destgrid['area'] = xr.DataArray(np.ones((ny,nx)),dims=["lat", "lon"],
                                    coords={"lat": destgrid.lat, "lon": destgrid.lon})*np.cos(np.deg2rad(destgrid.lat))*rEarth**2
    destgrid['lat'] = destgrid['lat'].assign_attrs({'units':'degrees_north','long_name':'latitude'})
    destgrid['lon'] = destgrid['lon'].assign_attrs({'units':'degrees_east','long_name':'longitude'})
    
    tmp = destgrid.cf.add_bounds(['lon','lat']).rename({'lat_bounds':'lat_b','lon_bounds':'lon_b'})
    lonb = tmp['lon_b']
    latb = tmp['lat_b']
    dim1 = lonb.dims[0]; dim2 = lonb.dims[1]
    lonb2 = xr.concat([lonb.isel({dim1:0,dim2:0}),lonb.isel({dim2:1})],dim=dim1).drop_vars('lon').swap_dims({'lon':'lon_b'})
    
    if (max(destgrid['lon'].values)<=180):
        lonb2 = xr.where(lonb2<-180,lonb2+360,lonb2)
        lonb2 = xr.where(lonb2>180,lonb2-360,lonb2)
    else:
        lonb2 = xr.where(lonb2<0,lonb2+360,lonb2)
        lonb2 = xr.where(lonb2>360,lonb2-360,lonb2)
    
    destgrid['lon_b'] = lonb2.assign_attrs(destgrid['lon'].attrs)
    
    dim1 = latb.dims[0]; dim2 = latb.dims[1]
    latb2 = xr.concat([latb.isel({dim1:0,dim2:0}),latb.isel({dim2:1})],dim=dim1).drop_vars('lat').swap_dims({'lat':'lat_b'})
    latb2 = xr.where(latb2<-90,-90,latb2)
    latb2 = xr.where(latb2>90,90,latb2)
    destgrid['lat_b'] = latb2.assign_attrs(destgrid['lat'].attrs)

    return destgrid


# # Need to add the following capabiity to regrid to a regular grid. Note the areal_mean fxn is right but need to adapt to
# # putt in standardized latitude and longitude names for non-GFDL models

# def regrid_regions(ds_grid, da_model, ds_obs_cnes, ds_obs_dtu, min_lat, max_lat, min_lon, max_lon):
# # Mask region, with buffer 
#     margin=2


#     #remove areal mean
#     def horizontal_mean_no_wet(da, metrics, lsm):
#         num = (da * metrics['area']).sum(dim=['lon', 'lat'])
#         denom = (metrics['area'].where(lsm)).sum(dim=['lon', 'lat'])
#         return num / denom

#     lsm = ~np.isnan(mod_mdt_rg)


#     return model_mask_reg, cnes_mask_reg.drop('xh').drop('yh'), dtu_mask_reg.drop('xh').drop('yh')
