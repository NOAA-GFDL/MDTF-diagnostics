# Import modules used in the POD
import numpy as np
import xarray as xr
import pandas as pd
import xesmf as xe
import os
import intake
import sys
import yaml

import momlevel
from sparse import COO

from gfdl_grid_fx import regrid_regions_gfdl
from other_grid_fx import generate_reg_grid, generate_global_grid
from plot_fx import make_regional_plots, make_global_plots
from nch import compute_error

print("Libs imported!")

###############################################################
################ Functions for the POD ########################
###############################################################

def chunk_data_grid(data_grid):
    chunk_dict = {"i": -1, "j": -1}

    # Check if the dataset has 'vertex' or 'vertices'
    if "vertex" in data_grid.dims:
        chunk_dict["vertex"] = -1
    elif "vertices" in data_grid.dims:
        chunk_dict["vertices"] = -1

    return data_grid.chunk(chunk_dict)


def regional_tch(data_grid, model_mask, ds1_mask, ds2_mask, min_lat, max_lat, min_lon, max_lon, tch_size, depth_threshold=None):

    destgrid = generate_reg_grid(min_lat, max_lat, min_lon, max_lon, tch_size)

    #data_grid = data_grid.chunk({"i": -1, "j": -1, "vertex": -1})
    #data_grid = chunk_data_grid(data_grid)
 
    # Find weights to position of gridpoints in TCH grid
    regrid_to_tch = xe.Regridder(data_grid, destgrid, 'conservative_normed', extrap_method=None, periodic=True, ignore_degenerate=True)
    wts=regrid_to_tch.weights

    # Flatten datasets
    model_flat=model_mask.values.ravel()
    cnes_flat=ds1_mask.values.ravel()
    dtu_flat=ds2_mask.values.ravel()
    lat_flat=data_grid.latitude.values.ravel()
    lon_flat=data_grid.longitude.values.ravel()

    # Require identical masks on all datasets
    def get_mask(arr):
        mask = [a if np.isnan(a) else 1 for a in arr]
        return np.array(mask)
        
    model_mask = get_mask(model_flat)
    cnes_mask = get_mask(cnes_flat)
    conserv_mask = model_mask*cnes_mask
        
    err, num_points, cost_func = compute_error(threshold, destgrid, wts, conserv_mask, [cnes_flat, dtu_flat], model_flat)

    return err, num_points, cost_func, destgrid

def global_tch(model_regrid, ds1_regrid, ds_regrid):

    destgrid = generate_global_grid(tch_size_global)

    # Find weights to position of gridpoints in TCH grid
    regrid_to_tch = xe.Regridder(model_regrid, destgrid, 'conservative_normed', periodic=True, extrap_method=None)
    wts=regrid_to_tch.weights
    lon2d,lat2d=np.meshgrid(model_regrid.lon, model_regrid.lat)
    
    # # Flattened MDT, lat, lon
    model_flat=model_regrid.values.ravel()
    cnes_flat=cnes_mdt_rg.mdt.values.ravel()
    dtu_flat= dtu_mdt_rg.mdt.values.ravel()
    lat_flat=lat2d.ravel()
    lon_flat=lon2d.ravel()

    # Get mask for locations over land
    def get_mask(arr):
        mask = [a if np.isnan(a) else 1 for a in arr]
        return np.array(mask)
    model_mask = get_mask(model_flat)
    conserv_mask = model_mask

    err, num_points, cost_func = compute_error(threshold, destgrid,  wts, conserv_mask, [cnes_flat, dtu_flat], model_flat)

    return err, num_points, cost_func, destgrid


def get_model_GFDL(ds, tgcsvin):
    """ 
    Takes in a model and a grid (e.g. da_model_cm4 and ds_grid), plus a csv of tide gauge locations.
    Return an xarray of model at locations nearest to the tide gaue with an ocean mask applied,
    as well as the depth at those points. (Workd for GFDL models)
    """

    omask = xr.where(np.isnan(ds.zos), np.nan, 1)
    # Get grid points nearest tide gauge locations.
    tgs_xr = momlevel.extract_tidegauge(ds.zos, ds.longitude, ds.latitude, mask=omask, csv=tgcsvin)

    # Check distance between model gridpoint and tide gauge location.
    proximity = [tgs_xr[tg].attrs['distance'] for tg in tgs_xr]
    
    # Get depth at tide gauge locations.
    # da = ds.deptho
    # tgs_depth = momlevel.extract_tidegauge(ds.deptho, ds.longitude, ds_grid.latitude, mask=omask, csv=tgcsvin)

    return tgs_xr.to_array(), proximity


