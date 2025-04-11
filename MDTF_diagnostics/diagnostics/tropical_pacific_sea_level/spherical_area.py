import numpy as np


def cal_area(lon, lat, dlon, dlat, r_earth=6.371 * 1e8):
    # input : lon, lat (not array, but single element)
    # output : area that matches the [lon,lat] coordinate
    #          units in cm^2

    # constant
    arad = r_earth
    dlon = np.float64(dlon * np.pi / 180.0)
    dlat = np.float64(dlat * np.pi / 180.0)
    lat = (90.0 - lat) * np.pi / 180.0
    area = arad * arad * np.sin(lat) * dlon * dlat

    return area


def da_area(
    da_var,
    lonname="lon",
    latname="lat",
    xname="x",
    yname="y",
    model=None,
    r_earth=6.371 * 1e8,
):
    """
    calculate spherical area
    
    """
    #     r_earth = 6.371*1E8         # cm

    if model in ["gfdl"]:

        # calculate dy
        dy = da_var[latname].copy() + np.nan
        dyl = da_var[latname].diff(yname, 1, label="lower")
        dyu = da_var[latname].diff(yname, 1, label="upper")

        dy.values[0, :] = dyl.values[0, :]  # forward differences
        dy.values[1:-1, :] = (dyl + dyu).values / 2.0  # central differences
        dy.values[-1, :] = dyu.values[-1, :]  # backward differences
        da_dy = dy / 180.0 * np.pi * r_earth / 100.0  # m  (2D)

        # calculate dx
        dx = da_var[lonname].copy() + np.nan
        dxl = da_var[lonname].diff(xname, 1, label="lower")
        dxu = da_var[lonname].diff(xname, 1, label="upper")

        dx.values[:, 0] = dxl.values[:, 0]  # forward differences
        dx.values[:, 1:-1] = (dxl + dxu).values / 2.0  # central differences
        dx.values[:, -1] = dxu.values[:, -1]  # backward differences
        da_dx = (
            dx
            / 180.0
            * np.pi
            * r_earth
            * np.cos(da_var[latname] / 180.0 * np.pi)
            / 100.0
        )  # m  (2D)

    else:

        # calculate dy
        dy = da_var[latname].copy() + np.nan
        dyl = da_var[latname].diff(yname, 1, label="lower")
        dyu = da_var[latname].diff(yname, 1, label="upper")

        dy.values[0] = dyl.values[0]  # forward differences
        dy.values[1:-1] = (dyl + dyu).values / 2.0  # central differences
        dy.values[-1] = dyu.values[-1]  # backward differences
        da_dy = dy / 180.0 * np.pi * r_earth / 100.0  # m  (2D)

        # calculate dx
        dx = da_var[lonname].copy() + np.nan
        dxl = da_var[lonname].diff(xname, 1, label="lower")
        dxu = da_var[lonname].diff(xname, 1, label="upper")

        dx.values[0] = dxl.values[0]  # forward differences
        dx.values[1:-1] = (dxl + dxu).values / 2.0  # central differences
        dx.values[-1] = dxu.values[-1]  # backward differences
        da_dx = (
            dx
            / 180.0
            * np.pi
            * r_earth
            * np.cos(da_var[latname] / 180.0 * np.pi)
            / 100.0
        )  # m (2D)

    da_area = da_dx * da_dy

    return da_area
