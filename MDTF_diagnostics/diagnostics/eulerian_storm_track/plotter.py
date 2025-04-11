#!/usr/bin/env python

# Importing Python packages to create plots
import matplotlib.pyplot as plt
import cartopy
from cartopy.util import add_cyclic_point
import numpy as np 


def plot_zonal(model_zonal_means, erai_zonal_means, era5_zonal_means, out_file: str = ''):

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

    plt.subplot(2, 2, 3)
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
    if len(out_file) > 0:
        if out_file.endswith('.ps'):
            plt.savefig(out_file, format='eps', dpi=300.)
            plt.close('all')
        elif out_file.endswith('.png'):
            plt.savefig(out_file, format='png', dpi=300.)
            plt.close('all')


def plot(lonGrid, latGrid, data, show: bool = False, out_file: str = '', title: str ='', **kwargs):

    plt.close('all')

    plt.figure()

    # adding cyclic point
    # provided the values are given as lat x lon
    lons = lonGrid[0,:]
    lats = latGrid[:,0]

    new_data, new_lons = add_cyclic_point(data, coord=lons)
    new_lonGrid, new_latGrid = np.meshgrid(new_lons, lats)

    ax = plt.axes(projection=cartopy.crs.PlateCarree())
    ax.coastlines()
    # getting rid of the line due to lack of continuity
    _ = plt.contourf(new_lonGrid, new_latGrid, new_data, cmap='jet', **kwargs)
    cb = plt.colorbar(ax=ax, shrink=0.5)
    cb.ax.set_ylabel(r'$\tilde{V}^{st}_{850}$ [m/s]')
  
    if len(title) > 0:
        plt.title(title)

    if show:
        plt.show()

    if len(out_file) > 0:
        if out_file.endswith('.ps'):
            plt.savefig(out_file, format='eps', dpi=300.)
            plt.close('all')
        elif out_file.endswith('.png'):
            plt.savefig(out_file, format='png', dpi=300.)
            plt.close('all')
