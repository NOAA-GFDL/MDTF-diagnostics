import numpy as np
import sys

####
# Input variable are all xr.DataArray

# The function here is designed for the MOM6 output 
#  lon lat is 2-D array with x,y are mere indices
####


def sverdrup_transport_3d(da_tauuo,da_tauvo):
    """
    Calculate sverdrup transport (whole water column transport)
    
    !!!
    Assumption : Sverdrup transport is dominated by zonal wind 
    !!!
    
    Wind stress tauu ($\tau_x$) and tauv ($\tau_y$) are used to calculate the transport

    , where rho is the average ocean density 1025kg/m^3  
    and beta = df/dy where f is Coriolis parameter 

    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    sea_density = 1025.       # kg/m^3 
    omega = 7.2921159*1E-5      # rad/s
    r_earth = 6.371*1E8         # cm
    
    
    # df/dy
    da_beta = 2.*omega*np.cos(da_tauuo.lat/180.*np.pi)/(r_earth*1e-2)   #1/m/s
    
    # Sverdrup transport
    curlx,curly = curl_tau_3d(da_tauuo,da_tauvo)      # N/m^3 = kg*m/s^2/m^3 = kg/m^2/s^2
    da_V_sv = 1/da_beta*(curlx+curly)/sea_density  # (m*s)*(kg/m^2/s^2)/(kg/m^3) = (kg/m/s)*(m^3/kg) = m^2/s
    da_V_sv = da_V_sv.transpose("time", "y", "x")
    
    # stream function
    da_stream_sv = -integral_x_FromEB_3d(da_V_sv)     # m^3/s
    
    # using stream function to derive x
    da_U_sv = dvar_dy_3d(da_stream_sv)
    
    
    return da_U_sv,da_V_sv,da_stream_sv

def dvar_dy_3d(da_var):
    """
    for 3-D array [time,y,x]
    """
    omega = 7.2921159*1e-5      # rad/s
    r_earth = 6.371*1e8         # cm
    
    # calulate dvar
    dv_dy = da_var.copy()+np.nan
    dv_yl = da_var.diff('y',1,label='lower')
    dv_yu = da_var.diff('y',1,label='upper')
    
    dv_dy.values[:,0,:] = dv_yl.values[:,0,:]              # forward differences
    dv_dy.values[:,1:-1,:] = (dv_yl+dv_yu).values        # central differences
    dv_dy.values[:,-1,:] = dv_yu.values[:,-1,:]            # backward differences
    
    # calculate dy 
    dy = dv_dy.lat.copy()+np.nan
    dyl = dv_dy.lat.diff('y',1,label='lower')
    dyu = dv_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]                    # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values                # central differences
    dy.values[-1,:] = dyu.values[-1,:]                  # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.                  # m
    
 
    dvar_dy = dv_dy/da_dy
    
    return dvar_dy
    

def integral_x_FromEB_3d(da_var):
    omega = 7.2921159*1E-5      # rad/s
    r_earth = 6.371*1E8         # cm
    
    da_mask = da_var.where(da_var.isnull(),other=1.)
    da_var = da_var.where(da_var.notnull(),other=0.)
    
    # calculate dx 
    dx = da_var.lon.copy()+np.nan
    dxl = da_var.lon.diff('x',1,label='lower')
 

    dx.values[:,0] = dxl[:,0].values                      
    dx.values[:,1:] = dxl.values                 
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_var.lat/180.*np.pi)/100.     # m
    
    # calulate int_var
    int_var = da_var.copy()*0.
    int_var_prev = da_var[:,:,:-1].values
    int_var_cur = da_var[:,:,1:].values
     
    int_var.values[:,:,:-1] = (int_var_prev+int_var_cur)/2.      
    int_var = int_var*da_dx
    
    int_var = np.cumsum(int_var.values[:,:,::-1],axis=2)[:,:,::-1]*da_mask
    
    return int_var    
    

    
def barotropic_streamfunc(da_vo,da_depth,dep_dim='z'):
    """
    Calculate sverdrup transport (whole water column transport)
    
    !!!
    Assumption : Sverdrup transport is dominated by zonal wind 
    !!!
    
    Wind stress tauu ($\tau_x$) and tauv ($\tau_y$) are used to calculate the transport

    , where rho is the average ocean density 1025kg/m^3  
    and beta = df/dy where f is Coriolis parameter 

    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    
    # calculate dz
    da_dz = da_vo.z.copy()
    da_dz.values[1:-1] = (da_vo.z[:-1].diff(dep_dim,1).values+da_vo.z[1:].diff(dep_dim,1).values)/2.
    da_dz.values[0] = (da_vo.z[1]-da_vo.z[0]).values
    da_dz.values[-1] = (da_vo.z[-1]-da_vo.z[-2]).values  # meters 
    

    # calculate depth average V
    da_V = (da_dz*da_vo).sum(dim=dep_dim)#/da_depth
    
    
    # stream function
    da_stream = -integral_x_FromEB(da_V)     # m^3/s

    
    
    return da_stream
    
    
    
