#!/usr/bin/env python

# Importing Python packages to create plots
import matplotlib.pyplot as plt
# from mpl_toolkits.basemap import Basemap, maskoceans, shiftgrid
import cartopy
import numpy as np 
import os

def plot_zonal(model_zonal_means, erai_zonal_means, era5_zonal_means, out_file=''): 

  plt.close('all')

  plt.figure(figsize=(8,12))
  plt.subplot(2,2,1)
  plt.plot(model_zonal_means['djf'], model_zonal_means['lat'], color='r', label='Model', ls='--')
  plt.plot(erai_zonal_means['djf'], erai_zonal_means['lat'], color='b', label='ERA-Interim', ls='--')
  plt.plot(era5_zonal_means['djf'], era5_zonal_means['lat'], color='g', label='ERA-5', ls='--')
  plt.title('DJF')
  plt.legend(loc=0)
  plt.ylim(-80, 80)
  plt.ylabel('Latitude')
  
  plt.subplot(2,2,2)
  plt.plot(model_zonal_means['jja'], model_zonal_means['lat'], color='r', label='Model', ls='--')
  plt.plot(erai_zonal_means['jja'], erai_zonal_means['lat'], color='b', label='ERA-Interim', ls='--')
  plt.plot(era5_zonal_means['jja'], era5_zonal_means['lat'], color='g', label='ERA-5', ls='--')
  plt.title('JJA')
  plt.legend(loc=0)
  plt.ylim(-80, 80)
  
  plt.subplot(2,2,3)
  plt.plot(model_zonal_means['mam'], model_zonal_means['lat'], color='r', label='Model', ls='--')
  plt.plot(erai_zonal_means['mam'], erai_zonal_means['lat'], color='b', label='ERA-Interim', ls='--')
  plt.plot(era5_zonal_means['mam'], era5_zonal_means['lat'], color='g', label='ERA-5', ls='--')
  plt.title('MAM')
  plt.legend(loc=0)
  plt.ylim(-80, 80)
  plt.ylabel('Latitude')
  plt.xlabel(r'$\tilde{V}^{st}_{850}$ [m/s]')

  plt.subplot(2,2,4)
  plt.plot(model_zonal_means['son'], model_zonal_means['lat'], color='r', label='Model', ls='--')
  plt.plot(erai_zonal_means['son'], erai_zonal_means['lat'], color='b', label='ERA-Interim', ls='--')
  plt.plot(era5_zonal_means['son'], era5_zonal_means['lat'], color='g', label='ERA-5', ls='--')
  plt.title('SON')
  plt.legend(loc=0)
  plt.ylim(-80, 80)
  plt.ylabel('Latitude')
  plt.xlabel(r'$\tilde{V}^{st}_{850}$ [m/s]')

  plt.tight_layout()
  if (len(out_file) > 0):
    if (out_file.endswith('.ps')):
      plt.savefig(out_file, format='eps', dpi=300.)
      plt.close('all')
    elif (out_file.endswith('.png')):
      plt.savefig(out_file, format='png', dpi=300.)
      plt.close('all')


def plot(lonGrid, latGrid, data, show=False, out_file='', title='', **kwargs):

  plt.close('all')

  # data = maskoceans(lonGrid, latGrid, data, inlands=False, resolution='l')
  # data.mask = ~(data.mask)

  plt.figure()
  lllat = np.nanmin(latGrid) 
  urlat = np.nanmax(latGrid) 
  lllon = np.nanmin(lonGrid) 
  urlon = np.nanmax(lonGrid)

  # m = Basemap(projection='cyl', urcrnrlat=urlat, urcrnrlon=urlon, llcrnrlat=lllat, llcrnrlon=lllon)
  # cnt = m.contourf(lonGrid, latGrid, data, cmap='jet', **kwargs)
  # m.colorbar()
  # # m.fillcontinents(lake_color=None)
  # m.drawcoastlines(linewidth=.5)
  # m.drawparallels(np.arange(-90, 90, 25), labels=[True, False, False, False])
  # m.drawmeridians(np.arange(-180, 180, 75), labels=[False, False, False, True])

  ax = plt.axes(projection=cartopy.crs.PlateCarree())
  ax.coastlines()
  cnt = plt.contourf(lonGrid, latGrid, data, cmap='jet', **kwargs)
  cb = plt.colorbar(ax=ax, shrink=0.5)
  cb.ax.set_ylabel(r'$\tilde{V}^{st}_{850}$ [m/s]')
  
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