def get_data(ds_obs, tgcsvin):
    """ 
    Like get_model()
    Takes in observed data (like ds_obs_cnes).
    Get data at nearest location to tide gauges, with an ocean mask applied.
    Return data as xarray and error as xarray.
    """
    # Create ocean mask.
    omask = xr.where(np.isnan(ds_obs.mdt), np.nan, 1)
    # Find data points closes to tide gauge locations.
    # print(tgcsvin)
    tgs_xr = momlevel.extract_tidegauge(ds_obs.mdt, ds_obs.longitude, ds_obs.latitude, mask=omask, csv=tgcsvin)

    # Check distance between data gridpoint and tide gauge location.
    proximity = [tgs_xr[tg].attrs['distance'] for tg in tgs_xr]

    # Get data error estimates at locations closest to tide gauges.
    tgs_err=momlevel.extract_tidegauge(ds_obs.err_mdt, ds_obs.longitude, ds_obs.latitude, mask=omask, csv=tgcsvin)

    #return tgs_xr
    return tgs_xr.to_array(), tgs_err.to_array(), proximity


def coastal_tch(destgrid, ds_array):
    ''' 
    Generalized NCH that uses only points along the coast for specified region. 
    Must pass in a flat array of coastal points only.
    Note coastal NCH uses just a single NCH box.
    '''
    n_datasets = len(ds_array)
    ds1_flat = ds_array[0]
    ds2_flat = ds_array[1]
    ds3_flat = ds_array[2]

    # Create weights array for coast where all points have weight of 1 (all are inside the single NCH box).
    wt_arr = COO.from_numpy(np.ones((len(ds1_flat), len(ds1_flat))))
    wts = xr.DataArray(data = wt_arr)    

    if n_datasets==4:
        ds4_flat = ds_array[3]
        err, _, cost_func = compute_error(1, destgrid, wts, [1 for i in  ds1_flat],  
                                         [ds1_flat, ds2_flat, ds4_flat], ds3_flat)
    else:
        err, _, cost_func = compute_error(1, destgrid, wts, [1 for i in  ds1_flat],  
                                            [ds1_flat, ds2_flat], ds3_flat)
    return err, cost_func


