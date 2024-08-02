from typing import Optional

import gridfill
import matplotlib.pyplot as plt  # python library we use to make plots
import numpy as np
import xarray as xr
from falwa.constant import P_GROUND, SCALE_HEIGHT
from matplotlib import gridspec
from cartopy import crs as ccrs

# from diagnostics.finite_amplitude_wave_diag.finite_amplitude_wave_diag_zonal_mean import plev_name, lat_name, lon_name, \
#     sampled_dataset


def gridfill_each_level(lat_lon_field, itermax=1000, verbose=False):
    """
    Fill missing values in lat-lon grids with values derived by solving Poisson's equation
    using a relaxation scheme.

    Args:
        lat_lon_field(np.ndarray): 2D array to apply gridfill on
        itermax(int): maximum iteration for poisson solver
        verbose(bool): verbose level of poisson solver

    Returns:
        A 2D array of the same dimension with all nan filled.
    """
    if np.isnan(lat_lon_field).sum() == 0:
        return lat_lon_field

    lat_lon_filled, converged = gridfill.fill(
        grids=np.ma.masked_invalid(lat_lon_field), xdim=1, ydim=0, eps=0.01,
        cyclic=True, itermax=itermax, verbose=verbose)

    return lat_lon_filled


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
        # plt.savefig(save_path.replace("/PS/", "/").replace(".eps", ".png"), bbox_inches='tight')  # Do I need this?
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
        # plt.savefig(save_path.replace("/PS/", "/").replace(".eps", ".png"), bbox_inches='tight')  # Do I need this?
        plt.show()


def convert_pseudoheight_to_hPa(height_array):
    """
    Args:
        height_array(np.array): pseudoheight in [m]

    Returns:
        np.array which contains pressure levels in [hPa]
    """
    p_array = P_GROUND * np.exp(- height_array / SCALE_HEIGHT)
    return p_array


def convert_hPa_to_pseudoheight(p_array):
    """
    Args:
        height_array(np.array): pseudoheight in [m]

    Returns:
        np.array which contains pressure levels in [hPa]
    """
    height_array = - SCALE_HEIGHT * np.log(p_array / P_GROUND)
    return height_array


class DataPreprocessor:
    def __init__(
            self, wk_dir, xlon, ylat, u_var_name, v_var_name, t_var_name, plev_name, lat_name, lon_name, time_coord_name):

        self._wk_dir = wk_dir
        self._xlon: np.array = xlon  # user input
        self._ylat: np.array = ylat  # user input
        self._u_var_name: str = u_var_name
        self._v_var_name: str = v_var_name
        self._t_var_name: str = t_var_name
        self._plev_name: str = plev_name
        self._lat_name: str = lat_name
        self._lon_name: str = lon_name
        self._original_plev = None
        self._original_lat = None
        self._original_lon = None
        self._original_time_coord = None
        self._time_coord_name: str = time_coord_name
        self._new_time_coord_name: str = "day"
        self._sampled_dataset = None  # Shall be xarray. Set type later
        self._gridfill_needed: Optional[bool] = None
        self._yz_mask = None
        self._xy_mask = None

    @property
    def xy_mask(self):
        return self._xy_mask

    @property
    def yz_mask(self):
        return self._yz_mask

    def _save_original_coordinates(self, dataset):
        self._original_plev = dataset.coords[self._plev_name]
        self._original_lat = dataset.coords[self._lat_name]
        self._original_lon = dataset.coords[self._lon_name]

    def _check_if_gridfill_is_needed(self, sampled_dataset):
        num_of_nan = sampled_dataset[self._u_var_name].isnull().sum().values
        if num_of_nan > 0:
            self._gridfill_needed = True
            self._do_save_mask(sampled_dataset)
        else:
            self._gridfill_needed = False

    def _do_save_mask(self, dataset):
        self._yz_mask = dataset[self._u_var_name]\
            .to_masked_array().mask.sum(axis=0).sum(axis=-1).astype(bool)
        self._xy_mask = dataset[self._u_var_name]\
            .to_masked_array().mask[:, 1:, :, :].sum(axis=0).sum(axis=0).astype(bool)

    def _save_preprocessed_data(self, dataset, output_path):
        dataset.to_netcdf(output_path)
        dataset.close()
        print(f"Finished outputing preprocessed dataset: {output_path}")

    def _interpolate_onto_regular_grid(self, dataset):
        dataset = dataset.interp(
            coords={self._lat_name: self._ylat, self._lon_name: self._xlon},
            method="linear",
            kwargs={"fill_value": "extrapolate"})
        return dataset

    def _implement_gridfill(self, dataset: xr.Dataset):
        if not self._gridfill_needed:
            print("No NaN values detected. Gridfill not needed. Bypass DataPreprocessor._implement_gridfill.")
            return dataset
        # *** Implement gridfill procedure ***
        print(f"self._gridfill_needed = True. Do gridfill with poisson solver.")
        args_tuple = [self._u_var_name, self._v_var_name, self._t_var_name]
        gridfill_file_path = self._wk_dir + "/model/netCDF/gridfill_{var}.nc"
        for var_name in args_tuple:
            field_at_all_level = xr.apply_ufunc(
                gridfill_each_level,
                *[dataset[var_name]],
                input_core_dims=((self._lat_name, self._lon_name),),
                output_core_dims=((self._lat_name, self._lon_name),),
                vectorize=True, dask="allowed")
            field_at_all_level.to_netcdf(gridfill_file_path.format(var=var_name))
            field_at_all_level.close()
            print(f"Finished outputing {var_name} to {gridfill_file_path.format(var=var_name)}")
        load_gridfill_path = gridfill_file_path.format(var="*")
        return load_gridfill_path

    def output_preprocess_data(self, sampled_dataset, output_path):
        """
        Main procedure executed by this class
        """
        self._save_original_coordinates(sampled_dataset)
        self._check_if_gridfill_is_needed(sampled_dataset)
        gridfill_path = self._implement_gridfill(sampled_dataset)
        gridfilled_dataset = xr.open_mfdataset(gridfill_path)
        dataset = self._interpolate_onto_regular_grid(gridfilled_dataset)  # Interpolate onto regular grid
        gridfilled_dataset.close()
        self._save_preprocessed_data(dataset, output_path)  # Save preprocessed data
        dataset.close()



