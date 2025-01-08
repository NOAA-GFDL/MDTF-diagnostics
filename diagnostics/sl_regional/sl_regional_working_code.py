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


# Import modules used in the POD
import os
#import matplotlib

#matplotlib.use("Agg")  # non-X windows backend

#import matplotlib.pyplot as plt
#import numpy as np
import intake
import sys
import yaml

print("Libs imported!")

#should be setttings file & runtime config file information

# User-set parameters
tch_size = 3.0     # Size of TCH box in degrees #jason file
cost_threshold = 5.0 # cost --> higher means larger model error relative to data
threshold = 10.0    # Threshold for number of non-nan grid points to perform TCH on that cell
modname = "esm4"    # cm4 or esm4
reg_choice = "all"    # gs or all
#inputdir='/glade/work/clittle/p2521/input/'
#outputdir='/glade/work/clittle/p2521/output/'
#outputdir='./'
#obsdir='obs/'
#modeldir='model/'
# rowstr = ['CNES','DTU',modname]


# Part 1: Read in the model data
# ------------------------------
# Debugging: remove following line in final PR
work_dir = os.environ["WORK_DIR"]
outputdir = f'{work_dir}/model/'
# Receive a dictionary of case information from the framework
print("reading case_info")
# Remove following line final PR
# os.environ["case_env_file"] = os.path.join(work_dir, "case_info.yml")

case_env_file = os.environ["case_env_file"]
assert os.path.isfile(case_env_file), f"case environment file not found"
with open(case_env_file, 'r') as stream:
    try:
        case_info = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

cat_def_file = case_info['CATALOG_FILE']
case_list = case_info['CASE_LIST']
# all cases share variable names and dimension coords in this example, so just get first result for each
zos_var = [case['zos_var'] for case in case_list.values()][0]
time_coord = [case['time_coord'] for case in case_list.values()][0]
lat_coord = [case['lat_coord'] for case in case_list.values()][0]
lon_coord = [case['lon_coord'] for case in case_list.values()][0]
# open the csv file using information provided by the catalog definition file
cat = intake.open_esm_datastore(cat_def_file)
# filter catalog by desired variable and output frequency
zos_subset = cat.search(variable_id=zos_var, frequency="mon")
# examine assets for a specific file
#zos_subset['CMIP.synthetic.day.r1i1p1f1.day.gr.atmos.r1i1p1f1.1980-01-01-1984-12-31'].df
# convert zos_subset catalog to an xarray dataset dict
zos_dict = zos_subset.to_dataset_dict(
    xarray_open_kwargs={"decode_times": True, "use_cftime": True}
)

# Extract the dataset from the dictionary
key = 'CMIP.NOAA-GFDL.GFDL-CM4.historical.mon.r1i1p1f1.Omon.gn.ocean.r1i1p1f1'
dataset = zos_dict[key]

ds_model = dataset.rename_dims({'y':'yh','x':'xh'})
da_model = ds_model.zos.reset_coords(drop=True).drop_vars(['x','y'])

#subset to obs time period


# Compute the time mean
da_model = da_model.mean(dim="time")


#da_model = ds_model

print(ds_model)
print(da_model)

#Read in OBS data
#obs_dir = os.environ["OBS_DATA_ROOT"] #this line does not work 
#reading in the OBS data manually

obs_dir = "/glade/work/netige/mdtf_Nov24/mdtf/inputdata/obs_data/"

ds_obs_cnes = xr.open_dataset(obs_dir+"cnescls22mdt.nc")
productname='CNES22'
ds_obs_cnes=ds_obs_cnes.drop_vars('time')
ds_obs_cnes = ds_obs_cnes.assign_coords(longitude=((360 + (ds_obs_cnes.longitude % 360)) % 360))
ds_obs_cnes = ds_obs_cnes.roll(longitude=int(len(ds_obs_cnes['longitude']) / 2),roll_coords=True)
ds_obs_cnes=ds_obs_cnes.isel(time=0)

ds_obs_dtu = xr.open_dataset(obs_dir+"dtuuh22mdt.nc")

ds_grid = xr.open_dataset(obs_dir+'cm4_grid.nc')

ds_grid=ds_grid[['geolon','geolat','geolon_c','geolat_c','wet','areacello', 'deptho']]
ds_grid=grid_model_sym_approx(ds_grid)

print(ds_grid)

print("Data_imported")

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

#Regridding
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
    try:
        model_flat = model_mask.values.ravel()  # Ensure model_mask is an xarray object or similar
        cnes_flat = ds1_mask.values.ravel()
        dtu_flat = ds2_mask.values.ravel()
        lat_flat = data_grid.lat.values.ravel()
        lon_flat = data_grid.lon.values.ravel()
    except AttributeError as e:
        raise ValueError("Input masks must be xarray objects or arrays with a `.values` attribute.") from e


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