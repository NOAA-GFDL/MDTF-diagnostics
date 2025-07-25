# Script to run GFDL grid functions

import numpy as np
import xarray as xr
import xesmf as xe
# from nch import * # saved generalized TCH function in python script for readability


# def maskmodel(ds_grid, da, min_lat, max_lat, min_lon, max_lon):
        
#     da=da.where(ds_grid.lat < max_lat)
#     da=da.where(ds_grid.lat > min_lat)
#     if max_lon > 60:
#         max_lon = max_lon - 360
#     if min_lon > 60:
#         min_lon = min_lon - 360
#     da=da.where(ds_grid.lon < max_lon)
#     da=da.where(ds_grid.lon > min_lon)

#     return da

def cutdomain(ds, margin, min_lat, max_lat, min_lon, max_lon):

    ds=ds.where(ds.latitude<max_lat+margin,drop=True)
    ds=ds.where(ds.latitude>min_lat-margin,drop=True)
    ds=ds.where(ds.longitude<max_lon+margin,drop=True)
    ds=ds.where(ds.longitude>min_lon-margin,drop=True)

    return ds

# def grid_model_sym_approx(ds):
    
#     grid_model = xr.Dataset()
#     grid_model['lon'] = ds['geolon']
#     grid_model['lat'] = ds['geolat']

#     grid_model['areacello'] = ds['areacello']
#     grid_model['deptho'] = ds['deptho']
    
#     ny, nx = grid_model['lon'].shape
    
#     lon_b = np.empty((ny+1, nx+1))
#     lat_b = np.empty((ny+1, nx+1))
#     lon_b[1:, 1:] = ds['geolon_c'].values
#     lat_b[1:, 1:] = ds['geolat_c'].values
    
#     # periodicity
#     lon_b[:, 0] = 360 - lon_b[:, -1]
#     lat_b[:, 0] = lat_b[:, -1]
    
#     # south edge
#     dy = (lat_b[2,:] - lat_b[1,:]).mean()
#     lat_b[0, 1:] = lat_b[1,1:] - dy
#     lon_b[0, 1:] = lon_b[1, 1:]
    
#     # corner point
#     lon_b[0, 0] = lon_b[1,0]
#     lat_b[0,0] = lat_b[0,1]
    
#     grid_model['lon_bnds'] = xr.DataArray(data=lon_b, dims=('yq','xq'))
#     grid_model['lat_bnds'] = xr.DataArray(data=lat_b, dims=('yq','xq'))
    
#     return grid_model

def chunk_data_grid(data_grid):
    chunk_dict = {"i": -1, "j": -1}

    # Check if the dataset has 'vertex' or 'vertices'
    if "vertex" in data_grid.dims:
        chunk_dict["vertex"] = -1
    elif "vertices" in data_grid.dims:
        chunk_dict["vertices"] = -1

    return data_grid.chunk(chunk_dict)

def regrid_regions_gfdl(da_model, ds_obs_cnes, ds_obs_dtu, min_lat, max_lat, min_lon, max_lon):
    # Mask region, with buffer 
    margin=2

    #da_model = da_model.chunk({"i": -1, "j": -1, "vertex": -1})
    #da_model = chunk_data_grid(da_model)

    
    ds_obs_cnes = cutdomain(ds_obs_cnes, margin, min_lat, max_lat, min_lon, max_lon)
    ds_obs_dtu = cutdomain(ds_obs_dtu, margin, min_lat, max_lat, min_lon, max_lon)
    #ds_bathy=cutdomain(ds_bathy, margin)
    
    regrid_cnes = xe.Regridder(ds_obs_cnes, da_model, "conservative_normed", extrap_method=None, periodic=True, ignore_degenerate=True)
    cnes_mdt = regrid_cnes(ds_obs_cnes.mdt,skipna=True, na_thres=1) 
    
    regrid_dtu = xe.Regridder(ds_obs_dtu, da_model, "conservative_normed", extrap_method=None, periodic=True, ignore_degenerate=True)
    dtu_mdt = regrid_dtu(ds_obs_dtu.mdt,skipna=True, na_thres=1) 

    area = xe.util.cell_area(da_model,6378)*1000*1000
    omask = xr.where(np.isnan(dtu_mdt), 0, 1)
    model_mdt=da_model.zos*xr.where(np.isnan(dtu_mdt), np.nan, 1)
    
    def horizontal_mean_no_wet(da, area, lsm):
    
        # num = (da * area).sum(dim=['x', 'y'])
        # denom = (area.where(lsm)).sum(dim=['x', 'y'])
        num = (da * area).sum(dim=['i', 'j'])
        denom = (area.where(lsm)).sum(dim=['i', 'j'])
        
        return num / denom
    
    gm_model = horizontal_mean_no_wet(model_mdt, area, omask)
    gm_cnes = horizontal_mean_no_wet(cnes_mdt, area, omask)
    gm_dtu = horizontal_mean_no_wet(dtu_mdt, area, omask)
    
    dtu_mask_reg = dtu_mdt-gm_dtu
    cnes_mask_reg = cnes_mdt-gm_cnes
    model_mask_reg = model_mdt-gm_model
    
    return model_mask_reg, cnes_mask_reg, dtu_mask_reg