def coastal_tch_calc(reginfo, nreg):# Add columns to hold TCH results
    region  = reginfo.iloc[nreg]['RegionName']
    psmsl_region = reginfo.iloc[nreg]['psmsl']
    ###########################################################################
    #                    Create csvs for momlevel
    ###########################################################################
    if psmsl_region:
        match region:
            case 'California':
                tglist=['1457', '256', '2126', '1352', '1394', '378', '1196', '1354',
                '165', '1071', '167']
            case 'Leeuwin':
                tglist=['189', '1549', '1762', '1115', '1031',
                    '111', '834', '957']
            case 'Kuroshio':
                tglist=['1142', '1320', '1089', '1191', '635', '674',
                    '679', '518']
            case 'Gulf Stream':
                tglist=['1246', '825', '2073', '822', '310', '2313', '2320', '831',
                '833', '2315']  
            case 'East Australia':
                tglist=['1246', '825', '2073', '822', '310', '2313', '2320', '831',
                '833', '2315']
            case _:
                print('Could not find a case in first search! Region is ', region)

        # Read in tide gauge locations.
        tgs_in = pd.read_csv(obs_dir+'PSMSL_ids.csv').T
        # Rename columns in dataframe.
        tgs_in.rename(columns = {0: 'lat', 1: 'lon', 2: 'name', 3: 'coast'}, inplace = True)
        # Order points by coast ID# and latitude.
        tgs_in['coast'] = tgs_in['coast'].str.zfill(3)
        tgs_in.lat, tgs_in.lon = tgs_in.lat.astype(float), tgs_in.lon.astype(float)
        tgs_in = tgs_in.sort_values(['coast','lat'],axis=0,ascending=[True,True])
        # Grab only the tide gauge info for the appropriate region. 
        tgs_in = tgs_in.T[tglist].T
        tg_lat, tg_lon = tgs_in['lat'].values, tgs_in['lon'].values
        # Save to CSV for momlevel to read in. 
        tgs_in.to_csv(f"tg_locs_{region}.csv")
        tg = None

    else:

        match region:

            case 'Gulf Stream':
                tg = np.genfromtxt(obs_dir+"Higginson2015.txt", dtype=None)
                tg_lat = tg[:,0]
                tg_lon = tg[:,1]
                tg = np.delete(tg, 15, axis=1)
                df = pd.DataFrame(tg[:,0:2])
                df.columns = ['lat','lon']
                df.index.name = 'name'
                df.to_csv("higg_tg_locs.csv")
                tg_mean = np.mean(tg[:,10:],axis=1) - np.mean(np.mean(tg[:,10:],axis=1))

            case 'Norway':
                tg = np.genfromtxt(obs_dir+"idzanovic.csv", dtype=float, skip_header=1, delimiter=',')
                # Remove first three tide gauges as there is no sufficiently close gridpoint for altimetry and/or model
                tg = np.delete(tg, [0,1,2], axis=0)
                tg_lat = tg[:,0]
                tg_lon = tg[:,1]
                df = pd.DataFrame(tg[:,0:2])
                df.columns = ['lon', 'lat']
                df.index.name = 'name'
                df.to_csv("idzanovic_tg_locs.csv")
                tg_mean = np.mean(tg[:,2:]/1e2,axis=1)-np.mean(np.mean(tg[:,2:]/1e2,axis=1))

    if psmsl_region:
        tgcsvin = f"./tg_locs_{region}.csv"
    else:
        match region:
            case 'Gulf Stream':
                tgcsvin="./higg_tg_locs.csv"
            case 'Norway':
                tgcsvin="./idzanovic_tg_locs.csv"
            case _:
                print('Could not find a case in second search! Region is ', region)

    tgs_mod_xr, mod_proximity   = get_model_GFDL(da_model, tgcsvin=tgcsvin)
    tgs_cnes_xr, tgs_cnes_err, cnes_proximity = get_data(ds_obs_cnes, tgcsvin)
    tgs_dtu_xr, tgs_dtu_err, dtu_proximity = get_data(ds_obs_dtu, tgcsvin)


    ########################################################
    #                       Compute TCH
    ########################################################
    # Flatten datasets and subtract mean. 
    data_flat = {modname: tgs_mod_xr.values - tgs_mod_xr.values.mean(),
                'DTU':  tgs_dtu_xr.values - tgs_dtu_xr.values.mean(),
                'CNES': tgs_cnes_xr.values - tgs_cnes_xr.values.mean()}

    if psmsl_region:
        tg_mean = None
    else:
        # Add tide gauge data is applicable (tg_mean is already flat).
        data_flat['TG'] = tg_mean
        
    destgrid = xr.Dataset({'lat':np.array([np.mean(tg_lat)]), 'lon':np.array([np.mean(tg_lon)])})    
    
    if reginfo.iloc[nreg]['ds4']!=None: 
        err_ac, cost_func_ac = coastal_tch(destgrid, [data_flat[reginfo.iloc[nreg]['ds1']], data_flat[reginfo.iloc[nreg]['ds2']], data_flat[reginfo.iloc[nreg]['ds3']], data_flat[reginfo.iloc[nreg]['ds4']]])
    else:
        err_ac, cost_func_ac = coastal_tch(destgrid, [data_flat[reginfo.iloc[nreg]['ds1']], data_flat[reginfo.iloc[nreg]['ds2']], data_flat[reginfo.iloc[nreg]['ds3']]])


    return tg_lat, tg_lon, tgs_dtu_err, tgs_cnes_err, err_ac, data_flat


