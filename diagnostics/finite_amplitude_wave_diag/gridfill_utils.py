import datetime

import gridfill
import numpy as np


def gridfill_each_level(lat_lon_field, itermax=1000, verbose=False):
    """
    Apply gridfill to do interpolation on lat-lon grid using poisson solver, and then interpolate onto 1-degree grid

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


