import numpy as np 
from netCDF4 import Dataset
import glob
import os

def fronts_for_date(latGrid, lonGrid, year, month, day, hour):
    #################### CATHERINE FRONTS ###############
   
    # initilazing output array as zeros
    wf = np.zeros(latGrid.shape)
    cf = np.zeros(latGrid.shape)

    # get list of files in the folder
    c_folder = '/mnt/drive1/processed_data/MERRA2fronts/%04d%02d/'%(year, month)

    # select date
    selectDate = '%04d%02d%02d'%(year, month, day)

    # string to search in the main c_folder (YYYY/MM folder)
    search_string = os.path.join(c_folder, '*%s_%02d*.ncdf'%(selectDate, hour))
    c_files = glob.glob(search_string)
   
    # if no files are found
    if (not c_files):
        print ("Catherine's front file not found.")
        return wf, cf
   
    # if found, then continue with the following code
    # for each file found, read in the lat, lon
    # grid them into a .5 x .625 hist2d to find the location of the fronts
    cf_lon = []
    cf_lat = []
    wf_lat = []
    wf_lon = []

    for c_file in c_files:
      # print (c_file)
      dataset = Dataset(c_file)
      dataset.set_auto_mask(False)
      c_lat = dataset.variables['latitude'][:]
      c_lon = dataset.variables['longitude'][:]
      c_slp = dataset.variables['MERRA2SLP'][:]
      c_info = dataset.variables['storm_info'][:]

      # CF_combined, CF_simmonds850, CF_hewson1km
      c_cf = dataset.variables['CF_combined'][:]
      # c_cf = dataset.variables['CF_simmonds850'][:]
      # c_cf = dataset.variables['CF_hewson1km'][:]
      c_cf_lon = c_cf[:,0]
      c_cf_lat = c_cf[:,1]

      cf_lat.extend(c_cf_lat.tolist())
      cf_lon.extend(c_cf_lon.tolist())

      # WF_Hewson850, WF_Hewson1Km, WF_HewsonWB
      c_wf = dataset.variables['WF_Hewson1km'][:] 
      # c_wf = dataset.variables['WF_Hewson850'][:] 
      c_wf_lon = c_wf[:,0]
      c_wf_lat = c_wf[:,1]
      
      wf_lat.extend(c_wf_lat.tolist())
      wf_lon.extend(c_wf_lon.tolist())

      dataset.close()

    wf_lat = np.asarray(wf_lat)
    wf_lon = np.asarray(wf_lon)
    
    cf_lat = np.asarray(cf_lat)
    cf_lon = np.asarray(cf_lon)

    cf_lon[cf_lon > 180.] = cf_lon[cf_lon > 180] - 360.
    cf_lon[cf_lon < -180.] = cf_lon[cf_lon < -180] + 360.
    
    wf_lon[wf_lon > 180.] = wf_lon[wf_lon > 180] - 360.
    wf_lon[wf_lon < -180.] = wf_lon[wf_lon < -180] + 360.

    invalid_ind = (wf_lat == -999.) | (wf_lon == -999.)
    wf_lat = wf_lat[~invalid_ind]
    wf_lon = wf_lon[~invalid_ind]
    
    invalid_ind = (cf_lat == -999.) | (cf_lon == -999.)
    cf_lat = cf_lat[~invalid_ind]
    cf_lon = cf_lon[~invalid_ind]

    lat_edges = np.asarray(latGrid[:,0])
    lon_edges = np.asarray(lonGrid[0,:])

    lat_div = lat_edges[1] - lat_edges[0]
    lon_div = lon_edges[1] - lon_edges[0]

    lat_edges = lat_edges - lat_div/2.
    lat_edges = np.append(lat_edges, lat_edges[-1]+lat_div)

    lon_edges = lon_edges - lon_div/2.
    lon_edges = np.append(lon_edges, lon_edges[-1]+lon_div)
    
    wf, _, _ = np.histogram2d(wf_lat, wf_lon, bins=(lat_edges, lon_edges))
    wf = np.double(wf > 0)
    
    cf, _, _ = np.histogram2d(cf_lat, cf_lon, bins=(lat_edges, lon_edges))
    cf = np.double(cf > 0)

    return wf, cf, c_slp, c_lat, c_lon, cf_lat, cf_lon, wf_lat, wf_lon
        
