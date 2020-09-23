import numpy as np 
import scipy.io as sio
import cartopy
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import defines
import os

def hist_2d(lon, lat, val=None, bins=None):
  ''' 
  Given lat/lon values, we create a 2d histogram global map. 
  '''

  if (bins is None): 
    # creating my bins
    lat_div = 5.
    lon_div = 5.
    bins = (np.arange(-180, 180+lon_div, lon_div), np.arange(-90, 90+lat_div, lat_div))

  # convert lat and lon into 2d array
  lat = np.array(lat).flatten()
  lon = np.array(lon).flatten()
  lon[lon >= 180.] -= 360. 
  
  # make sure the lens equal each other
  assert(len(lat) == len(lon))
  if (val is not None): 
    val = np.array(val).flatten()
    assert(len(lon) == len(val))

  # bins for the latitude and longitude
  lon_bins = bins[0]
  lat_bins = bins[1]
  lon_mids = lon_bins[:-1] + (lon_bins[1] - lon_bins[0])/2.
  lat_mids = lat_bins[:-1] + (lat_bins[1] - lat_bins[0])/2.

  H_cnts, x, y = np.histogram2d(lon, lat, bins=bins)
  if (val is None): 
    H_sums = H_cnts
  else:
    H_sums, x, y = np.histogram2d(lon, lat, bins=bins, weights=val)

  return {'cnts': H_cnts.T, 'sums': H_sums.T, 'lon': lon_mids, 'lat': lat_mids}

