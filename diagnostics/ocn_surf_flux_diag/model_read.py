import xarray as xr
import numpy as np
import metpy.calc
from metpy.units import units

def regional_var(varlist, lon_lim, lat_lim, year_lim):
    """
    The model io for needed variables and crop based on the 
    region and period of interest.
    
    Varlist needs to include atmosphere model variables
    1. 'huss'    : Surface 2m Humidity (kg kg-1)
    2. 'ts'      : Skin Temperature (SST for open ocean; K)
    3. 'sfcWind' : Near-Surface Wind Speed (10 meter; m s-1)
    4. 'psl'     : Sea Level Pressure (Pa)
    5. 'hfls'    : Surface Upward Latent Heat Flux (W m-2 and positive upward)
    6. 'pr'      : Precipitation (kg m-2 s-1)
    If there are more needed model variables, user can manually 
    add variable in the varlist.

    The io function also calculate the 
        1. surface saturated specific humidity (qsurf)
        2. specific humidity difference between qsurf and huss (del_q)

    To accomplish the calculation of qsurf
        - ts (surface temperature)
        - psl (sea level pressure)
    are nesessary variables in this model io. 

    Inputs:
    =================
    varlist (list) : a list object containing all the file locations.
                     
    lon_lim (list) : a list object containing the min and max value of 
                     longitude of the desired region.

    lat_lim (list) : a list object containing the min and max value of 
                     latitude of the desired region.
    
    year_lim (list) : a list object containing the min and max value of 
                     year of the desired period.


    Outputs:
    =================
    ds_atm_regional (xr.Dataset) : a xarray dataset including all variables

    """

    
    for nvar,var in enumerate(varlist):
        ds_temp = xr.open_mfdataset(varlist[nvar])
        
        if nvar == 0:
            ds_atm = ds_temp.copy()
        else:
            ds_atm = xr.merge([ds_atm,ds_temp],compat='override')
    
    ###########################################################################
    # cropping dataset

    ds_atm_regional = ((ds_atm).where(
                           (ds_atm.lon>=np.array(lon_lim).min())&
                           (ds_atm.lon<=np.array(lon_lim).max())&
                           (ds_atm.lat>=np.array(lat_lim).min())&
                           (ds_atm.lat<=np.array(lat_lim).max())&
                           (ds_atm['time.year']>=np.array(year_lim).min())&
                           (ds_atm['time.year']<=np.array(year_lim).max()),
                           drop=True)
                      )

    ###########################################################################
    # # Calculate $\Delta$q
    #
    # $\delta$ q is the specific humidity difference between
    # saturation q near surface determined by SST and 2m(3m) q.
    # - To calculate the q near surface, I use the slp and dewpoint
    #    assuming the same as SST.
    # - To calculate the q at 2m, I use the RH at 2m, T at 1m, and
    #    slp to determine the mix ratio and then the specific humidity

    da_q_surf = ds_atm_regional['huss'].copy()*np.nan

    mixing_ratio_surf = (metpy.calc.saturation_mixing_ratio(
                                ds_atm_regional['psl'].values*units.Pa,
                                ds_atm_regional['ts'].values*units.K)
                        )
    q_surf = metpy.calc.specific_humidity_from_mixing_ratio(mixing_ratio_surf)

    # unit for mixing ratio and specific humidity is kg/kg
    da_q_surf.values = q_surf.magnitude
    ds_atm_regional['qsurf'] = da_q_surf
    ds_atm_regional['del_q'] = 0.98*ds_atm_regional['qsurf']-ds_atm_regional['huss']
    ds_atm_regional['del_q'] = ds_atm_regional['del_q']*1e3   # kg/kg => g/kg

    return ds_atm_regional
