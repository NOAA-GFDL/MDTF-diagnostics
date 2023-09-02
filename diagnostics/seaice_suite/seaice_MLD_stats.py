#!/usr/bin/env python
# coding: utf-8
import numpy as np
import pandas as pd
from scipy import stats


def xr_reshape(a, dim, newdims, coords):
    """ Reshape DataArray a to convert its dimension dim into sub-dimensions given by
    newdims and the corresponding coords.
    Example: ar = xr_reshape(a, 'time', ['year', 'month'], [(2017, 2018), np.arange(12)]) """

    # Create a pandas MultiIndex from these labels
    ind = pd.MultiIndex.from_product(coords, names=newdims)

    # Replace the time index in the DataArray by this new index,
    a1 = a.copy()

    a1.coords[dim] = ind

    # Convert multiindex to individual dims using DataArray.unstack().
    # This changes dimension order! The new dimensions are at the end.
    a1 = a1.unstack(dim)

    # Permute to restore dimensions
    i = a.dims.index(dim)
    dims = list(a1.dims)

    for d in newdims[::-1]:
        dims.insert(i, d)

    for d in newdims:
        _ = dims.pop(-1)

    return a1.transpose(*dims)


def _lrm(x=None, y=None):
    """wrapper that returns the predicted values from a linear regression fit of x and y"""

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    return slope, intercept


def _lagcorr(a, lag=1):
    """wrapper that returns lagged correlation
    Parameters
    ----------
    a : ndarray with leading dim of index which is combination of (year,month) in that order
        Input array.
    Returns
    -------
    res : ndarray
        Pearson's correlation coefficient at one month lag for each month
    See Also
    --------
    scipy.stats.pearsonr """

    sumfunc = np.nansum
 
    NN = a.shape
    NYR = NN[0]
    N = NYR*12
    
    # create new matrix like a, but shifted by one month
    b = np.copy(a)
    b = b.reshape(N, 1)
    b = np.r_[b, np.nan*np.ones((lag, 1))]  # add a new row of nans to b
    b = b[lag:(N+lag), ...]  # eliminate first row
    b = b.reshape(NYR, 12)  # return to year,month
    
    r_num = sumfunc(a * b, axis=0)
    r_den = np.sqrt(sumfunc(a * a, axis=0) * sumfunc(b * b, axis=0))

    r = r_num / r_den
    return r