def global_map(ax=None):
  '''Create a global map for plotting the figures.'''
  if (ax is None):
    plt.style.use('seaborn-talk')
    ax = plt.axes(projection=cartopy.crs.PlateCarree())
  else:
    ax.coastlines(lw=1.)
    ax.set_extent([-180, 180, -90, 90])
    gl = ax.gridlines(crs=cartopy.crs.PlateCarree(), draw_labels=True, lw=2., color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    gl.xlocator = mticker.FixedLocator([-180, -90, 0, 90, 180])
    gl.ylocator = mticker.FixedLocator([-90, -45, 0, 45, 90])
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

  return ax

def read_tracks(year): 
  '''Reading in tracks for a given year'''
  in_file = os.path.join(defines.read_folder, f'{defines.model}_{year}.mat')
  tracks = sio.loadmat(in_file)
  return tracks['cyc'][0]

def plot_2d(ax, x, y, z): 
  cf = ax.contourf(x, y, z)
  cf = ax.colorbar(cax=cax)

def get_data(tracks):

  g_lat = []
  g_lon = []
  g_slp = []
  l_lat = []
  l_lon = []
  l_slp = []
  lat = []
  lon = []
  slp = []
  for track in tracks:

    # lysiss
    l_lat.append(track['fulllat'][0][0])
    l_lon.append(track['fulllon'][0][0])
    l_slp.append(track['fullslp'][0][0])
    
    # genesis
    g_lat.append(track['fulllat'][0][-1])
    g_lon.append(track['fulllon'][0][-1])
    g_slp.append(track['fullslp'][0][-1])
    
    # all
    lat.extend(track['fulllat'][0].tolist())
    lon.extend(track['fulllon'][0].tolist())
    slp.extend(track['fullslp'][0].tolist())

  return {'genesis': {'lat': g_lat, 'lon': g_lon, 'slp': g_slp}, \
      'lysis': {'lat': l_lat, 'lon': l_lon, 'slp': l_slp}, \
      'all': {'lat': lat, 'lon': lon, 'slp': slp}}

def track_density_2d(lon, lat, ax=None):
  H = hist_2d(lon, lat)
  if (ax is not None): 
    # levels=np.arange(0, 0.004, 0.0001)
    levels=10 # cuz I don't know the range of the colorbar
    cf = ax.contourf(H['lon'], H['lat'], H['cnts']/np.sum(H['cnts']), cmap='jet', levels=levels, extend='max')
    cb = plt.colorbar(cf, ax=ax, shrink=0.5, extend='max')
  return H

def track_feature_density_2d(lon, lat, ax=None):
  H = hist_2d(lon, lat)
  if (ax is not None): 
    levels=np.arange(0, 0.004, 0.0001)
    cf = ax.contourf(H['lon'], H['lat'], H['cnts']/np.sum(H['cnts']), cmap='jet', levels=levels, extend='max')
    cb = plt.colorbar(cf, ax=ax, shrink=0.5, extend='max')
  return H

def track_intensity_2d():
  pass

############### main test code #################

# check if mat file exists, if not run the mat file creator code
mat_file = os.path.join(defines.read_folder, f'{defines.model}_{defines.over_write_years[0]}.mat') 
if (not os.path.exists(mat_file)):
  os.system('python3 main_create_dict.py')

# data = {'genesis': {'lat': [], 'lon': [], 'slp': []}, \
#       'lysis': {'lat': [], 'lon': [], 'slp': []}, \
#       'all': {'lat': [], 'lon': [], 'slp': []}}
# # loop through all the years
# for year in range(defines.over_write_years[0], defines.over_write_years[1]+1):
#   tracks = read_tracks(year)
#   tmp = get_data(tracks)
#   for key in data.keys():
#     for inner_key in data[key].keys():
#       data[key][inner_key].extend(tmp[key][inner_key])

# -- new statistic
# loop through all the years
# this part of the code is where I have to keep adding to the histogram
# because now we only have to count one occurence per grid, not all occurences

# Defining the bins
lat_div = 5.
lon_div = 5.
bins = (np.arange(-180, 180+lon_div, lon_div), np.arange(-90, 90+lat_div, lat_div))
lon_mids = bins[0][:-1] + (bins[0][1] - bins[0][0])/2.
lat_mids = bins[1][:-1] + (bins[1][1] - bins[1][0])/2.

# initializing dict that I need
init_shape = (len(lat_mids), len(lon_mids))
stats = {}
for stat_type in ['all', 'genesis', 'lysis']:
  stats[stat_type] = {}
  if (stat_type == 'all'):
    stats[stat_type]['feature_density'] = np.zeros(init_shape)
    stats[stat_type]['track_density'] = np.zeros(init_shape)
  else:
    stats[stat_type] = np.zeros(init_shape)

g_lon = []
g_lat = []
l_lon = []
l_lat = []
# loop through all the years and save the tracks
for year in range(defines.over_write_years[0], defines.over_write_years[1]+1):
  tracks = read_tracks(year)
  for track in tracks: 
    lon = np.squeeze(track['fulllon'])
    lat = np.squeeze(track['fulllat'])

    # # considering only lat cases between -60 and 60
    # ind = (np.abs(lat) < 60)
    # if (not np.any(ind)): 
    #   continue
    # lon = lon[ind]
    # lat = lat[ind]

    l_lon.append(lon[-1])
    l_lat.append(lat[-1])
    g_lon.append(lon[0])
    g_lat.append(lat[0])

    # feature density
    H = hist_2d(lon, lat, bins=bins)

    #  feature density - count all occurences
    stats['all']['feature_density'] += H['cnts']
    stats['all']['track_density'] += np.double(H['cnts'] > 0)

# lysis
H = hist_2d(l_lon, l_lat)
stats['lysis'] = H['cnts']

# genesis
H = hist_2d(g_lon, g_lat)
stats['genesis'] = H['cnts']

# normalizing all the global histograms
stats['genesis'] /= np.nansum(stats['genesis'])
stats['lysis'] /= np.nansum(stats['lysis'])
stats['all']['feature_density'] /= np.nansum(stats['all']['feature_density'])
stats['all']['track_density'] /= np.nansum(stats['all']['track_density'])

# Creating the necessary plots
# track density
plt.close('all')

out_file = os.path.join(defines.images_folder, f'{defines.model}_{year}_track_stats.png')
cmap = 'jet'

# creating the 2x2 plot
fig, axes = plt.subplots(ncols=2, nrows=2, subplot_kw={'projection': cartopy.crs.PlateCarree()}, figsize=(12,8))

ax = global_map(axes[0, 0])
levels = np.linspace(0, 0.0025, 10)
ax.set_title(f'Feature Density')
cf = ax.contourf(lon_mids, lat_mids, stats['all']['feature_density'], cmap=cmap, extend='max', levels=levels)
plt.colorbar(cf, ax=ax, shrink=0.7)

ax = global_map(axes[0, 1])
ax.set_title(f'Track Density')
levels = np.linspace(0, 0.0025, 10)
cf = ax.contourf(lon_mids, lat_mids, stats['all']['track_density'], cmap=cmap, extend='max', levels=levels)
plt.colorbar(cf, ax=ax, shrink=0.7)

ax = global_map(axes[1, 0])
ax.set_title(f'Genesis')
levels = np.linspace(0, 0.0025, 10)
cf = ax.contourf(lon_mids, lat_mids, stats['genesis'], cmap=cmap, extend='max', levels=levels)
plt.colorbar(cf, ax=ax, shrink=0.7)

ax = global_map(axes[1, 1])
ax.set_title(f'Lysis')
levels = np.linspace(0, 0.0025, 10)
cf = ax.contourf(lon_mids, lat_mids, stats['lysis'], cmap=cmap, extend='max', levels=levels)
plt.colorbar(cf, ax=ax, shrink=0.7)

plt.suptitle(f'{defines.model.upper()} ({defines.over_write_years[0]} - {defines.over_write_years[1]})')
plt.tight_layout()
plt.savefig(out_file, dpi=300.)
plt.show()
