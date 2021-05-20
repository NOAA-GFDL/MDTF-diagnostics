import xarray as xr

file_path = None
output_path = None

#United States BB provided; replace with region of interest
#lon in range -180,180
nla=71.36
sla=18.91
wlo=-171.79
elo=-66.96
ds = xr.open_dataset(file_path, decode_times=False)

#the diagnostic assumes your grid has a longitudinal range -180,180
#Shift your grid from 0,360 using the following lines
ds.coords['lon'] = (ds.coords['lon'] + 180) % 360 - 180 #shift the values
ds = ds.sortby(ds.lon) #sort them

#in the case your data is not cropped to a
#specific region, this code can be used to select a subset of data within a lat/lon

mask_lon = (ds.lon >= wlo) & (ds.lon <= elo)
mask_lat = (ds.lat >= sla) & (ds.lat <= nla)
cropped_ds = ds.where(mask_lon & mask_lat, drop=True)

cropped_ds.to_netcdf(output_path)
