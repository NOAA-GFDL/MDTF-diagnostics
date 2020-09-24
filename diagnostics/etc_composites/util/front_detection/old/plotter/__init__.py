import numpy as np 
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

def plot(lon, lat, data, proj='cyl', label_div=[10., 20.], ax=None, show=False, title=None, cmap='jet', figsize=(0, 0)):

  min_lon = np.nanmin(lon)
  min_lat = np.nanmin(lat)
  
  max_lon = np.nanmax(lon)
  max_lat = np.nanmax(lat)

  if (not ax):
    if (figsize[0] == 0):
      fig = plt.figure()
    else: 
      fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111)

  m = Basemap(projection=proj, llcrnrlon=min_lon, urcrnrlon=max_lon, llcrnrlat=min_lat, urcrnrlat=max_lat, ax=ax)
  m.drawcoastlines()
  m.drawparallels(np.arange(int(min_lat/5)*5, max_lat, label_div[0]), labels=[True, False, False, False])
  m.drawmeridians(np.arange(int(min_lon/5)*5, max_lon, label_div[1]), labels=[False, False, False, True])
  c = m.pcolor(lon, lat, data, cmap=cmap)
  m.colorbar(c, ax=ax)

  if (title):
    plt.title(title)

  if (show):
    plt.show()

  return ax, m