print("Functions Defined!")
###############################################################
#################### End of Functions #########################
###############################################################


# Section 1: Set parameters
# -------------------------

reg_choice = os.environ['reg_choice']
modname = os.environ['modname']
threshold = float(os.environ['threshold'])
tch_size = float(os.environ['tch_size'])
rez = float(os.environ['rez'])
cost_threshold = float(os.environ['cost_threshold'])

print("Parameters Set!")


# Section 2: Read in the model data
# ---------------------------------

work_dir = os.environ["WORK_DIR"]
outputdir = f'{work_dir}/model/'

print("reading case_info")

# Receive a dictionary of case information from the framework
                                
case_env_file = os.environ["case_env_file"]
assert os.path.isfile(case_env_file), f"case environment file not found"
with open(case_env_file, 'r') as stream:
    try:
        case_info = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

cat_def_file = case_info['CATALOG_FILE']
case_list    = case_info['CASE_LIST']

# all cases share variable names and dimension coords in this example, so just get first result for each
zos_var    = [case['zos_var']    for case in case_list.values()][0]
time_coord = [case['time_coord'] for case in case_list.values()][0]
lat_coord  = [case['lat_coord']  for case in case_list.values()][0]
lon_coord  = [case['lon_coord']  for case in case_list.values()][0]

# open the csv file using information provided by the catalog definition file
cat        = intake.open_esm_datastore(cat_def_file)

# filter catalog by desired variable and output frequency
zos_subset = cat.search(variable_id=zos_var, frequency="mon")      

# convert zos_subset catalog to an xarray dataset dict
zos_dict   = zos_subset.to_dataset_dict(
    xarray_open_kwargs={"decode_times": True, 
                        "use_cftime": True}
)

# Extract the dataset from the dictionary
print("Available s:", list(zos_dict.keys()))
dataset = zos_dict[list(zos_dict)[0]]

print(dataset)

if modname == "cm4" or modname == "esm4":
    ds_model = dataset.rename({'y':'j', 'x':'i','lat':'latitude', 'lon':'longitude'}).drop('bnds')
else:
    ds_model = dataset

da_model = ds_model

#subset to obs time period
da_model   = da_model.sel(time=slice("1993-01-16", 
                                     "2012-12-16"))
# Compute the time mean
da_model   = da_model.mean(dim="time").load()

print("Model data imported")

# Section 3: Read in the obs data & ancillary data
# ------------------------------------------------

#obs_dir = os.environ["OBS_DATA_ROOT"] 

obs_dir = os.environ["OBS_DATA"] + "/"

#Read in CNES and DTU data

ds_obs_cnes       = xr.open_dataset(obs_dir+"cnescls22mdt.nc")
productname       = 'CNES22'
ds_obs_cnes       = ds_obs_cnes.drop_vars('time')
ds_obs_cnes       = ds_obs_cnes.assign_coords(longitude
                                              =((360 + (ds_obs_cnes.longitude % 360)) % 360))
ds_obs_cnes       = ds_obs_cnes.roll(longitude
                                     =int(len(ds_obs_cnes['longitude']) / 2),
                                     roll_coords=True)
ds_obs_cnes       = ds_obs_cnes.isel(time=0)

ds_obs_dtu        = xr.open_dataset(obs_dir+"dtuuh22mdt.nc")

#Read in Bathymetry data

bathy             = np.load(obs_dir+'GEBCO_1_12.npy')

bathy_lat         = np.arange(-90,90+1/12,1/12)
bathy_lon         = np.arange(-180,180,1/12)

ds_bathy          = xr.Dataset(data_vars=dict(depth=(["lat", "lon"], bathy)), 
                               coords=dict(lat=("lat", bathy_lat), 
                                           lon=("lon", bathy_lon)),
                               attrs=dict(description="GEBCO bathymetry (depth below geoid) data")                      
)

