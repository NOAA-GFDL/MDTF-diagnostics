# Import modules
import os
import numpy as np
import xarray as xr

# BINNING/COMPOSITING MODEL DATA #############################################################

#  MATH FUNCTION(S) ############################################


def boxavg(thing, lat, lon):
    coslat_values = np.transpose(np.tile(np.cos(np.deg2rad(lat)), (len(lon), 1)))
    thing1 = thing*coslat_values
    thing2 = thing1/thing1
    average = np.nansum(np.nansum(thing1,0))/np.nansum(np.nansum(coslat_values*thing2,0))

    return average

# Lats/Lons


latres = float(os.getenv("latres"))
lonres = float(os.getenv("lonres"))
lats = np.arange(-5, 5+latres, latres)
lons = np.arange(-5, 5+lonres, lonres)
# Gather the years that were inputted by user
FIRST_YR = np.int(os.getenv("startdate"))
LAST_YR = np.int(os.getenv("enddate"))
ds_all = []

for y in range(FIRST_YR,LAST_YR+1):
    # Open all the yearly snapshot (budget and regular variable) files
    ds_reg = xr.open_dataset(os.environ['WORK_DIR'] + '/model/Model_Regular_Variables_' + str(y) + '.nc')
    ds_budg = xr.open_dataset(os.environ['WORK_DIR']+'/model/Model_Budget_Variables_' + str(y) + '.nc')
    # Merge the budget and regular variable files by year
    ds_merge = xr.merge([ds_reg,ds_budg])
    ds_reg.close()
    ds_budg.close()
    # Get all the merged files together so that once all are collected they can be concatenated
    ds_all.append(ds_merge)
    ds_merge.close()

# Concatenate the year files together so all variables are combined across all storms
data = xr.concat(ds_all, dim='numstorms')

# Get a list of the data variables in data to trim the data after lifetime maximum intensity (LMI)
Model_vars = list(data.keys())

# Grab the vmax variable to get the LMI itself and point of LMI for trimming to account only for intensification period
maxwinds = data['maxwind']
winds_list = []

# Loop through the variables to pick out the feedbacks and add a normalized version of that variable
for var in Model_vars:
    if var[0:5] == 'hanom' or var[0:10] == 'hMoistanom' or var[0:10] == 'hTempanom' or var[0:4] == 'hvar':
        normvar = np.array(data[var])
        boxavrawvar = np.array(data[var])
        boxavvar = np.ones((len(maxwinds),len(maxwinds[0]))) * np.nan
        boxavnormvar = np.ones((len(maxwinds),len(maxwinds[0]))) * np.nan
        for s in range(len(maxwinds)):
            for t in range(len(maxwinds[s])):
                hvar = np.array(data.hvar[s][t][:][:])
                boxavghvar = boxavg(hvar,np.array(data.latitude[s][t][:]), np.array(data.longitude[s][t][:]))
                normvar[s][t][:][:] = normvar[s][t][:][:]/boxavghvar
                boxavvar[s][t] = boxavg(boxavrawvar[s][t][:][:], np.array(data.latitude[s][t][:]),
                                        np.array(data.longitude[s][t][:]))
                boxavnormvar[s][t] = boxavg(np.array(normvar[s][t][:][:]), np.array(data.latitude[s][t][:]),
                                            np.array(data.longitude[s][t][:]))
        data['norm' + var] = (['numstorms', 'numsteps', 'latlen', 'lonlen'], np.array(normvar[:][:][:][:]))
        data['boxav_' + var] = (['numstorms', 'numsteps'], np.array(boxavvar[:][:]))
        data['boxav_norm_' + var] = (['numstorms', 'numsteps'], np.array(boxavnormvar[:][:]))

# Loop through all model storms and find the LMI, then tag each storm with its LMI for binning later
for s in range(len(maxwinds)):
    windmax = float(max(maxwinds[s][:]))
    windmaxindex = np.squeeze(np.where(maxwinds[s] == windmax))
    # Check if there are more than one maximum wind speed
    if windmaxindex.size >= 2:
        windmaxindex = int(windmaxindex[0])
    else:
        windmaxindex = int(np.squeeze(np.where(maxwinds[s] == windmax)))
    # Loop and have all the indices after the timestep of LMI be NaN for all vars
    for var in Model_vars:
        data[var][s, windmaxindex+1:len(maxwinds[s])+1] = np.nan
    
    vmax_indiv_list = []
    for t in range(0, len(maxwinds[s])):
        # First check and NaN all variables at timesteps where TC center is outside 30 N/S
        if data.centerLat[s][t] > 30 or data.centerLat[s][t] < -30:
            for var in Model_vars:
                if data[var].ndim == 2:
                    data[var][s][t] = np.nan
                elif data[var].ndim == 3:
                    data[var][s][t][:] = np.nan
                else:
                    data[var][s][t][:][:] = np.nan
        # Get max wind at specific step to tag the steps for binning snapshot
        vmax_sel = maxwinds[s,t].values
        vmax = xr.full_like(data.h[s, t], float(vmax_sel)).rename('vmax')
        vmax_indiv_list.append(vmax)
    vmax_indiv_array = xr.concat(vmax_indiv_list, dim='numsteps')
    # Create the vmax tag variable
    winds_list.append(vmax_indiv_array)