def sverdrup_transport(da_tauuo,da_tauvo):
    """
    Calculate sverdrup transport (whole water column transport)
    
    !!!
    Assumption : Sverdrup transport is dominated by zonal wind 
    !!!
    
    Wind stress tauu ($\tau_x$) and tauv ($\tau_y$) are used to calculate the transport

    , where rho is the average ocean density 1025kg/m^3  
    and beta = df/dy where f is Coriolis parameter 

    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    sea_density = 1025.       # kg/m^3 
    omega = 7.2921159*1E-5      # rad/s
    r_earth = 6.371*1E8         # cm
    
    
    # df/dy
    da_beta = 2.*omega*np.cos(da_tauuo.lat/180.*np.pi)/(r_earth*1e-2)   #1/m/s
    
    # Sverdrup transport
    curlx,curly = curl_tau(da_tauuo,da_tauvo)      # N/m^3 = kg*m/s^2/m^3 = kg/m^2/s^2
    da_V_sv = 1/da_beta*(curlx+curly)/sea_density  # (m*s)*(kg/m^2/s^2)/(kg/m^3) = (kg/m/s)*(m^3/kg) = m^2/s
    
    # stream function
    da_stream_sv = -integral_x_FromEB(da_V_sv)     # m^3/s
    
    # continuity to derive U
    
#     # using continuity equation directly
#     da_dVdy = dvar_dy(da_V_sv)
#     da_dUdx = -da_dVdy   
#     da_U_sv = integral_x_FromEB(da_dUdx)
    
    # using stream function to derive x
    da_U_sv = dvar_dy(da_stream_sv)
    
    
    return da_U_sv,da_V_sv,da_stream_sv


def dvar_dy(da_var):
    """
    for 2-D array [y,x]
    """
    omega = 7.2921159*1e-5      # rad/s
    r_earth = 6.371*1e8         # cm
    
    # calulate dvar
    dv_dy = da_var.copy()+np.nan
    dv_yl = da_var.diff('y',1,label='lower')
    dv_yu = da_var.diff('y',1,label='upper')
    
    dv_dy.values[0,:] = dv_yl.values[0,:]              # forward differences
    dv_dy.values[1:-1,:] = (dv_yl+dv_yu).values        # central differences
    dv_dy.values[-1,:] = dv_yu.values[-1,:]            # backward differences
    
    # calculate dy 
    dy = dv_dy.lat.copy()+np.nan
    dyl = dv_dy.lat.diff('y',1,label='lower')
    dyu = dv_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]                    # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values                # central differences
    dy.values[-1,:] = dyu.values[-1,:]                  # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.                  # m
    
 
    dvar_dy = dv_dy/da_dy
    
    return dvar_dy
    

def integral_x_FromEB(da_var):
    omega = 7.2921159*1E-5      # rad/s
    r_earth = 6.371*1E8         # cm
    
    da_mask = da_var.where(da_var.isnull(),other=1.)
    da_var = da_var.where(da_var.notnull(),other=0.)
    
    # calculate dx 
    dx = da_var.lon.copy()+np.nan
    dxl = da_var.lon.diff('x',1,label='lower')
 

    dx.values[:,0] = dxl[:,0].values                      
    dx.values[:,1:] = dxl.values                 
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_var.lat/180.*np.pi)/100.     # m
    
    # calulate int_var
    int_var = da_var.copy()*0.
    int_var_prev = da_var[:,:-1].values
    int_var_cur = da_var[:,1:].values
     
    int_var.values[:,:-1] = (int_var_prev+int_var_cur)/2.      
    int_var = int_var*da_dx
    
    int_var = np.cumsum(int_var.values[:,::-1],axis=1)[:,::-1]*da_mask
    
    return int_var    
    
    
    
    
# def integral_x_FromEB_temp(da_var):
#     omega = 7.2921159*1E-5      # rad/s
#     r_earth = 6.371*1E8         # cm
    
#     da_mask = da_var.where(da_var.isnull(),other=1.)
#     da_var = da_var.where(da_var.notnull(),other=0.)
    
#     # calculate dx 
#     dx = da_var.lon.copy()+np.nan
#     dxl = da_var.lon.diff('x',1,label='lower')
 

#     dx.values[:,0] = dxl[:,0].values                      
#     dx.values[:,1:] = dxl.values                 
#     da_dx = dx/180.*np.pi*r_earth*np.cos(da_var.lat/180.*np.pi)/100.     # m
    
#     # calulate int_var
#     int_var = da_var.copy()*0.
#     int_var_prev = da_var[:,:-1].values
#     int_var_cur = da_var[:,1:].values
     
#     int_var.values[:,1:] = (int_var_prev+int_var_cur)/2.      
#     int_var = int_var*da_dx
    
#     int_var = np.cumsum(int_var.values[:,::-1],axis=1)[:,::-1]*da_mask
    
#     return int_var

# def integral_y(da_var):
#     omega = 7.2921159*1E-5      # rad/s
#     r_earth = 6.371*1E8         # cm
    
#     da_var = da_var.where(da_var.notnull(),other=0.)
    
#     # calculate dy 
#     dy = da_var.lat.copy()+np.nan
#     dyl = da_var.lat.diff('y',1,label='lower')

#     dy.values[0,:] = 0.                         
#     dy.values[1:,:] = dyl.values       
#     da_dy = dy/180.*np.pi*r_earth/100.                  # m
    
#     # calulate int_var
#     int_var = da_var.copy()*0.
#     int_var_prev = da_var[:-1,:].values
#     int_var_cur = da_var[1:,:].values
    
#     int_var.values[0,:] = 0.                                      # start as 0 when y = 0
#     int_var.values[1:,:] = (int_var_prev+int_var_cur)/2.      
#     int_var = int_var*da_dy
    
#     int_var = int_var.cumsum(dim='y')
    
#     return int_var

# def dvar_dy_1d(da_var):
#     """
#     for 1-D array [y]
#     """
#     omega = 7.2921159*1e-5      # rad/s
#     r_earth = 6.371*1e8         # cm
    
#     # calulate dvar
#     dv_dy = da_var.copy()+np.nan
#     dv_yl = da_var.diff('y',1,label='lower')
#     dv_yu = da_var.diff('y',1,label='upper')
    
#     dv_dy.values[0] = dv_yl.values[0]              # forward differences
#     dv_dy.values[1:-1] = (dv_yl+dv_yu).values        # central differences
#     dv_dy.values[-1] = dv_yu.values[-1]            # backward differences
    
#     # calculate dy 
#     dy = dv_dy.y.copy()+np.nan
#     dyl = dv_dy.y.diff('y',1,label='lower')
#     dyu = dv_dy.y.diff('y',1,label='upper')
    
#     dy.values[0] = dyl.values[0]                    # forward differences
#     dy.values[1:-1] = (dyl+dyu).values                # central differences
#     dy.values[-1] = dyu.values[-1]                  # backward differences  
#     da_dy = dy/180.*np.pi*r_earth/100.                  # m
    
 
#     dvar_dy = dv_dy/da_dy
    
#     return dvar_dy
    


# def dvar_dy_3d(da_var):
#     """
#     for 3-D array [time,y,x]
#     """
#     omega = 7.2921159*1E-5      # rad/s
#     r_earth = 6.371*1E8         # cm
    
#     # calulate dvar
#     dv_dy = da_var.copy()+np.nan
#     dv_yl = da_var.diff('y',1,label='lower')
#     dv_yu = da_var.diff('y',1,label='upper')
    
#     dv_dy.values[:,0,:] = dv_yl.values[:,0,:]              # forward differences
#     dv_dy.values[:,1:-1,:] = (dv_yl+dv_yu).values        # central differences
#     dv_dy.values[:,-1,:] = dv_yu.values[:,-1,:]            # backward differences
    
#     # calculate dy 
#     dy = dv_dy.lat.copy()+np.nan
#     dyl = dv_dy.lat.diff('y',1,label='lower')
#     dyu = dv_dy.lat.diff('y',1,label='upper')
    
#     dy.values[0,:] = dyl.values[0,:]                    # forward differences
#     dy.values[1:-1,:] = (dyl+dyu).values                # central differences
#     dy.values[-1,:] = dyu.values[-1,:]                  # backward differences  
#     da_dy = dy/180.*np.pi*r_earth/100.                  # m
    
 
#     dvar_dy = dv_dy/da_dy
    
#     return dvar_dy
    

# def integral_x_3d(da_var):
#     omega = 7.2921159*1E-5      # rad/s
#     r_earth = 6.371*1E8         # cm
    
#     da_var = da_var.where(da_var.notnull(),other=0.)
    
#     # calculate dx 
#     dx = da_var.lon.copy()+np.nan
#     dxl = da_var.lon.diff('x',1,label='lower')
#     #dxu = da_var.lon.diff('x',1,label='upper')

#     dx.values[:,0] = 0.                         
#     dx.values[:,1:] = dxl.values                 
#     da_dx = dx/180.*np.pi*r_earth*np.cos(da_var.lat/180.*np.pi)/100.     # m
    
#     # calulate int_var
#     int_var = da_var.copy()*0.
#     int_var_prev = da_var[:,:,:-1].values
#     int_var_cur = da_var[:,:,1:].values
    
#     int_var.values[:,:,0] = 0.                                      # start as 0 when x = 0
#     int_var.values[:,:,1:] = (int_var_prev+int_var_cur)/2.      
#     int_var = int_var*da_dx
    
#     int_var = int_var.cumsum(dim='x')
    
#     return int_var
    
    

