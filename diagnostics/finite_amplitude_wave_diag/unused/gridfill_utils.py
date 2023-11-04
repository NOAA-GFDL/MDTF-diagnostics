import numpy as np


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
