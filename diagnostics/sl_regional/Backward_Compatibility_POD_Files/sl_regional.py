import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
import pandas as pd
import xesmf as xe
from gfdl_grid_fx import grid_model_sym_approx, regrid_regions_gfdl
from other_grid_fx import generate_reg_grid#, regrid_regions_reg
from plot_fx import make_regional_plots
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from nch import compute_error


print("Libs imported!")

#model data
model_dataset = xr.open_dataset('/glade/work/netige/mdtf_Nov24/mdtf/inputdata/mdtf_test_data/cm4/mon/cm4.zos.mon.nc')
zos_data = model_dataset.mdt
model_mean_zos = zos_data.mean

print(model_mean_zos)

# User-set parameters
tch_size = 3.0     # Size of TCH box in degrees #jason file
cost_threshold = 5.0 # cost --> higher means larger model error relative to data
threshold = 10.0    # Threshold for number of non-nan grid points to perform TCH on that cell
modname = "esm4"    # cm4 or esm4
reg_choice = "all"    # gs or all
inputdir='/glade/work/clittle/p2521/input/'
#outputdir='/glade/work/clittle/p2521/output/'
import os
wd = os.getcwd()
outputdir=f'{wd}/model/'
obsdir='obs/'
modeldir='model/'

#read in Model data (based on modname)
match modname:
    case "cm4":
        ds_model = xr.open_dataset(inputdir+modeldir+'cm4_mdt_new.nc')
        ds_grid = xr.open_dataset(inputdir+modeldir+'cm4_grid.nc')
        da_model = ds_model.mdt.reset_coords(drop=True).drop_vars(['xh','yh'])
    case "esm4":
        ds_model = xr.open_dataset(inputdir+modeldir+'esm4_mdt_new.nc')
        ds_model=ds_model.rename_vars({'zos':'mdt'}).rename_dims({'y':'yh','x':'xh'})
        ds_grid = xr.open_dataset(inputdir+modeldir+'ESM4_ocean_static.nc')
        da_model=ds_model.mdt.reset_coords(drop=True).drop_vars(['x','y'])

ds_grid=ds_grid[['geolon','geolat','geolon_c','geolat_c','wet','areacello', 'deptho']]
ds_grid=grid_model_sym_approx(ds_grid)

print(ds_grid)

#read in Obs/Reference Data
ds_obs_cnes = xr.open_dataset(inputdir+obsdir+"cnescls22mdt.nc")
productname='CNES22'
ds_obs_cnes=ds_obs_cnes.drop_vars('time')
ds_obs_cnes = ds_obs_cnes.assign_coords(longitude=((360 + (ds_obs_cnes.longitude % 360)) % 360))
ds_obs_cnes = ds_obs_cnes.roll(longitude=int(len(ds_obs_cnes['longitude']) / 2),roll_coords=True)
ds_obs_cnes=ds_obs_cnes.isel(time=0)

ds_obs_dtu = xr.open_dataset(inputdir+obsdir+"dtuuh22mdt.nc")

print("Data Read in!!")

#Region classification
regnames=['California','Leeuwin','Gulf Stream','Kuroshio','East Australia']
reginfo=pd.DataFrame(regnames,columns=['RegionName'])

##large region
wbound=[360-165.,95,360-95,110,136]
ebound=[360-95.,130,360-50,160,166]
nbound=[65.,-5,55,60,-10]
sbound=[15.,-50,13,15,-52]

proj_lon=[120.,0,25,-110,0]
proj_lat=[70.,90,70,60,90]

reginfo['west_bound']=wbound
reginfo['east_bound']=ebound
reginfo['north_bound']=nbound
reginfo['south_bound']=sbound
reginfo['region_name']=regnames
reginfo['proj_longitude']=proj_lon
reginfo['proj_latitude']=proj_lat

if reg_choice == "gs":
    # reginfo=reginfo.iloc[[2], :]
    reginfo=reginfo.iloc[[3], :]
else:    
    reginfo=reginfo

print("Region Classification Done!!!")

# Regridding

# import warnings
# warnings.filterwarnings( "ignore")#|lat|>90

#regrid model and reference data
model_reg_col = []
cnes_reg_col = []
dtu_reg_col = []

for nreg in np.arange(len(reginfo)):
    # print('starting ' + str(nreg))
    model_reg, cnes_reg, dtu_reg = regrid_regions_gfdl(ds_grid, 
                                                  da_model, 
                                                  ds_obs_cnes, 
                                                  ds_obs_dtu, 
                                                  reginfo.iloc[nreg].south_bound, 
                                                  reginfo.iloc[nreg].north_bound, 
                                                  reginfo.iloc[nreg].west_bound, 
                                                  reginfo.iloc[nreg].east_bound)
    model_reg_col.append(model_reg)
    cnes_reg_col.append(cnes_reg)
    dtu_reg_col.append(dtu_reg)
    print('finished ' + str(nreg)) 

#TCH
def regional_tch(data_grid, model_mask, ds1_mask, ds2_mask, min_lat, max_lat, min_lon, max_lon, tch_size, depth_threshold=None):

    destgrid = generate_reg_grid(min_lat, max_lat, min_lon, max_lon, tch_size)
    
    # Find weights to position of gridpoints in TCH grid
    regrid_to_tch = xe.Regridder(data_grid, destgrid,'conservative', extrap_method=None)
    wts=regrid_to_tch.weights

    # Flatten datasets
    model_flat=model_mask.values.ravel()
    cnes_flat=ds1_mask.values.ravel()
    dtu_flat=ds2_mask.values.ravel()
    lat_flat=data_grid.lat.values.ravel()
    lon_flat=data_grid.lon.values.ravel()

    # Require identical masks on all datasets
    def get_mask(arr):
        mask = [a if np.isnan(a) else 1 for a in arr]
        return np.array(mask)
    model_mask = get_mask(model_flat)
    cnes_mask = get_mask(cnes_flat) 
    conserv_mask = model_mask*cnes_mask
        
    R, err, num_points, cost_func = compute_error(threshold, destgrid, wts, conserv_mask, model_flat, cnes_flat, dtu_flat, num_datasets=3)

    return R, err, num_points, cost_func, destgrid

Rs = []
errs = []
num_pointss = []
cost_funcs = []
tchgrids = []

for nreg in np.arange(len(reginfo)):

    # Efficiently select data
    model_reg = model_reg_col[nreg]
    cnes_reg = cnes_reg_col[nreg]
    dtu_reg = dtu_reg_col[nreg]

    R, err, num_points, cost_func, tchgrid = regional_tch(ds_grid, 
                                                           model_reg,
                                                           cnes_reg,
                                                           dtu_reg,
                                                           reginfo.iloc[nreg].south_bound,
                                                           reginfo.iloc[nreg].north_bound,
                                                           reginfo.iloc[nreg].west_bound,
                                                           reginfo.iloc[nreg].east_bound,
                                                           tch_size)
    print('Done with ' + reginfo.iloc[nreg].RegionName)

    errs.append(err.copy())
    Rs.append(R.copy())
    cost_funcs.append(cost_func.copy())
    num_pointss.append(num_points.copy())
    tchgrids.append(tchgrid.copy())


make_regional_plots(modname,reginfo, ds_grid, tchgrids, model_reg_col, cnes_reg_col, dtu_reg_col, errs, cost_funcs, num_pointss, cost_threshold, outputdir)

print("POD Run Completed, Yay!!!")
