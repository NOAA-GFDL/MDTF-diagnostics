#!/usr/bin/env python

# Importing Python packages to create plots
import matplotlib.pyplot as plt
# from mpl_toolkits.basemap import Basemap
import cartopy
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import numpy as np 
import os

def plot(lonGrid, latGrid, data, show=True, out_file=''):

  lllat = np.nanmin(latGrid) 
  urlat = np.nanmax(latGrid) 
  lllon = np.nanmin(lonGrid) 
  urlon = np.nanmax(lonGrid)

  plt.figure()
  ax = plt.subplot(111, projection=cartopy.crs.PlateCarree())
  ax.set_extend([lllon, urlon, lllat, urlat])
  ax.coastlines(lw=.5)
  ax.gridlines()
  # m = Basemap(projection='cyl', urcrnrlat=urlat, urcrnrlon=urlon, llcrnrlat=lllat, llcrnrlon=lllon)
  # m.drawcoastlines(linewidth=.5)
  cf = ax.contourf(lonGrid, latGrid, data, cmap='jet')
  # for c in cnt.collections:
    # c.set_edgecolor('k')
    # c.set_linewidth(0.01)
  plt.colorbar(cf, ax=ax ,shrink=0.5)
  gl = ax.gridlines(crs=cartopy.crs.PlateCarree(), draw_labels=True, linewidth=2., color='gray', \
      alpha=0.5, linestyle='--')
  gl.xlabels_top = False
  gl.ylabels_right = False
  gl.xformatter = LONGITUDE_FORMATTER
  gl.yformatter = LATITUDE_FORMATTER

  if (show):
    plt.show()

  if (len(out_file) > 0):
    out_full_file = os.environ['fig_out_folder'] + out_file
    plt.save_fig(out_full_file)