# Load DTU and CNES files regridded onto 0.5 or 1 degree grid. 
# Assign the appropriate TCH size and threshold for number of points in the cell
match rez:
    case 0.5:
        tch_size_global = 3   # size of TCH box in degrees
        dtu_mdt_rg      = xr.open_dataset(obs_dir+'dtu_mdt_p5deg.nc')
        cnes_mdt_rg     = xr.open_dataset(obs_dir+'cnes_mdt_p5deg.nc')
    case 1:
        dtu_mdt_rg      = xr.open_dataset(obs_dir+'dtu_mdt_1deg.nc')
        cnes_mdt_rg     = xr.open_dataset(obs_dir+'cnes_mdt_1deg.nc')
        tch_size_global = 6   # size of TCH box in degrees


# Section 4: Setting up regions
# -----------------------------

# Bounds for region of interest.
wbound  =  [360-165.,95,360-95,110,136,5]
ebound  =  [360-95.,130,360-50,160,166,30]
nbound  =  [65.,-5,55,60,-10,75]
sbound  =  [15.,-50,13,15,-52,55]

# Longitudes and latitudes for plot projection
proj_lon = [120.,0,25,-110,0,270]
proj_lat = [70.,90,70,60,90,85]

# Set up data frame to hold region information (will use for both regional and coastal PODS)
regnames = ['California',
            'Leeuwin',
            'Gulf Stream',
            'Kuroshio',
            'East Australia', 
            'Norway']

reginfo  = pd.DataFrame(regnames, columns = ['RegionName'])

reginfo['west_bound']     = wbound
reginfo['east_bound']     = ebound
reginfo['north_bound']    = nbound
reginfo['south_bound']    = sbound
reginfo['region_name']    = regnames
reginfo['proj_longitude'] = proj_lon
reginfo['proj_latitude']  = proj_lat

reginfo['psmsl'] =  False
reginfo['ds1']   =  'DTU'
reginfo['ds2']   =  'CNES'
reginfo['ds3']   =  modname
reginfo['ds4']   =  None

reginfo['ds1_error'], reginfo['ds1_cost'] = None, None
reginfo['ds2_error'], reginfo['ds2_cost'] = None, None
reginfo['ds3_error'], reginfo['ds3_cost'] = None, None
reginfo['ds4_error'], reginfo['ds4_cost'] = None, None

# Set datasets and need to grab tide gauge locations from PSMSL for coastal POD.
# For regions where we have tide gauge MDT data, do not need to grab PSMSL tide gauge locations.
for index, row in reginfo.iterrows():
    regname = row['RegionName']
    if regname in ['California', 'Leeuwin', 'Kuroshio', 'East Australia']:
        reginfo.loc[index, 'psmsl'] = True
    else:
        reginfo.loc[index, 'psmsl'] = False
        reginfo.loc[index,'ds4'] = 'TG'

if reg_choice == "gs":
    reginfo=reginfo.iloc[[2], :]
else:    
    reginfo=reginfo


# Section 5: Regional & Coastal NCH
# ---------------------------------

# Regrid to model grid on regional domain

model_reg_col = []
cnes_reg_col = []
dtu_reg_col = []

# Regrid model and reference data.

for nreg in np.arange(len(reginfo)):
    model_reg, cnes_reg, dtu_reg = regrid_regions_gfdl(da_model, 
                                              ds_obs_cnes, 
                                              ds_obs_dtu, 
                                              reginfo.iloc[nreg].south_bound, 
                                              reginfo.iloc[nreg].north_bound, 
                                              reginfo.iloc[nreg].west_bound, 
                                              reginfo.iloc[nreg].east_bound)
    model_reg_col.append(model_reg)
    cnes_reg_col.append(cnes_reg)
    dtu_reg_col.append(dtu_reg)
    print('finished ' + reginfo.iloc[nreg].RegionName)

# TCH error estimate for each region

Rs            = []
errs          = []
num_pointss   = []
cost_funcs    = []
tchgrids      = []
tg_lats       = []
tg_lons       = []
tgs_dtu_errs  = []
tgs_cnes_errs = []
err_acs       = []
data_flats    = []

