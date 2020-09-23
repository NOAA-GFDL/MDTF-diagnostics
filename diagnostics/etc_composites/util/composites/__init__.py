import numpy as np 
import matplotlib.pyplot as plt
import math

class dotdict(dict):
  '''
  a dictionary that supports dot notation 
  as well as dictionary access notation 
  usage: d = DotDict() or d = DotDict({'val1':'first'})
  set attributes: d.val2 = 'second' or d['val2'] = 'second'
  get attributes: d.val2 or d['val2']
  '''
  __getattr__ = dict.__getitem__
  __setattr__ = dict.__setitem__
  __delattr__ = dict.__delitem__

  def __init__(self, dct):
    for key, value in dct.items():
      if hasattr(value, 'keys'):
        value = DotDict(value)
      self[key] = value

def plot(H, ax=None): 
  if (ax is None):
    plt.figure()
    plt.pcolormesh(H.x, H.y, H.sum/H.cnt); 
    plt.colorbar()
    plt.show()
  else:
    pc = ax.pcolormesh(H.x, H.y, H.sum/H.cnt); 
    plt.colorbar(pc, ax=ax)

def gplot(lon, lat, data): 
  plt.close('all')
  plt.pcolormesh(lon, lat, data); 
  plt.colorbar()
  plt.show()

def pplot(lon, lat, dist, values, ax=None): 
  mask = dist < 1500
  minLat = np.nanmin(lat[mask])
  maxLat = np.nanmax(lat[mask])
  minLon = np.nanmin(lon[mask])
  maxLon = np.nanmax(lon[mask])
  values[dist > 1500] = np.nan

  if (ax is None): 
    plt.figure()
    plt.pcolormesh(lon, lat, values)
    plt.xlim([minLon, maxLon])
    plt.ylim([minLat, maxLat])
    plt.show()
  else: 
    pc = ax.pcolormesh(lon, lat, values)
    plt.colorbar(pc, ax=ax)
    ax.set_xlim([minLon, maxLon])
    ax.set_ylim([minLat, maxLat])

def haversine_distance(lat, lon, centerLat, centerLon): 
  '''
  Computes the haversine distance between two points. 
  '''
  # km per degree value
  mean_radius_earth = 6371

  # Haversine function to find distances between lat and lon
  lat1 = lat * math.pi / 180; 
  lat2 = centerLat * math.pi / 180; 
  
  lon1 = lon * math.pi / 180; 
  lon2 = centerLon * math.pi / 180; 
  
  # convert dx and dy to radians as well
  dLat = lat1 - lat2
  dLon = lon1 - lon2

  R = mean_radius_earth

  # computing distance in X direction
  a = np.sin(dLat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dLon/2)**2
  c = np.arctan2(np.sqrt(a), np.sqrt(1-a)); 
  dist = 2 * R * c; 

  return dist

def angle_from_center(lat, lon, centerLat, centerLon): 
  '''
  Computes the angle between two points. 
  '''
  # NOTE: have to fix edge issues, for now we will test logic first 
  delta_lat = (lat - centerLat)
  delta_lon = (lon - centerLon)
  theta = np.arctan2(delta_lat, delta_lon)
  return theta

def custom_hist2d(X, Y, values, bins): 
  '''
  Create a 2d histogram given the x and y values along with the bins 
  Returns sum and cnt histogram 2d matrix
  '''
  X = X.flatten()
  Y = Y.flatten()
  values = values.flatten()

  ind = (~np.isnan(X)) & (~np.isnan(Y)) & (~np.isnan(values))
  X = X[ind]
  Y = Y[ind]
  values = values[ind]

  x_edges = bins[0]
  y_edges = bins[1]

  x = x_edges[:-1] + (x_edges[1] - x_edges[0])/2.
  y = y_edges[:-1] + (y_edges[1] - y_edges[0])/2.

  H_sum, _, _ = np.histogram2d(X, Y, bins=bins, weights=values) 
  H_sum = H_sum.T
  H_cnt, _, _ = np.histogram2d(X, Y, bins=bins)
  H_cnt = H_cnt.T
  
  return dotdict({'sum': H_sum, 'cnt': H_cnt, 'x': x, 'y': y, 'x_edges': x_edges, 'y_edges': y_edges})

def circular_avg_one_step(lat, lon, values, centerLat, centerLon, bins=None):
  '''
  get the histogram 2d of count and sum centered at centerLat, centerLon
  '''

  lat = lat.flatten()
  lon = lon.flatten()
  values = values.flatten()

  # calculate distance from center
  dist = haversine_distance(lat, lon, centerLat, centerLon)
  dist_mask = (dist < 1500)

  valid_mask = (dist_mask) & (~np.isnan(values))

  ang = angle_from_center(lat, lon, centerLat, centerLon)

  if bins is None:
    dist_bins = np.arange(0, 1700, 100)
    ang_bins = np.arange(-180, 180+20, 20)*np.pi/180
  else:
    dist_bins = bins[0]
    ang_bins = bins[1]

  H = custom_hist2d(dist[valid_mask], ang[valid_mask], values[valid_mask], bins=(dist_bins, ang_bins))
  
  return H

