#!/usr/bin/env python

# Importing Python packages to create plots
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap, maskoceans, shiftgrid
import numpy as np 
import os

def plot(lonGrid, latGrid, data, show=False, out_file='', title='', **kwargs):

  plt.close('all')

  # data = maskoceans(lonGrid, latGrid, data, inlands=False, resolution='l')
  # data.mask = ~(data.mask)

  plt.figure()
  lllat = np.nanmin(latGrid) 
  urlat = np.nanmax(latGrid) 
  lllon = np.nanmin(lonGrid) 
  urlon = np.nanmax(lonGrid)

  m = Basemap(projection='cyl', urcrnrlat=urlat, urcrnrlon=urlon, llcrnrlat=lllat, llcrnrlon=lllon)
  cnt = m.contourf(lonGrid, latGrid, data, cmap='jet', **kwargs)
  m.colorbar()
  # m.fillcontinents(lake_color=None)
  m.drawcoastlines(linewidth=.5)
  m.drawparallels(np.arange(-90, 90, 25), labels=[True, False, False, False])
  m.drawmeridians(np.arange(-180, 180, 75), labels=[False, False, False, True])
  
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