# Update Model data with the vmax tag created above
model_winds_array = xr.concat(winds_list, dim='numstorms')
model_updated = xr.merge([data, model_winds_array])
# Stretch the boxav variables to 1 dimension and make a new stretched windmax variable
newvars = list(model_updated.keys())
for var in newvars:
    if var[0:5] == 'boxav':
        (model_updated)['new_' + var] = (['newsteps'], np.squeeze(np.reshape(np.array(model_updated[var]),
                                                                            (len(data.numstorms)*len(data.numsteps)))))

model_updated['new_maxwind'] = (['newsteps'], np.squeeze(np.reshape(np.array(model_updated['maxwind']),
                                                                   (len(data.numstorms)*len(data.numsteps)))))

# Bin snapshots according to max wind speed bins
bins = np.arange(0,66,3)
# Set a count array to gather the sample size for each bin and all bins
count_denom = len(data.latitude[0][0]) * len(data.longitude[0][0])
bins_count = np.zeros(len(bins))
vmax2 = model_updated.vmax.copy(deep=True)
onedvmax = model_updated.new_maxwind.copy(deep=True)
for b, bin in enumerate(bins):
    upperbin = bin+3
    # Variable to get the number of samples for the current bin (divide by the resolution dims multiplied together)
    count = (len(np.where((model_updated.vmax>=bin)&(model_updated.vmax<upperbin))[0])/count_denom)
    bins_count[b] = count
    vmax2 = (xr.where((model_updated.vmax>=bin)&(model_updated.vmax<upperbin), b, vmax2))
    onedvmax = (xr.where((model_updated.new_maxwind>=bin)&(model_updated.new_maxwind<upperbin), b, onedvmax))
bin_ds = xr.Dataset(data_vars=dict(bins=(['numstorms', 'numsteps', 'latlen', 'lonlen'], vmax2.values)))
onedbin_ds = xr.Dataset(data_vars=dict(newbins=(['newsteps'], onedvmax.values)))
ds = xr.merge([model_updated, bin_ds, onedbin_ds])
ds = ds.set_coords(['bins'])
ds = ds.set_coords(['newbins'])

# Get the mean of each bin for one composite image
bins = np.arange(0,22,1)
binlabels = np.arange(1.5,66,3)
dsbins = ds['bins'].values
dsnewbins = ds['newbins'].values
binmeans = {}
binboxavstdevs = {}
for var_name, values in ds.items():
    dvar = ds[var_name].values
    if len(np.shape(dvar)) == 4:
        avg_bin_list = []
        for b, bin in enumerate(bins):
            avg_bin_list.append(np.nanmean(np.where(dsbins == bin, np.array(dvar), np.nan), axis=(0, 1)))
        binmeans[var_name] = (['bin', 'lat', 'lon'], avg_bin_list)
    if len(np.shape(dvar)) == 1:
        avg_bin_list = []
        stdev_bin_list = []
        for b, bin in enumerate(bins):
            avg_bin_list.append(np.nanmean(np.where(dsnewbins == bin, np.array(var), np.nan), axis=(0)))
            stdev_bin_list.append(np.nanstd(np.where(dsnewbins == bin, np.array(dvar), np.nan), axis=(0)))
        binmeans[var_name] = (['bin'], avg_bin_list)
        binboxavstdevs[var_name] = (['bin'], stdev_bin_list)

# Bin means
binmeans['bin'] = (['bin'], binlabels)
binmeans['lat'] = (['lat'], lats)
binmeans['lon'] = (['lon'], lons)
binmeans['bincounts'] = ('bin', bins_count)
# Add relevant raw variables that have not been binned or composited
binmeans['maxwind'] = (['numstorms', 'numsteps'], np.array(data['maxwind']))
binmeans['minSLP'] = (['numstorms', 'numsteps'], np.array(data['minSLP']))

# Binned boxav stdevs
binboxavstdevs['bin'] = (['bin'], binlabels)
binboxavstdevs['bincounts'] = ('bin', bins_count)

modelbinavgdata = xr.Dataset(data_vars=binmeans, attrs={'description': 'Mean Binned Data'})
modelbinboxavstdevdata = xr.Dataset(data_vars=binboxavstdevs,
                                    attrs={'description': 'Standard Deviations of Binned Box Averaged Variables'})

modelbinavgdata.to_netcdf(os.environ['WORK_DIR'] + '/model/Model_Binned_Composites.nc')
modelbinboxavstdevdata.to_netcdf(os.environ['WORK_DIR'] + '/model/Model_Binned_STDEVS_of_BoxAvgs.nc')