def divergence(da_u,da_v):
    """
    calculate horizonal divergence based on U,V field
    
    """
    g = 9.81                  # m/s^2
    omega = 7.2921159*1E-5    # rad/s
    r_earth = 6.371*1E8         # cm

    
    # calulate dv
    dv_dy = da_v.copy()+np.nan
    dv_yl = da_v.diff('y',1,label='lower')
    dv_yu = da_v.diff('y',1,label='upper')
    
    dv_dy.values[0,:] = dv_yl.values[0,:]              # forward differences
    dv_dy.values[1:-1,:] = (dv_yl+dv_yu).values        # central differences
    dv_dy.values[-1,:] = dv_yu.values[-1,:]            # backward differences
    
    # calculate dy 
    dy = dv_dy.lat.copy()+np.nan
    dyl = dv_dy.lat.diff('y',1,label='lower')
    dyu = dv_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]                           # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values                     # central differences
    dy.values[-1,:] = dyu.values[-1,:]                         # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.                     # m
    
    # dv/dy 
    dv_dy = dv_dy/da_dy                                # 1/s
    
    # calulate du
    du_dx = da_u.copy()+np.nan
    du_xl = da_u.diff('x',1,label='lower')
    du_xr = da_u.diff('x',1,label='upper')

    du_dx.values[:,0] = du_xl.values[:,0]              # forward differences
    du_dx.values[:,1:-1] = (du_xl+du_xr).values        # central differences
    du_dx.values[:,-1] = du_xr[:,-1].values            # backward differences

    # calculate dx 
    dx = du_dx.lon.copy()+np.nan
    dxl = du_dx.lon.diff('x',1,label='lower')
    dxu = du_dx.lon.diff('x',1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]                           # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values                     # central differences
    dx.values[:,-1] = dxu.values[:,-1]                         # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_u.lat/180.*np.pi)/100.     # m
    
    # du/dx 
    du_dx = du_dx/da_dx                                # 1/s 
    
    
    # divergence flow    
    da_divx = du_dx
    da_divy = dv_dy       # 1/s
    
    return da_divx,da_divy



def geostraphic_flow(da_zos,da_rho,dep=100,eq_mask=True):
    """
    Calculate geostrophic flow based on geostrophic balance. Therefore
    depth has to set to lower than Ekman layer (different in location)
    but the general depth is around 80m
    
    
    # Calculate Geostrophic flow
    The geostrophic flow is calculated based on geostrophic balance
    > fv = \frac{1}{\rho}\frac{\partial p}{\partial x} + g/rho_0 \int^0_z \partial rho/\partial x
    > fu = -\frac{1}{\rho}\frac{\partial p}{\partial y} + g/rho_0 \int^0_z \partial rho/\partial y 
    > p = p_{atm}+\int_{-h}^\eta g\rho dz

    -h is ocean bottom, $\eta$ is sea surface height above geoid, and $p_{atm}$ is atmospheric pressure. 
    In this calculate, we investigate the sea surface height induced surface current. 
    We assume constant $\rho=1025$kg/m^3, constant $g=9.81$m/s^2, and $p_{atm}$ related eta changes is included. 
    > v = \frac{g}{f}\frac{\partial \eta}{\partial x} + g/(f*rho_0) \int^0_z \partial rho/\partial x
    > u = -\frac{g}{f}\frac{\partial \eta}{\partial y} + g/(f*rho_0) \int^0_z \partial rho/\partial y
    

    """
    g = 9.81                  # m/s^2
    omega = 7.2921159*1E-5    # rad/s
    f = 2.*omega*np.sin(da_zos.lat/180.*np.pi)
    r_earth = 6.371*1E8       # cm
    rho_0 = 1025              # kg/m^3

    
    # calculate dz
    da_dz = da_rho.z.copy()
    da_dz.values[1:-1] = (da_rho.z[:-1].diff('z',1).values+da_rho.z[1:].diff('z',1).values)/2.
    da_dz.values[0] = (da_rho.z[1]-da_rho.z[0]).values
    da_dz.values[-1] = (da_rho.z[-1]-da_rho.z[-2]).values  # meters
    
    
    # calulate dzos in y
    dzos_dy = da_zos.copy()+np.nan
    dzos_yl = da_zos.diff('y',1,label='lower')
    dzos_yu = da_zos.diff('y',1,label='upper')
    
    dzos_dy.values[0,:] = dzos_yl.values[0,:]              # forward differences
    dzos_dy.values[1:-1,:] = (dzos_yl+dzos_yu).values      # central differences
    dzos_dy.values[-1,:] = dzos_yu.values[-1,:]            # backward differences
    
    # calulate drho in y
    drho_dy = da_rho.copy()+np.nan
    drho_yl = da_rho.diff('y',1,label='lower')
    drho_yu = da_rho.diff('y',1,label='upper')
    
    drho_dy.values[:,0,:] = drho_yl.values[:,0,:]              # forward differences
    drho_dy.values[:,1:-1,:] = (drho_yl+drho_yu).values      # central differences
    drho_dy.values[:,-1,:] = drho_yu.values[:,-1,:]            # backward differences
    
    # calculate dy 
    dy = dzos_dy.lat.copy()+np.nan
    dyl = dzos_dy.lat.diff('y',1,label='lower')
    dyu = dzos_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]                           # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values                     # central differences
    dy.values[-1,:] = dyu.values[-1,:]                         # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.                     # m
    
    # dzos/dy 
    dzos_dy = dzos_dy/da_dy                                # m/m
    
    # drho/dy
    drho_dy = drho_dy/da_dy                                # kg/m^3/m  
    int_drho_dy = (drho_dy*da_dz).cumsum(dim='z')          # kg/m^3
    
    
    # calulate dzos in x
    dzos_dx = da_zos.copy()+np.nan
    dzos_xl = da_zos.diff('x',1,label='lower')
    dzos_xr = da_zos.diff('x',1,label='upper')

    dzos_dx.values[:,0] = dzos_xl.values[:,0]              # forward differences
    dzos_dx.values[:,1:-1] = (dzos_xl+dzos_xr).values      # central differences
    dzos_dx.values[:,-1] = dzos_xr[:,-1].values            # backward differences
    
    # calulate drho in x
    drho_dx = da_rho.copy()+np.nan
    drho_xl = da_rho.diff('x',1,label='lower')
    drho_xr = da_rho.diff('x',1,label='upper')

    drho_dx.values[:,:,0] = drho_xl.values[:,:,0]              # forward differences
    drho_dx.values[:,:,1:-1] = (drho_xl+drho_xr).values      # central differences
    drho_dx.values[:,:,-1] = drho_xr[:,:,-1].values            # backward differences

    # calculate dx 
    dx = dzos_dx.lon.copy()+np.nan
    dxl = dzos_dx.lon.diff('x',1,label='lower')
    dxu = dzos_dx.lon.diff('x',1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]                           # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values                     # central differences
    dx.values[:,-1] = dxu.values[:,-1]                         # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_zos.lat/180.*np.pi)/100.     # m
    
    # dzos/dx 
    dzos_dx = dzos_dx/da_dx                                # m/m  
    
    # drho/dx 
    drho_dx = drho_dx/da_dx                                # kg/m^3/m  
    int_drho_dx = (drho_dx*da_dz).cumsum(dim='z')          # kg/m^3
    
    
    
    # mask Coriolis between -2 to 2
    if eq_mask :
        f = f.where((da_zos.lat>2.)|(da_zos.lat<-2.),other=np.nan)
    
    # geostrophic flow    
    da_geou = -g/f*dzos_dy + g/f/rho_0*int_drho_dy    # m/s
    da_geov = g/f*dzos_dx + g/f/rho_0*int_drho_dx     # m/s
    
    return da_geou, da_geov
        


    
