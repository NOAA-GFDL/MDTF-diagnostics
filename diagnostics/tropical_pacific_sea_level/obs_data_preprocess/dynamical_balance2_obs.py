import numpy as np


####
# Input variable are all xr.DataArray
####

####


def curl_var(da_uo, da_vo, x_name="lon", y_name="lat", r_earth=6.371 * 1e8):
    """
    Calculate the curl of the vector field 
    
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    # make sure the dim order is correct
    da_uo = da_uo.transpose(y_name,x_name)
    da_vo = da_vo.transpose(y_name,x_name)
    
    # calulate du
    du_dy = da_uo.copy() + np.nan
    du_yl = da_uo.diff(y_name, 1, label="lower")
    du_yu = da_uo.diff(y_name, 1, label="upper")

    du_dy.values[0, :] = du_yl.values[0, :]  # forward differences
    du_dy.values[1:-1, :] = (du_yl + du_yu).values  # central differences
    du_dy.values[-1, :] = du_yu.values[-1, :]  # backward differences

    # calculate dy
    dy = du_dy.lat.copy() + np.nan
    dyl = du_dy.lat.diff(y_name, 1, label="lower")
    dyu = du_dy.lat.diff(y_name, 1, label="upper")

    dy.values[0] = dyl.values[0]  # forward differences
    dy.values[1:-1] = (dyl + dyu).values  # central differences
    dy.values[-1] = dyu.values[-1]  # backward differences
    da_dy = dy / 180.0 * np.pi * r_earth / 100.0  # m

    # du/dy
    du_dy = du_dy / da_dy  # N/m^3

    # calulate dv
    dv_dx = da_vo.copy() + np.nan
    dv_xl = da_vo.diff(x_name, 1, label="lower")
    dv_xr = da_vo.diff(x_name, 1, label="upper")

    dv_dx.values[:, 0] = dv_xl.values[:, 0]  # forward differences
    dv_dx.values[:, 1:-1] = (dv_xl + dv_xr).values  # central differences
    dv_dx.values[:, -1] = dv_xr[:, -1].values  # backward differences

    # calculate dx
    dx = dv_dx.lon.copy() + np.nan
    dxl = dv_dx.lon.diff(x_name, 1, label="lower")
    dxu = dv_dx.lon.diff(x_name, 1, label="upper")

    dx.values[0] = dxl.values[0]  # forward differences
    dx.values[1:-1] = (dxl + dxu).values  # central differences
    dx.values[-1] = dxu.values[-1]  # backward differences
    da_dx = (
        dx / 180.0 * np.pi * r_earth * np.cos(da_uo.lat / 180.0 * np.pi) / 100.0
    )  # m

    # dv/dx
    dv_dx = dv_dx / da_dx  # N/m^3

    curl_v = dv_dx
    curl_u = -du_dy

    return curl_u, curl_v


def curl_var_3d(da_varx, da_vary, xname="lon", yname="lat", tname="time", r_earth=6.371 * 1e8):
    """
    Calculate wind stress curl 
    
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    3. Both are 3d array with (time,y,x) 
    
    """

    # make sure the dim order is correct
    da_varx = da_varx.transpose(tname,yname,xname)
    da_vary = da_vary.transpose(tname,yname,xname)    
    
    # calulate dtauu
    du_dy = da_varx.copy() + np.nan
    du_yl = da_varx.diff(yname, 1, label="lower")
    du_yu = da_varx.diff(yname, 1, label="upper")

    du_dy.values[:, 0, :] = du_yl.values[:, 0, :]  # forward differences
    du_dy.values[:, 1:-1, :] = (du_yl + du_yu).values  # central differences
    du_dy.values[:, -1, :] = du_yu.values[:, -1, :]  # backward differences

    # calculate dy
    dy = du_dy.lat.copy() + np.nan
    dyl = du_dy.lat.diff(yname, 1, label="lower")
    dyu = du_dy.lat.diff(yname, 1, label="upper")

    dy.values[0] = dyl.values[0]  # forward differences
    dy.values[1:-1] = (dyl + dyu).values  # central differences
    dy.values[-1] = dyu.values[-1]  # backward differences
    da_dy = dy / 180.0 * np.pi * r_earth / 100.0  # m

    # du/dy
    du_dy = du_dy / da_dy  # N/m^3

    # calulate dtauv
    dv_dx = da_vary.copy() + np.nan
    dv_xl = da_vary.diff(xname, 1, label="lower")
    dv_xr = da_vary.diff(xname, 1, label="upper")

    dv_dx.values[:, :, 0] = dv_xl.values[:, :, 0]  # forward differences
    dv_dx.values[:, :, 1:-1] = (dv_xl + dv_xr).values  # central differences
    dv_dx.values[:, :, -1] = dv_xr[:, :, -1].values  # backward differences

    # calculate dx
    dx = dv_dx.lon.copy() + np.nan
    dxl = dv_dx.lon.diff(xname, 1, label="lower")
    dxu = dv_dx.lon.diff(xname, 1, label="upper")

    dx.values[0] = dxl.values[0]  # forward differences
    dx.values[1:-1] = (dxl + dxu).values  # central differences
    dx.values[-1] = dxu.values[-1]  # backward differences
    da_dx = (
        dx / 180.0 * np.pi * r_earth * np.cos(da_varx.lat / 180.0 * np.pi) / 100.0
    )  # m

    # dv/dx
    dv_dx = dv_dx / da_dx  # N/m^3

    curlvar_v = dv_dx
    curlvar_u = -du_dy

    return curlvar_u, curlvar_v
