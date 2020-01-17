#!/usr/bin/env python

# Importing Python packages to create plots
import matplotlib.pyplot as plt
import cartopy
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import numpy as np 
import os

def plot(lonGrid, latGrid, data, show=False, out_file='', title='', **kwargs):
  
  lonGrid[lonGrid >= 180] -= 360.
  lllat = np.nanmin(latGrid) 
  urlat = np.nanmax(latGrid) 
  lllon = np.nanmin(lonGrid) 
  urlon = np.nanmax(lonGrid)

  plt.close('all')

  plt.figure()
  ax = plt.subplot(111, projection=cartopy.crs.PlateCarree())
  ax.set_extent([lllon, urlon, lllat, urlat])
  ax.coastlines(lw=.5)
  ax.gridlines()
  cf = ax.contourf(lonGrid, latGrid, data, cmap='jet')
  plt.colorbar(cf, ax=ax ,shrink=0.5)
  gl = ax.gridlines(crs=cartopy.crs.PlateCarree(), draw_labels=True, linewidth=2., color='gray', \
      alpha=0.5, linestyle='--')
  gl.xlabels_top = False
  gl.ylabels_right = False
  gl.xformatter = LONGITUDE_FORMATTER
  gl.yformatter = LATITUDE_FORMATTER

  
  if (len(title) > 0):
    plt.title(title)

  if (show):
    plt.show()

  if (len(out_file) > 0):
    if (out_file.endswith('.ps')):
      plt.savefig(out_file, format='eps', dpi=300.)
      plt.close('all')
    elif (out_file.endswith('.png')):
      plt.savefig(out_file, format='png', dpi=300.)
      plt.close('all')