def ekman_current(da_tauuo,da_tauvo,dep=0.,eq_mask=True):
    """
    Calculate Ekman current at each layer
    
    
    # Calculate surface Ekman transport

    The Ekman current at the surface is based on the balance of Coriolis force and eddy viscosity
    > $-fv=A_h\frac{\partial^2 u}{\partial z^2}$ \
    > $fu=A_h\frac{\partial^2 v}{\partial z^2}$

    By assuming the solution in the form of $u = ce^{kz}$
    > $u=C_0 e^{-z/d} [\tau_x cos(-\frac{z}{d}-\frac{\pi}{4})-\tau_y sin(-\frac{z}{d}-\frac{\pi}{4})]$\
    > $v=C_0 e^{-z/d} [\tau_x sin(-\frac{z}{d}-\frac{\pi}{4})+\tau_y cos(-\frac{z}{d}-\frac{\pi}{4})]$\
    > $C_0 = \frac{\sqrt{2}}{\rho f d}$,
    > $d=\sqrt{\frac{2A_z}{f}}$ (or indicated exponential scale depth)

    Surface ekman current will be when $z=0$
    
    

    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    still testing the calculation might have problem
    
    """
    dep = np.float(dep)
    sea_density = 1025.       # kg/m^3 
    omega = 7.2921159*1E-5    # rad/s
    Ah = 5E-2                 # m/s^2
    f = 2.*omega*np.sin(da_tauuo.lat/180.*np.pi)
    # d = 1./np.sqrt(np.abs(f)/(2*Ah))   # the Ekman layer depth 
    d=80.
    
    # mask Coriolis between -2 to 2
    if eq_mask:
        f = f.where((f.lat>2.)|(f.lat<-2.),other=np.nan)
 
    C_0 = np.sqrt(2)/(sea_density*np.abs(f)*d)
    da_eku = C_0*np.exp(-dep/d)*(da_tauuo*np.cos(-np.pi/4-dep/d)-da_tauvo*np.sin(-np.pi/4-dep/d)*(f/np.abs(f)))
    da_ekv = C_0*np.exp(-dep/d)*(da_tauuo*np.sin(-np.pi/4-dep/d)*(f/np.abs(f))+da_tauvo*np.cos(-np.pi/4-dep/d))    
     
    return da_eku,da_ekv    


def ekman_transport(da_tauuo,da_tauvo,eq_mask=True):
    """
    Calculate Ekman layer integrated transport 
    
    # Calculate the Ekman transport
    Wind stress tauu ($\tau_x$) and tauv ($\tau_y$) are used to calculate the Ekman transport according to 
    > $V_e = -\frac{\tau_x}{\rho f}$
    >
    > $U_e = \frac{\tau_y}{\rho f}$ 

    , where $\rho$ is the average ocean density 1025kg/m^3 (average may be changed to 1027kg/m^3 at the surface) 
    and $f$ is the Coriolis parameter 

    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    sea_density = 1025.       # kg/m^3 
    omega = 7.2921159*1E-5    # rad/s
    f = 2.*omega*np.sin(da_tauuo.lat/180.*np.pi)
    
    # mask Coriolis between -2 to 2
    if eq_mask:
       f = f.where((f.lat>2.)|(f.lat<-2.),other=np.nan)
    
    da_U_ek = da_tauvo/(sea_density*f)    # m^2/s
    da_V_ek = -da_tauuo/(sea_density*f)
     
    return da_U_ek,da_V_ek


def tau_forcing(da_tauuo,da_tauvo,ekdep=50.):
    """
    Calculate surface forcing due to wind stress 
    
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    sea_density = 1025.       # kg/m^3 
    
    da_taux = da_tauuo/(sea_density)/ekdep    # m/s^2
    da_tauy = da_tauvo/(sea_density)/ekdep    # m/s^2
     
    return da_taux,da_tauy

def pgf(da_zos):
    """
    Calculate pressure gradient force
    
    """
    g = 9.81                  # m/s^2
    omega = 7.2921159*1E-5    # rad/s
    r_earth = 6.371*1E8         # cm

    
    # calulate dzos
    dzos_dy = da_zos.copy()
    dzos_yl = da_zos.diff('y',1,label='lower')
    dzos_yu = da_zos.diff('y',1,label='upper')
    
    dzos_dy.values[0,:] = dzos_yl.values[0,:]              # forward differences
    dzos_dy.values[1:-1,:] = (dzos_yl+dzos_yu).values      # central differences
    dzos_dy.values[-1,:] = dzos_yu.values[-1,:]            # backward differences
    
    # calculate dy 
    dy = dzos_dy.lat.copy()+np.nan
    dyl = dzos_dy.lat.diff('y',1,label='lower')
    dyu = dzos_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]                           # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values                     # central differences
    dy.values[-1,:] = dyu.values[-1,:]                         # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.                     # m
    
    # dz/dy 
    dzos_dy = dzos_dy/da_dy                                # m/m
    
    # calulate dzos
    dzos_dx = da_zos.copy()+np.nan
    dzos_xl = da_zos.diff('x',1,label='lower')
    dzos_xr = da_zos.diff('x',1,label='upper')

    dzos_dx.values[:,0] = dzos_xl.values[:,0]              # forward differences
    dzos_dx.values[:,1:-1] = (dzos_xl+dzos_xr).values      # central differences
    dzos_dx.values[:,-1] = dzos_xr[:,-1].values            # backward differences

    # calculate dx 
    dx = dzos_dx.lon.copy()+np.nan
    dxl = dzos_dx.lon.diff('x',1,label='lower')
    dxu = dzos_dx.lon.diff('x',1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]                           # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values                     # central differences
    dx.values[:,-1] = dxu.values[:,-1]                         # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_zos.lat/180.*np.pi)/100.     # m
    
    # dz/dx 
    dzos_dx = dzos_dx/da_dx                                # m/m  
    
    # geostrophic flow    
    da_pgfx = -g*dzos_dx     # m/s^2
    da_pgfy = -g*dzos_dy     # m/s^2
    
    return da_pgfx, da_pgfy


def pgf_inc_density(da_zos,da_rho,ekdep=50.):
    """
    Calculate pressure gradient force including the density changes
    with in the Ekman layer
    
    """
    omega = 7.2921159*1E-5    # rad/s
    rho_0 = 1025              # kg/m^3
    r_earth = 6.371*1E8         # cm
    g = 9.81                  # m/s^2

    
    da_rho = da_rho.where(da_rho.z <= ekdep, drop=True)

    # calculate dz
    da_dz = da_rho.z.copy()
    da_dz.values[1:-1] = (da_rho.z[:-1].diff('z',1).values+da_rho.z[1:].diff('z',1).values)/2.
    da_dz.values[0] = (da_rho.z[1]-da_rho.z[0]).values
    da_dz.values[-1] = (da_rho.z[-1]-da_rho.z[-2]).values  # meters
    
    # calulate drho in y
    drho_dy = da_rho.copy()+np.nan
    drho_yl = da_rho.diff('y',1,label='lower')
    drho_yu = da_rho.diff('y',1,label='upper')
    
    drho_dy.values[:,0,:] = drho_yl.values[:,0,:]              # forward differences
    drho_dy.values[:,1:-1,:] = (drho_yl+drho_yu).values      # central differences
    drho_dy.values[:,-1,:] = drho_yu.values[:,-1,:]            # backward differences
    
    # calculate dy 
    dy = drho_dy.lat.copy()+np.nan
    dyl = drho_dy.lat.diff('y',1,label='lower')
    dyu = drho_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]                           # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values                     # central differences
    dy.values[-1,:] = dyu.values[-1,:]                         # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.                     # m
    
    # drho/dy
    drho_dy = drho_dy/da_dy                                # kg/m^3/m  
    int_drho_dy = (drho_dy*da_dz).cumsum(dim='z')             # kg/m^3
    int_drho_dy = layer_avg_single(int_drho_dy)
    
    # calulate drho in x
    drho_dx = da_rho.copy()+np.nan
    drho_xl = da_rho.diff('x',1,label='lower')
    drho_xr = da_rho.diff('x',1,label='upper')

    drho_dx.values[:,:,0] = drho_xl.values[:,:,0]              # forward differences
    drho_dx.values[:,:,1:-1] = (drho_xl+drho_xr).values        # central differences
    drho_dx.values[:,:,-1] = drho_xr[:,:,-1].values            # backward differences

    # calculate dx 
    dx = drho_dx.lon.copy()+np.nan
    dxl = drho_dx.lon.diff('x',1,label='lower')
    dxu = drho_dx.lon.diff('x',1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]                           # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values                     # central differences
    dx.values[:,-1] = dxu.values[:,-1]                         # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_zos.lat/180.*np.pi)/100.     # m
    
    # drho/dx 
    drho_dx = drho_dx/da_dx                                # kg/m^3/m  
    int_drho_dx = (drho_dx*da_dz).cumsum(dim='z')          # kg/m^3
    int_drho_dx = layer_avg_single(int_drho_dx)
    
    
    da_pgfx, da_pgfy = pgf(da_zos)

    da_pgfy = da_pgfy-g/rho_0*int_drho_dy
    da_pgfx = da_pgfx-g/rho_0*int_drho_dx
    
    return da_pgfx, da_pgfy
        
