# Script to run GFDL grid functions

import numpy as np
# import numpy.matlib
# from scipy import optimize
# from itertools import combinations
# import math
# from tqdm.notebook import tnrange, tqdm
import xarray as xr
import xesmf as xe
from nch import * # saved generalized TCH function in python script for readability



def grid_model_sym_approx(ds):
    
    grid_model = xr.Dataset()
    grid_model['lon'] = ds['geolon']
    grid_model['lat'] = ds['geolat']

    grid_model['areacello'] = ds['areacello']
    grid_model['deptho'] = ds['deptho']
    
    ny, nx = grid_model['lon'].shape
    
    lon_b = np.empty((ny+1, nx+1))
    lat_b = np.empty((ny+1, nx+1))
    lon_b[1:, 1:] = ds['geolon_c'].values
    lat_b[1:, 1:] = ds['geolat_c'].values
    
    # periodicity
    lon_b[:, 0] = 360 - lon_b[:, -1]
    lat_b[:, 0] = lat_b[:, -1]
    
    # south edge
    dy = (lat_b[2,:] - lat_b[1,:]).mean()
    lat_b[0, 1:] = lat_b[1,1:] - dy
    lon_b[0, 1:] = lon_b[1, 1:]
    
    # corner point
    lon_b[0, 0] = lon_b[1,0]
    lat_b[0,0] = lat_b[0,1]
    
    grid_model['lon_bnds'] = xr.DataArray(data=lon_b, dims=('yq','xq'))
    grid_model['lat_bnds'] = xr.DataArray(data=lat_b, dims=('yq','xq'))
    
    return grid_model

def regrid_regions_gfdl(ds_grid, da_model, ds_obs_cnes, ds_obs_dtu, min_lat, max_lat, min_lon, max_lon):
# Mask region, with buffer 
    margin=2

    def cutdomain(ds, margin):
        ds=ds.where(ds.latitude<max_lat+margin,drop=True)
        ds=ds.where(ds.latitude>min_lat-margin,drop=True)
        ds=ds.where(ds.longitude<max_lon+margin,drop=True)
        ds=ds.where(ds.longitude>min_lon-margin,drop=True)
        return ds
        
    def maskmodel(ds_grid,da):
    
        da=da.where((ds_grid.lat<max_lat))
        da=da.where((ds_grid.lat>min_lat))
        da=da.where((ds_grid.lon<(max_lon-360)))
        da=da.where((ds_grid.lon>(min_lon-360)))
        
        return da
        
    ds_obs_cnes=cutdomain(ds_obs_cnes, margin)
    ds_obs_dtu=cutdomain(ds_obs_dtu, margin)
    #ds_bathy=cutdomain(ds_bathy, margin)
    
    regrid_cnes_mom = xe.Regridder(ds_obs_cnes, ds_grid, "conservative_normed")
    cnes_mdt_mom = regrid_cnes_mom(ds_obs_cnes.mdt,skipna=True, na_thres=1) 
    cnes_mdt_mom = cnes_mdt_mom
    
    regrid_dtu_mom = xe.Regridder(ds_obs_dtu, ds_grid, "conservative_normed")
    dtu_mdt_mom = regrid_dtu_mom(ds_obs_dtu.mdt,skipna=True, na_thres=1) 
    dtu_mdt_mom = dtu_mdt_mom
    
    #regrid_bathy_mom = xe.Regridder(ds_bathy, ds_grid, "conservative_normed")
    #bathy_depth_mom = regrid_bathy_mom(-ds_bathy.depth,skipna=True, na_thres=1) 
    #bathy_depth_mom = bathy_depth_mom
    ## add bathymetry mask here!
    
    # Force identical Masks!
    
    regmask=maskmodel(ds_grid,da_model*0+1)
    dtu_mask_reg=regmask*dtu_mdt_mom
    cnes_mask_reg=regmask*cnes_mdt_mom
    model_mask_reg=regmask*da_model
    
    #remove areal mean
    def horizontal_mean_no_wet(da, metrics, lsm):
        num = (da * metrics['areacello']).sum(dim=['xh', 'yh'])
        denom = (metrics['areacello'].where(lsm)).sum(dim=['xh', 'yh'])
        return num / denom
    
    lsm = ~np.isnan(model_mask_reg)
    gm_model=horizontal_mean_no_wet(model_mask_reg, ds_grid, lsm)
    gm_cnes=horizontal_mean_no_wet(cnes_mask_reg, ds_grid, lsm)
    gm_dtu=horizontal_mean_no_wet(dtu_mask_reg, ds_grid, lsm)
    
    dtu_mask_reg=dtu_mask_reg-gm_dtu
    cnes_mask_reg=cnes_mask_reg-gm_cnes
    model_mask_reg=model_mask_reg-gm_model
    
    return model_mask_reg, cnes_mask_reg.drop('xh').drop('yh'), dtu_mask_reg.drop('xh').drop('yh')