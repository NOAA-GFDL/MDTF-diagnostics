import datetime

import gridfill
import numpy as np


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

    lat_lon_filled, converged = gridfill.fill(
        grids=np.ma.masked_invalid(lat_lon_field), xdim=1, ydim=0, eps=0.01,
        cyclic=True, itermax=itermax, verbose=verbose)

    return lat_lon_filled


def fill_nan_with_zonal_mean_each_level(lat_lon_field):
    """
    The solution is from the StackOverflow thread:
        https://stackoverflow.com/questions/18689235/numpy-array-replace-nan-values-with-average-of-columns
    Args:
        lat_lon_field(np.ndarray): field of dimension (lat, lon)
    Returns:
        A 2D array of the same shape as lat_lon_field with NaN filled with zonal mean value
    """

    copy_array = lat_lon_field.copy()
    zonal_mean = np.nan_to_num(np.nanmean(copy_array, axis=-1), nan=10)
    inds = np.where(np.isnan(copy_array))
    copy_array[inds] = np.take(zonal_mean, inds[0])
    return copy_array


def use_northern_hem_data_for_southern_hem(lat_lon_field):
    """
    The solution is from the StackOverflow thread:
        https://stackoverflow.com/questions/18689235/numpy-array-replace-nan-values-with-average-of-columns
    Args:
        lat_lon_field(np.ndarray): field of dimension (lat, lon)
    Returns:
        A 2D array of the same shape as lat_lon_field with NaN filled with zonal mean value
    """

    copy_array = lat_lon_field.copy()
    zonal_mean = np.nan_to_num(np.nanmean(copy_array, axis=-1), nan=10)
    inds = np.where(np.isnan(copy_array))
    copy_array[inds] = np.take(zonal_mean, inds[0])
    return copy_array

if __name__ == '__main__':
    narray = np.array([[1, 0, 1, np.nan], [np.nan, 3, 4, 5],])
    results = fill_nan_with_zonal_mean_each_level(narray)
    print(results.shape)
    print(results)
    print(np.nanmean(narray, axis=-1))
    print(results.mean(axis=-1))