def ekman_layer_balance_LG06(da_zos,da_tauuo,da_tauvo,ekdep=50.,eq_mask=True):
    omega = 7.2921159*1E-5    # rad/s
    f = 2.*omega*np.sin(da_zos.lat/180.*np.pi)
    
    # mask Coriolis between -2 to 2
    if eq_mask :
        f = f.where((f.lat>2.)|(f.lat<-2.),other=np.nan)
    da_pgfx, da_pgfy = pgf(da_zos)
    da_taux, da_tauy = tau_forcing(da_tauuo,da_tauvo,ekdep=ekdep)
    da_u = (da_pgfy+da_tauy)/f
    da_v = -(da_pgfx+da_taux)/f
    
    return da_u, da_v
    
    
def ekman_layer_balance_Hsu(da_zos,da_rho,da_tauuo,da_tauvo,ekdep=50.,eq_mask=True):
    omega = 7.2921159*1E-5    # rad/s
    f = 2.*omega*np.sin(da_zos.lat/180.*np.pi)
    rho_0 = 1025              # kg/m^3
    r_earth = 6.371*1E8         # cm
    g = 9.81                  # m/s^2

    
    da_rho = da_rho.where(da_rho.z <= ekdep, drop=True)

    # calculate dz
    da_dz = da_rho.z.copy()
    da_dz.values[1:-1] = (da_rho.z[:-1].diff('z',1).values+da_rho.z[1:].diff('z',1).values)/2.
    da_dz.values[0] = (da_rho.z[1]-da_rho.z[0]).values
    da_dz.values[-1] = (da_rho.z[-1]-da_rho.z[-2]).values  # meters
    
    # calulate drho in y
    drho_dy = da_rho.copy()+np.nan
    drho_yl = da_rho.diff('y',1,label='lower')
    drho_yu = da_rho.diff('y',1,label='upper')
    
    drho_dy.values[:,0,:] = drho_yl.values[:,0,:]              # forward differences
    drho_dy.values[:,1:-1,:] = (drho_yl+drho_yu).values      # central differences
    drho_dy.values[:,-1,:] = drho_yu.values[:,-1,:]            # backward differences
    
    # calculate dy 
    dy = drho_dy.lat.copy()+np.nan
    dyl = drho_dy.lat.diff('y',1,label='lower')
    dyu = drho_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]                           # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values                     # central differences
    dy.values[-1,:] = dyu.values[-1,:]                         # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.                     # m
    
    # drho/dy
    drho_dy = drho_dy/da_dy                                # kg/m^3/m  
    int_drho_dy = (drho_dy*da_dz).cumsum(dim='z')             # kg/m^3
    int_drho_dy = layer_avg_single(int_drho_dy)
    
    # calulate drho in x
    drho_dx = da_rho.copy()+np.nan
    drho_xl = da_rho.diff('x',1,label='lower')
    drho_xr = da_rho.diff('x',1,label='upper')

    drho_dx.values[:,:,0] = drho_xl.values[:,:,0]              # forward differences
    drho_dx.values[:,:,1:-1] = (drho_xl+drho_xr).values        # central differences
    drho_dx.values[:,:,-1] = drho_xr[:,:,-1].values            # backward differences

    # calculate dx 
    dx = drho_dx.lon.copy()+np.nan
    dxl = drho_dx.lon.diff('x',1,label='lower')
    dxu = drho_dx.lon.diff('x',1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]                           # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values                     # central differences
    dx.values[:,-1] = dxu.values[:,-1]                         # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_zos.lat/180.*np.pi)/100.     # m
    
    # drho/dx 
    drho_dx = drho_dx/da_dx                                # kg/m^3/m  
    int_drho_dx = (drho_dx*da_dz).cumsum(dim='z')             # kg/m^3
    int_drho_dx = layer_avg_single(int_drho_dx)
    
    # mask Coriolis between -2 to 2
    if eq_mask :
        f = f.where((f.lat>2.)|(f.lat<-2.),other=np.nan)
    
    da_pgfx, da_pgfy = pgf(da_zos)
    da_taux, da_tauy = tau_forcing(da_tauuo,da_tauvo,ekdep=ekdep)
    da_u = (da_pgfy+da_tauy-g/rho_0*int_drho_dy)/f
    da_v = -(da_pgfx+da_taux-g/rho_0*int_drho_dx)/f
    

    return da_u, da_v
    

def ekman_pumping(da_curltau,eq_mask=True):
    """
    Calculate Ekman pumping based on wind stress curl
    
    # Ekman pumping 
    The Ekman pumping/suction is calculated as
    $W_E = \nabla \times \frac{\tau}{\rho f} $  
    where $\rho = 1025$ kg/m^3 and $f=2\omega \sin$(`lat`)
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    sea_density = 1025.       # kg/m^3 
    omega = 7.2921159*1E-5    # rad/s
    f = 2.*omega*np.sin(da_curltau.lat/180.*np.pi)
    
    # mask Coriolis between -2 to 2
    if eq_mask :
        f = f.where((f.lat>2.)|(f.lat<-2.),other=np.nan)
    
    da_ekw = da_curltau/(sea_density*f)    # m^2/s

    return da_ekw

def ekman_pumping2(da_tauuo,da_tauvo,eq_mask=True):
    """
    Calculate Ekman pumping based on wind stress curl
    
    # Ekman pumping 
    The Ekman pumping/suction is calculated as
    $W_E = \nabla \times \frac{\tau}{\rho f} $  
    where $\rho = 1025$ kg/m^3 and $f=2\omega \sin$(`lat`)
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    sea_density = 1025.       # kg/m^3 
    omega = 7.2921159*1E-5    # rad/s
    f = 2.*omega*np.sin(da_tauuo.lat/180.*np.pi)
    
    # mask Coriolis between -2 to 2
    if eq_mask :
        f = f.where((f.lat>2.)|(f.lat<-2.),other=np.nan)
    
    da_tauuo = da_tauuo/f/sea_density
    da_tauvo = da_tauvo/f/sea_density     # m^2/s
    da_ekw_u,da_ekw_v = curl_tau(da_tauuo,da_tauvo) 

    return da_ekw_u,da_ekw_v