for nreg in np.arange(len(reginfo)):
    
    # Efficiently select data.
    model_reg = model_reg_col[nreg]
    cnes_reg  = cnes_reg_col[nreg]
    dtu_reg   = dtu_reg_col[nreg]

    # Returned arrays have shape [cnes, dtu, model, optional: third dataset]
    err_, num_points_, cost_func_, tchgrid_ = regional_tch(da_model, 
                                                           model_reg,
                                                           cnes_reg,
                                                           dtu_reg,
                                                           reginfo.iloc[nreg].south_bound,
                                                           reginfo.iloc[nreg].north_bound,
                                                           reginfo.iloc[nreg].west_bound,
                                                           reginfo.iloc[nreg].east_bound,
                                                           tch_size)

    #return tg information from alongcoast
    tg_lat, tg_lon, tgs_dtu_err, tgs_cnes_err, err_ac, data_flat = coastal_tch_calc(reginfo,nreg)
    
    errs.append(err_.copy())
    cost_funcs.append(cost_func_.copy())
    num_pointss.append(num_points_.copy())
    tchgrids.append(tchgrid_.copy())
    
    tg_lats.append(tg_lat.copy())
    tg_lons.append(tg_lon.copy())
    tgs_dtu_errs.append(tgs_dtu_err.copy())
    tgs_cnes_errs.append(tgs_cnes_err.copy())
    err_acs.append(err_ac.copy())    
    data_flats.append(data_flat.copy())

    print('Done with ' + reginfo.iloc[nreg].RegionName)

make_regional_plots(modname,
                    reginfo, 
                    da_model, 
                    tchgrids, 
                    model_reg_col, 
                    cnes_reg_col, 
                    dtu_reg_col,
                    errs, 
                    cost_funcs, 
                    num_pointss, 
                    cost_threshold, 
                    outputdir, 
                    tg_lats, 
                    tg_lons, 
                    tgs_dtu_errs, 
                    tgs_cnes_errs, 
                    err_acs, 
                    data_flats, 
                    ds_bathy=ds_bathy)

print("Regional POD completed successfully")

# Section 6: Global TCH
# ---------------------


def horizontal_mean_no_wet(da, metrics, lsm):
    """ 
    Compute mean with only ocean points. 
    """

    num   = (da * metrics['area']).sum(dim=['lon', 'lat'])
    denom = (metrics['area'].where(lsm)).sum(dim=['lon', 'lat'])
    
    return num / denom

#da_model = da_model.chunk({"i": -1, "j": -1, "vertex": -1})
#da_model = chunk_data_grid(da_model)


# Get conversion between model grid (ds_grid) and regular data grid (dtu_mdt_rg)
regrid_mod = xe.Regridder(da_model, 
                          dtu_mdt_rg, 
                          "conservative_normed", 
                          extrap_method=None, 
                          periodic=True, 
                          ignore_degenerate=True)

# Regrid model onto the 0.5 or 1 degree regular grid.
mod_mdt_rg = regrid_mod(da_model.zos) 

# Mask model where data is masked.
mod_mdt_rg = mod_mdt_rg.where(
    ~np.isnan(mod_mdt_rg)).where(
    ~np.isnan(cnes_mdt_rg.mdt))

# Get points that are not on land (therefore not nan).
lsm      = ~np.isnan(mod_mdt_rg)
gm_model = horizontal_mean_no_wet(mod_mdt_rg, 
                                  dtu_mdt_rg, 
                                  lsm)

# Get model mean.
mod_mdt_rg = mod_mdt_rg-gm_model.values

err, num_points, cost_func, destgrid = global_tch(mod_mdt_rg, 
                                                  cnes_mdt_rg, 
                                                  dtu_mdt_rg)

data_dict = {modname:mod_mdt_rg, 
             'CNES':cnes_mdt_rg, 
             'DTU':dtu_mdt_rg}

make_global_plots(data_dict, 
                  err, 
                  cost_func, 
                  destgrid, 
                  num_points, 
                  cost_threshold, 
                  modname, 
                  outputdir)


# Section 7: Close the catalog files and
# release variable dict reference for garbage collection
# ------------------------------------------------------
cat.close()
zos_dict = None


# Sectionn 8: Confirm POD executed successfully
# ---------------------------------------------
print("Last log message by MDSL POD: Finished successfully !!!")
sys.exit(0)
