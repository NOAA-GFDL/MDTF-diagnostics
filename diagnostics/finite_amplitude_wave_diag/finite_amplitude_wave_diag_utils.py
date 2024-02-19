from typing import Dict
import numpy as np
import xarray as xr  # python library we use to read netcdf files
import matplotlib.pyplot as plt  # python library we use to make plots
from matplotlib import gridspec
from cartopy import crs as ccrs
from falwa.xarrayinterface import QGDataset
from falwa.oopinterface import QGFieldNH18
from falwa.constant import P_GROUND, SCALE_HEIGHT


class LatLonMapPlotter(object):
    def __init__(self, figsize, title_str, xgrid, ygrid, cmap, xland, yland, lon_range, lat_range):
        self._figsize = figsize
        self._title_str = title_str
        self._xgrid = xgrid
        self._ygrid = ygrid
        self._cmap = cmap
        self._xland = xland
        self._yland = yland
        self._lon_range = lon_range
        self._lat_range = lat_range

    def plot_and_save_variable(self, variable, cmap, var_title_str, save_path, num_level=30):
        fig = plt.figure(figsize=self._figsize)
        spec = gridspec.GridSpec(
            ncols=1, nrows=1, wspace=0.3, hspace=0.3)
        ax = fig.add_subplot(spec[0], projection=ccrs.PlateCarree())
        ax.coastlines(color='black', alpha=0.7)
        ax.set_aspect('auto', adjustable=None)
        main_fig = ax.contourf(
            self._xgrid, self._ygrid,
            variable,
            num_level,
            cmap=cmap)
        ax.scatter(self._xgrid[self._xland], self._ygrid[self._yland], s=1, c='gray')
        ax.set_xticks(self._lon_range, crs=ccrs.PlateCarree())
        ax.set_yticks(self._lat_range, crs=ccrs.PlateCarree())
        fig.colorbar(main_fig, ax=ax)
        ax.set_title(f"{self._title_str}\n{var_title_str}")
        plt.savefig(save_path, bbox_inches='tight')
        plt.savefig(save_path.replace(".png", ".eps"), bbox_inches='tight')
        plt.show()


class HeightLatPlotter(object):
    def __init__(self, figsize, title_str, xgrid, ygrid, cmap, xlim):
        self._figsize = figsize
        self._title_str = title_str
        self._xgrid = xgrid
        self._ygrid = ygrid
        self._cmap = cmap
        self._xlim = xlim  # [-80, 80]

    def plot_and_save_variable(self, variable, cmap, var_title_str, save_path, num_level=30):
        fig = plt.figure(figsize=self._figsize)
        spec = gridspec.GridSpec(ncols=1, nrows=1)
        ax = fig.add_subplot(spec[0])
        # *** Zonal mean U ***
        main_fig = ax.contourf(
            self._xgrid,
            self._ygrid,
            variable,
            num_level,
            cmap=cmap if cmap else self._cmap)
        fig.colorbar(main_fig, ax=ax)
        ax.set_title(f"{self._title_str}\n{var_title_str}")
        ax.set_xlim(self._xlim)
        plt.tight_layout()
        plt.savefig(save_path, bbox_inches='tight')
        plt.savefig(save_path.replace(".png", ".eps"), bbox_inches='tight')  # Do I need this?
        plt.show()