def ekman_pumping2_3d_decompose(da_tauuo,da_tauvo,eq_mask=True,xname='x',yname='y'):
    """
    Calculate Ekman pumping based on wind stress curl
    
    # Ekman pumping 
    The Ekman pumping/suction is calculated as
    $W_E = \nabla \times \frac{\tau}{\rho f} $  
    where $\rho = 1025$ kg/m^3 and $f=2\omega \sin$(`lat`)
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    3. Both are 3d array with (time,y,x) 
    
    """
    sea_density = 1025.       # kg/m^3 
    omega = 7.2921159*1E-5    # rad/s
    f = 2.*omega*np.sin(da_tauuo.lat/180.*np.pi)
    
    # mask Coriolis between -2 to 2
    if eq_mask :
        f = f.where((f.lat>2.)|(f.lat<-2.),other=np.nan)
        
    da_ekw_curlwind_u,da_ekw_curlwind_v = curl_tau_3d(da_tauuo,da_tauvo,xname=xname,yname=yname)
    da_ekw_curlwind_u = da_ekw_curlwind_u/f/sea_density
    da_ekw_curlwind_v = da_ekw_curlwind_v/f/sea_density
    da_ekw_curlwind = da_ekw_curlwind_u+da_ekw_curlwind_v
    
    da_tauuo = da_tauuo/f/sea_density
    da_tauvo = da_tauvo/f/sea_density     # m^2/s
    da_ekw_u,da_ekw_v = curl_tau_3d(da_tauuo,da_tauvo,xname=xname,yname=yname) 
    
    da_ekw_zonalwind = da_ekw_u+da_ekw_v-da_ekw_curlwind
    

    return da_ekw_u,da_ekw_v,da_ekw_curlwind,da_ekw_zonalwind

def ekman_pumping2_3d(da_tauuo,da_tauvo,eq_mask=True,xname='x',yname='y'):
    """
    Calculate Ekman pumping based on wind stress curl
    
    # Ekman pumping 
    The Ekman pumping/suction is calculated as
    $W_E = \nabla \times \frac{\tau}{\rho f} $  
    where $\rho = 1025$ kg/m^3 and $f=2\omega \sin$(`lat`)
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    3. Both are 3d array with (time,y,x) 
    
    """
    sea_density = 1025.       # kg/m^3 
    omega = 7.2921159*1E-5    # rad/s
    f = 2.*omega*np.sin(da_tauuo.lat/180.*np.pi)
    
    # mask Coriolis between -2 to 2
    if eq_mask :
        f = f.where((f.lat>2.)|(f.lat<-2.),other=np.nan)
    
    da_tauuo = da_tauuo/f/sea_density
    da_tauvo = da_tauvo/f/sea_density     # m^2/s
    da_ekw_u,da_ekw_v = curl_tau_3d(da_tauuo,da_tauvo,xname=xname,yname=yname) 

    return da_ekw_u,da_ekw_v



def conv_tau(da_tauuo,da_tauvo):
    """
    Calculate wind stress convergence
    
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    r_earth = 6.371*1E8         # cm

    
    # calulate dtauu
    du_dx = da_tauuo.copy()+np.nan
    du_yl = da_tauuo.diff('y',1,label='lower')
    du_yu = da_tauuo.diff('y',1,label='upper')
    
    du_dx.values[0,:] = du_yl.values[0,:]            # forward differences
    du_dx.values[1:-1,:] = (du_yl+du_yu).values      # central differences
    du_dx.values[-1,:] = du_yu.values[-1,:]          # backward differences
    
    # calculate dx 
    dx = du_dx.lon.copy()+np.nan
    dxl = du_dx.lon.diff('x',1,label='lower')
    dxu = du_dx.lon.diff('x',1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]            # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values      # central differences
    dx.values[:,-1] = dxu.values[:,-1]          # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_tauuo.lat/180.*np.pi)/100.     # m
    
    
    # du/dx 
    du_dx = du_dx/da_dx                       # N/m^3
    
    # calulate dtauv
    dv_dy = da_tauvo.copy()+np.nan
    dv_xl = da_tauvo.diff('x',1,label='lower')
    dv_xr = da_tauvo.diff('x',1,label='upper')

    dv_dy.values[:,0] = dv_xl.values[:,0]            # forward differences
    dv_dy.values[:,1:-1] = (dv_xl+dv_xr).values      # central differences
    dv_dy.values[:,-1] = dv_xr[:,-1].values          # backward differences

    # calculate dy 
    dy = dv_dy.lat.copy()+np.nan
    dyl = dv_dy.lat.diff('y',1,label='lower')
    dyu = dv_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]            # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values      # central differences
    dy.values[-1,:] = dyu.values[-1,:]          # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.      # m
       
    
    # dv/dy 
    dv_dy = dv_dy/da_dy                       # N/m^3    
    
    conv_v = -dv_dy
    conv_u = -du_dx
     
    return conv_u, conv_v


def curl_var(da_uo,da_vo,x_name='lon',y_name='lat'):
    """
    Calculate the curl of the vector field 
    
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    r_earth = 6.371*1E8         # cm

    
    # calulate du
    du_dy = da_uo.copy()+np.nan
    du_yl = da_uo.diff(y_name,1,label='lower')
    du_yu = da_uo.diff(y_name,1,label='upper')
    
    du_dy.values[0,:] = du_yl.values[0,:]            # forward differences
    du_dy.values[1:-1,:] = (du_yl+du_yu).values      # central differences
    du_dy.values[-1,:] = du_yu.values[-1,:]          # backward differences
    
    # calculate dy 
    dy = du_dy.lat.copy()+np.nan
    dyl = du_dy.lat.diff(y_name,1,label='lower')
    dyu = du_dy.lat.diff(y_name,1,label='upper')
    
    dy.values[0] = dyl.values[0]              # forward differences
    dy.values[1:-1] = (dyl+dyu).values        # central differences
    dy.values[-1] = dyu.values[-1]            # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.      # m
    
    # du/dy 
    du_dy = du_dy/da_dy                       # N/m^3
    
    # calulate dv
    dv_dx = da_vo.copy()+np.nan
    dv_xl = da_vo.diff(x_name,1,label='lower')
    dv_xr = da_vo.diff(x_name,1,label='upper')

    dv_dx.values[:,0] = dv_xl.values[:,0]            # forward differences
    dv_dx.values[:,1:-1] = (dv_xl+dv_xr).values      # central differences
    dv_dx.values[:,-1] = dv_xr[:,-1].values          # backward differences

    # calculate dx 
    dx = dv_dx.lon.copy()+np.nan
    dxl = dv_dx.lon.diff(x_name,1,label='lower')
    dxu = dv_dx.lon.diff(x_name,1,label='upper')
    
    dx.values[0] = dxl.values[0]              # forward differences
    dx.values[1:-1] = (dxl+dxu).values        # central differences
    dx.values[-1] = dxu.values[-1]            # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_uo.lat/180.*np.pi)/100.     # m
    
    # dv/dx 
    dv_dx = dv_dx/da_dx                       # N/m^3    
    
    curl_v = dv_dx
    curl_u = -du_dy
     
    return curl_u, curl_v