def area_avg_one_step(lat, lon, values, centerLat, centerLon, bins=None):
  '''
  get the histogram 2d of count and sum centered at centerLat, centerLon
  '''

  # if (np.any(~np.isnan(values))): 
  #   import pdb; pdb.set_trace()

  # calculate distance from center
  dist = haversine_distance(lat, lon, centerLat, centerLon)
  dist_y = haversine_distance(lat, centerLon, centerLat, centerLon)
  dist_x = np.sqrt(dist**2 - dist_y**2)

  # apply mask distance of 1500 km 
  dist_mask = (dist_x < 1500) & (dist_y < 1500)
  dist_mask = (dist < 1500)

  valid_mask = (dist_mask) & (~np.isnan(values))

  # # taking care of the edges, before creating the new equal area grids 
  # lon_shift = np.copy(lon) 
  # lon_shift -= 360. # shift everything to -720 to -180 | -360 to 0

  # creating masks to add -ve values 
  # west_mask = ((lon - centerLon) < 0) | (((lon_shift - centerLon) < 0) & ((lon_shift - centerLon) >- 50))
  if (centerLon < 60):
    west_mask = ((lon - centerLon) < 0) | (lon > 300)
  elif (centerLon > 300):
    east_mask = ((lon - centerLon) >= 0) | (lon < 60)
    west_mask = np.invert(east_mask)
  else: 
    west_mask = ((lon - centerLon) < 0)
  # creating mask so that everything polewards is positive
  # and anything
  equatorward_mask = ((np.abs(lat) - np.abs(centerLat)) < 0)

  dist_x[west_mask] *= -1
  dist_y[equatorward_mask] *= -1

  if not bins:
    dist_bins = np.arange(-1500, 1700, 100)
  else:
    dist_bins = bins[0]
    ang_bins = bins[1]

  H = custom_hist2d(dist_x[valid_mask], dist_y[valid_mask], values[valid_mask], bins=(dist_bins, dist_bins))

  # if (np.nansum(H.sum)> 0):
  #   plt.figure(figsize=(8,4))
  #   ax = plt.subplot(1,2,1)
  #   pplot(lon, lat, dist, values, ax)
  #   ax.plot(centerLon, centerLat, 'r*') 
  #   ax = plt.subplot(1,2,2)
  #   ax.plot(0, 0, 'r*') 
  #   plot(H, ax)
  #   plt.tight_layout()
  #   plt.savefig(f'/localdrive/drive10/mcms_tracker/RUNDIR/tmp_imgs/etc_pr.png', dpi=300.)
  #   import pdb; pdb.set_trace()

  return H

def test_plot(val, lon=None, lat=None):
  plt.style.use(['classic', 'ggplot'])
  plt.ion()
  plt.figure()
  if (lat is None) | (lon is None):
    plt.pcolormesh(val)
  else:
    plt.pcolormesh(lon, lat, val)
  plt.colorbar()
  # plt.show()

def plot_polar(theta, r, values, type='pcolormesh'): 
  '''
  Plots the figure in polar cordinates given theta and r values
  '''
  plt.style.use('ggplot')
  r, theta = np.meshgrid(r,theta)

  # x = r * np.cos(theta)
  # y = r * np.sin(theta)
  # breakpoint()
  # pc = plt.pcolormesh(x, y, values) 

  fig, ax = plt.subplots(subplot_kw=dict(projection='polar'))
  if (type == 'contourf'):
    pc = ax.contourf(theta, r, values, cmap='jet')
  elif (type == 'pcolormesh'):
    pc = ax.pcolormesh(theta, r, values, cmap='jet')
  plt.colorbar(pc)
  # plt.show()

def plot_area(X, Y, values, type='pcolormesh'): 
  '''
  Plots the figure in equal area grid
  '''
  plt.style.use('ggplot')
  fig, ax = plt.subplots()
  if (type == 'contourf'):
    pc = ax.contourf(X, Y, values, cmap='jet')
  elif (type == 'pcolormesh'):
    pc = ax.pcolormesh(X, Y, values, cmap='jet')
  plt.colorbar(pc)
  # plt.show()

def compute_dist_from_cdt(lat, lon, centerLat, centerLon):

    # km per degree value
    mean_radius_earth = 6371

    # Haversine function to find distances between lat and lon
    lat1 = lat * math.pi / 180; 
    lat2 = centerLat * math.pi / 180; 
    
    lon1 = lon * math.pi / 180; 
    lon2 = centerLon * math.pi / 180; 
    
    # convert dx and dy to radians as well
    dLat = lat1 - lat2
    dLon = lon1 - lon2

    R = mean_radius_earth

    # computing distance in X direction
    a = np.sin(dLat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dLon/2)**2
    c = np.arctan2(np.sqrt(a), np.sqrt(1-a)); 
    dist = 2 * R * c; 

    return dist