def curl_tau(da_tauuo,da_tauvo,xname='x',yname='y'):
    """
    Calculate wind stress curl 
    
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    
    """
    r_earth = 6.371*1E8         # cm

    
    # calulate dtauu
    du_dy = da_tauuo.copy()+np.nan
    du_yl = da_tauuo.diff(yname,1,label='lower')
    du_yu = da_tauuo.diff(yname,1,label='upper')
    
    du_dy.values[0,:] = du_yl.values[0,:]            # forward differences
    du_dy.values[1:-1,:] = (du_yl+du_yu).values      # central differences
    du_dy.values[-1,:] = du_yu.values[-1,:]          # backward differences
    
    # calculate dy 
    dy = du_dy.lat.copy()+np.nan
    dyl = du_dy.lat.diff(yname,1,label='lower')
    dyu = du_dy.lat.diff(yname,1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]            # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values      # central differences
    dy.values[-1,:] = dyu.values[-1,:]          # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.      # m
    
    # du/dy 
    du_dy = du_dy/da_dy                       # N/m^3
    
    # calulate dtauv
    dv_dx = da_tauvo.copy()+np.nan
    dv_xl = da_tauvo.diff(xname,1,label='lower')
    dv_xr = da_tauvo.diff(xname,1,label='upper')

    dv_dx.values[:,0] = dv_xl.values[:,0]            # forward differences
    dv_dx.values[:,1:-1] = (dv_xl+dv_xr).values      # central differences
    dv_dx.values[:,-1] = dv_xr[:,-1].values          # backward differences

    # calculate dx 
    dx = dv_dx.lon.copy()+np.nan
    dxl = dv_dx.lon.diff(xname,1,label='lower')
    dxu = dv_dx.lon.diff(xname,1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]            # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values      # central differences
    dx.values[:,-1] = dxu.values[:,-1]          # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_tauuo.lat/180.*np.pi)/100.     # m
    

    # dv/dx 
    dv_dx = dv_dx/da_dx                       # N/m^3    
    
    curltau_v = dv_dx
    curltau_u = -du_dy
     
    return curltau_u, curltau_v

def curl_var_3d(da_varx,da_vary,xname='lon',yname='lat'):
    """
    Calculate wind stress curl 
    
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    3. Both are 3d array with (time,y,x) 
    
    """
    r_earth = 6.371*1E8         # cm

    
    # calulate dtauu
    du_dy = da_varx.copy()+np.nan
    du_yl = da_varx.diff(yname,1,label='lower')
    du_yu = da_varx.diff(yname,1,label='upper')
 
    du_dy.values[:,0,:] = du_yl.values[:,0,:]            # forward differences
    du_dy.values[:,1:-1,:] = (du_yl+du_yu).values      # central differences
    du_dy.values[:,-1,:] = du_yu.values[:,-1,:]          # backward differences
    
    # calculate dy 
    dy = du_dy.lat.copy()+np.nan
    dyl = du_dy.lat.diff(yname,1,label='lower')
    dyu = du_dy.lat.diff(yname,1,label='upper')
    
    dy.values[0] = dyl.values[0]            # forward differences
    dy.values[1:-1] = (dyl+dyu).values      # central differences
    dy.values[-1] = dyu.values[-1]          # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.      # m
    
    # du/dy 
    du_dy = du_dy/da_dy                       # N/m^3
    
    # calulate dtauv
    dv_dx = da_vary.copy()+np.nan
    dv_xl = da_vary.diff(xname,1,label='lower')
    dv_xr = da_vary.diff(xname,1,label='upper')

    dv_dx.values[:,:,0] = dv_xl.values[:,:,0]            # forward differences
    dv_dx.values[:,:,1:-1] = (dv_xl+dv_xr).values      # central differences
    dv_dx.values[:,:,-1] = dv_xr[:,:,-1].values          # backward differences

    # calculate dx 
    dx = dv_dx.lon.copy()+np.nan
    dxl = dv_dx.lon.diff(xname,1,label='lower')
    dxu = dv_dx.lon.diff(xname,1,label='upper')
    
    dx.values[0] = dxl.values[0]            # forward differences
    dx.values[1:-1] = (dxl+dxu).values      # central differences
    dx.values[-1] = dxu.values[-1]          # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_varx.lat/180.*np.pi)/100.     # m
    

    # dv/dx 
    dv_dx = dv_dx/da_dx                       # N/m^3    
    
    curlvar_v = dv_dx
    curlvar_u = -du_dy
     
    return curlvar_u, curlvar_v
    
    
def curl_tau_3d(da_tauuo,da_tauvo,xname='x',yname='y'):
    """
    Calculate wind stress curl 
    
    
    Make sure 
    
    1. two Arrays are already regrid to the tracer points
    2. two Arrays have the same dimensions and grid points
    3. Both are 3d array with (time,y,x) 
    
    """
    r_earth = 6.371*1E8         # cm

    
    # calulate dtauu
    du_dy = da_tauuo.copy()+np.nan
    du_yl = da_tauuo.diff(yname,1,label='lower')
    du_yu = da_tauuo.diff(yname,1,label='upper')
 
    du_dy.values[:,0,:] = du_yl.values[:,0,:]            # forward differences
    du_dy.values[:,1:-1,:] = (du_yl+du_yu).values      # central differences
    du_dy.values[:,-1,:] = du_yu.values[:,-1,:]          # backward differences
    
    # calculate dy 
    dy = du_dy.lat.copy()+np.nan
    dyl = du_dy.lat.diff(yname,1,label='lower')
    dyu = du_dy.lat.diff(yname,1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]            # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values      # central differences
    dy.values[-1,:] = dyu.values[-1,:]          # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.      # m
    
    # du/dy 
    du_dy = du_dy/da_dy                       # N/m^3
    
    # calulate dtauv
    dv_dx = da_tauvo.copy()+np.nan
    dv_xl = da_tauvo.diff(xname,1,label='lower')
    dv_xr = da_tauvo.diff(xname,1,label='upper')

    dv_dx.values[:,:,0] = dv_xl.values[:,:,0]            # forward differences
    dv_dx.values[:,:,1:-1] = (dv_xl+dv_xr).values      # central differences
    dv_dx.values[:,:,-1] = dv_xr[:,:,-1].values          # backward differences

    # calculate dx 
    dx = dv_dx.lon.copy()+np.nan
    dxl = dv_dx.lon.diff(xname,1,label='lower')
    dxu = dv_dx.lon.diff(xname,1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]            # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values      # central differences
    dx.values[:,-1] = dxu.values[:,-1]          # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_tauuo.lat/180.*np.pi)/100.     # m
    
    # dv/dx 
    dv_dx = dv_dx/da_dx                       # N/m^3    
    
    curltau_v = dv_dx
    curltau_u = -du_dy
     
    return curltau_u, curltau_v
    
    
def merid_stream_func(da_var,da_mask=None):
    """
    Calculate the meridional stream function based on zonal mean v
    
    """
    r_earth = 6.371*1E8         # cm
    if da_mask is not None:
        da_var = da_var*da_mask
#         da_var = da_var.where(da_var.notnull(),drop=True)
    
    # calculate dx 
    dx = da_var.lon.copy()+np.nan
    dxl = da_var.lon.diff('x',1,label='lower')
    dxu = da_var.lon.diff('x',1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]            # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values/2.     # central differences
    dx.values[:,-1] = dxu.values[:,-1]          # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_var.lat/180.*np.pi)/100.     # meters
    
    # calculate dz
    da_dz = da_var.z.copy()
    da_dz.values[1:-1] = (da_var.z[:-1].diff('z',1).values+da_var.z[1:].diff('z',1).values)/2.
    da_dz.values[0] = (da_var.z[1]-da_var.z[0]).values
    da_dz.values[-1] = (da_var.z[-1]-da_var.z[-2]).values  # meters
    
#     da_min_count = da_var.isel(z=0).count(dim='x')*1/3
    
    da_zonal = (da_var*da_dx).sum(dim='x')#,min_count=da_min_count.values)
    da_stream = (da_zonal*da_dz).cumsum(dim='z')#,skipna=False)  # m^2/s
    
    return  da_stream


def layer_avg(da_uo,da_vo,dep_ind=4):
    da_uo = da_uo.isel(z=np.arange(dep_ind+1,dtype=int))
    da_vo = da_vo.isel(z=np.arange(dep_ind+1,dtype=int))
    
    dz = da_vo.z.copy()
    dz.values[1:] = da_vo.z.diff(dim='z').values
    
    da_uo_avg = (da_uo*dz).sum(dim='z')/dz.z[-1].values
    da_vo_avg = (da_vo*dz).sum(dim='z')/dz.z[-1].values
    
    return da_uo_avg,da_vo_avg


def layer_avg_single(da_var):

    dz = da_var.z.copy()
    dz.values[1:] = da_var.z.diff(dim='z').values
    
    da_var_avg = (da_var*dz).sum(dim='z')/dz.z[-1].values
    
    return da_var_avg

def layer_avg_cdiff(da_var,dep_ind=4):
    """
    Calculate the depth average of any variable with z dimensions.
    
    Updated from the previous two function. 
    The dz array is calculated using central difference 
    to increase the accuracy of the numerical method 
    
    """
    
    da_var = da_var.isel(z=np.arange(dep_ind+1,dtype=int))

    # calculate dz
    da_dz = da_var.z.copy()
    da_dz.values[1:-1] = (da_var.z[:-1].diff('z',1).values+da_var.z[1:].diff('z',1).values)/2.
    da_dz.values[0] = (da_var.z[1]-da_var.z[0]).values
    da_dz.values[-1] = (da_var.z[-1]-da_var.z[-2]).values  # meters

    da_var_avg = (da_var*da_dz).sum(dim='z')/da_dz.z[-1].values
    
    return da_var_avg


def heat_advection(da_uo,da_vo,da_thetao):
    """
    Calculate the heat advection in x and y direction
    
    """
    r_earth = 6.371*1E8         # cm
    
    # calulate dthetao in x
    dthetao_dx = da_thetao.copy()+np.nan
    dthetao_xl = da_thetao.diff('x',1,label='lower')
    dthetao_xr = da_thetao.diff('x',1,label='upper')

    dthetao_dx.values[:,:,0] = dthetao_xl.values[:,:,0]              # forward differences
    dthetao_dx.values[:,:,1:-1] = (dthetao_xl+dthetao_xr).values        # central differences
    dthetao_dx.values[:,:,-1] = dthetao_xr[:,:,-1].values            # backward differences

    # calculate dx 
    dx = dthetao_dx.lon.copy()+np.nan
    dxl = dthetao_dx.lon.diff('x',1,label='lower')
    dxu = dthetao_dx.lon.diff('x',1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]                           # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values                     # central differences
    dx.values[:,-1] = dxu.values[:,-1]                         # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_thetao.lat/180.*np.pi)/100.     # m
    
    # dthetao/dx 
    dthetao_dx = dthetao_dx/da_dx                                # K/m  

    
    # calulate dthetao in y
    dthetao_dy = da_thetao.copy()+np.nan
    dthetao_yl = da_thetao.diff('y',1,label='lower')
    dthetao_yu = da_thetao.diff('y',1,label='upper')
    
    dthetao_dy.values[:,0,:] = dthetao_yl.values[:,0,:]              # forward differences
    dthetao_dy.values[:,1:-1,:] = (dthetao_yl+dthetao_yu).values      # central differences
    dthetao_dy.values[:,-1,:] = dthetao_yu.values[:,-1,:]            # backward differences
    
    # calculate dy 
    dy = dthetao_dy.lat.copy()+np.nan
    dyl = dthetao_dy.lat.diff('y',1,label='lower')
    dyu = dthetao_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]                           # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values                     # central differences
    dy.values[-1,:] = dyu.values[-1,:]                         # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.                     # m
    
    # drho/dy
    dthetao_dy = dthetao_dy/da_dy                                # K/m  
    
    

    da_ut = -dthetao_dx*da_uo
    da_vt = -dthetao_dy*da_vo
    
    
    
    

    return da_ut, da_vt,dthetao_dx,dthetao_dy
    

def gradient_x_y_2d(da_var):
    """
    Calculate the 2-dimensional gradient of 2D variables
    
    """
    r_earth = 6.371*1E8         # cm

    
    # calulate dvar_y
    dvar_dy = da_var.copy()+np.nan
    dvar_yl = da_var.diff('y',1,label='lower')
    dvar_yu = da_var.diff('y',1,label='upper')
    
    dvar_dy.values[0,:] = dvar_yl.values[0,:]              # forward differences
    dvar_dy.values[1:-1,:] = (dvar_yl+dvar_yu).values      # central differences
    dvar_dy.values[-1,:] = dvar_yu.values[-1,:]            # backward differences
    
    # calculate dy 
    dy = dvar_dy.lat.copy()+np.nan
    dyl = dvar_dy.lat.diff('y',1,label='lower')
    dyu = dvar_dy.lat.diff('y',1,label='upper')
    
    dy.values[0,:] = dyl.values[0,:]                       # forward differences
    dy.values[1:-1,:] = (dyl+dyu).values                   # central differences
    dy.values[-1,:] = dyu.values[-1,:]                     # backward differences  
    da_dy = dy/180.*np.pi*r_earth/100.                     # m
    
    # dvar/dy 
    dvar_dy = dvar_dy/da_dy                                # var_unit/m
    
    # calulate dvar_x
    dvar_dx = da_var.copy()+np.nan
    dvar_xl = da_var.diff('x',1,label='lower')
    dvar_xr = da_var.diff('x',1,label='upper')

    dvar_dx.values[:,0] = dvar_xl.values[:,0]              # forward differences
    dvar_dx.values[:,1:-1] = (dvar_xl+dvar_xr).values      # central differences
    dvar_dx.values[:,-1] = dvar_xr[:,-1].values            # backward differences

    # calculate dx 
    dx = dvar_dx.lon.copy()+np.nan
    dxl = dvar_dx.lon.diff('x',1,label='lower')
    dxu = dvar_dx.lon.diff('x',1,label='upper')
    
    dx.values[:,0] = dxl.values[:,0]                       # forward differences
    dx.values[:,1:-1] = (dxl+dxu).values                   # central differences
    dx.values[:,-1] = dxu.values[:,-1]                     # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(da_var.lat/180.*np.pi)/100.     # m
    

    # dvar/dx 
    dvar_dx = dvar_dx/da_dx                                # var_unit/m   

     
    return dvar_dx, dvar_dy

def zonalband_gradient_x(da_var,lat):
    """
    Calculate the 1-dimensional gradient of in x direction variables
    
    """
    r_earth = 6.371*1E8         # cm
    
    # calulate dvar_x
    dvar_dx = da_var.copy()+np.nan
    dvar_xl = da_var.diff('x',1,label='lower')
    dvar_xr = da_var.diff('x',1,label='upper')

    dvar_dx.values[:,0] = dvar_xl.values[:,0]              # forward differences
    dvar_dx.values[:,1:-1] = (dvar_xl+dvar_xr).values      # central differences
    dvar_dx.values[:,-1] = dvar_xr[:,-1].values            # backward differences

    # calculate dx 
    dx = dvar_dx.x.copy()+np.nan
    dxl = dvar_dx.x.diff('x',1,label='lower')
    dxu = dvar_dx.x.diff('x',1,label='upper')
    
    dx.values[0] = dxl.values[0]                       # forward differences
    dx.values[1:-1] = (dxl+dxu).values                   # central differences
    dx.values[-1] = dxu.values[-1]                     # backward differences  
    da_dx = dx/180.*np.pi*r_earth*np.cos(lat/180.*np.pi)/100.     # m
    

    # dvar/dx 
    dvar_dx = dvar_dx/da_dx                                # var_unit/m   

     
    return dvar_dx