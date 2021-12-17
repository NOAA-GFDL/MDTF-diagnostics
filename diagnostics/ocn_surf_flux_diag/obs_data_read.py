import os
import metpy.calc
import numpy as np
import xarray as xr
from metpy.units import units


def tao_triton(obs_data_dir,lon_lim,lat_lim,year_lim=None):
    """
    The observational data io for latent heat flux corrections. 
    If there are more needed model variables, a manual 
    added variable in the setting section is available.
    
    The TAO/TRITON daily observation is downloaded from 
    https://www.pmel.noaa.gov/tao/drupal/flux/index.html. 
    The year limit argument is to let the user 
    to set their time period based on different analysis period.
    
    
    The io function also calculate the 
        1. surface saturated specific humidity (qsurf)
        2. specific humidity difference between qsurf and huss (del_q)
    
    To acomplish the calculation of qsurf
        - ts (surface temperature)
        - psl (sea level pressure)
    are nesessary variables in this model io. 
    
    Inputs:
    =================
    lon_lim (list) : a list object containing the min and max value of 
                     longitude of the desired region.
                     
    lat_lim (list) : a list object containing the min and max value of 
                     latitude of the desired region.
                     
    year_lim (list) : a list object containing the min and max value of 
                     year of the desired period. Default is None, which 
                     means all available data will be used.
                     
                     
    Outputs:
    =================
    ds_all_ts (xr.Dataset) : a xarray dataset in the form of dask array 
                     
    
    """

    # original variable name for dir name
    dirlist = ['WindSpeed10m','SST','RH','Latent','airT','SLP']

    # original variable name for file name
    varlist = ['wzs','sst','rh','qlat','airt','bp']

    # original variable name in netcdf
    varname = ['WZS_2401','T_25','RH_910','QL_137','AT_21','BP_915']

    var_file_dict = {}
    for nvar,var in enumerate(varlist):
        var_file = []
        location = []
        files = os.listdir(os.path.join(obs_data_dir,dirlist[nvar],'daily'))
        for file in files:
            if file.startswith(var) and file.endswith('_dy.cdf'):
                startlen = len(var)
                endlen = len('_dy.cdf')
                loc = file[startlen:-endlen]

                lat_index = loc.find('n')
                if lat_index == -1 :
                    lat_index = loc.find('s')            

                # latitude
                if loc[lat_index] in ['n']:
                    lat_loc = np.float(loc[:lat_index])
                else :
                    lat_loc = -np.float(loc[:lat_index])

                # longitude
                if loc[-1] in ['e']:
                    lon_loc = np.float(loc[lat_index+1:-1])
                else:
                    lon_loc = -np.float(loc[lat_index+1:-1])+360.

                # make sure station in the region limit
                if lon_loc >= np.array(lon_lim).min() and lon_loc <= np.array(lon_lim).max():
                    if lat_loc >= np.array(lat_lim).min() and lat_loc <= np.array(lat_lim).max():
                        var_file.append(loc)
        var_file_dict[var] = var_file


    # pick only overlapping stations
    for nvar,var in enumerate(varlist):
        if nvar == 0:
            final_list = var_file_dict[var]
        else:
            final_list = list(set(final_list) & set(var_file_dict[var]))  

    stn_locs = final_list   

    ds_mlist = {}
    print('TAO/TRITON stations:')
    for stn_loc in stn_locs:
        data_files = []
        for nvar,var in enumerate(varlist):
            path = os.path.join(obs_data_dir,dirlist[nvar],'daily')
            file = var+stn_loc+'_dy.cdf'
            data_files.append(os.path.join(path,file))
        try :
            ds_list = [xr.open_dataset(file) for file in data_files]
            ds_mlist[stn_loc] = ds_list
            print("%s included"%stn_loc)
        except FileNotFoundError:
            print('%s not enough data'%stn_loc)



    ### clean fill_value
    for stn_loc in stn_locs:
        for nvar,var in enumerate(varname):
            ds_mlist[stn_loc][nvar][var] = ds_mlist[stn_loc][nvar][var]\
                        .where(ds_mlist[stn_loc][nvar][var] != 1e35,other=np.nan)


    # # Calculate $\Delta$q
    #
    # $\delta$ q is the specific humidity difference between
    #   saturation q near surface determined by SST and 2m(3m) q.
    #
    # - To calculate the q near surface, I use the slp and dewpoint
    #    assuming the same as SST.
    # - To calculate the q at 2m, I use the RH at 2m, T at 1m, and
    #    slp to determine the mix ratio and then the specific humidity
    #


    for stn_loc in stn_locs:
        temp_list = [ds_mlist[stn_loc][nvar][varname[nvar]].squeeze() for nvar in range(len(varname))]

        ds_merge = xr.merge(temp_list,compat='override')

        for nvar in range(len(varlist)):
            ds_merge = ds_merge.rename_vars({varname[nvar]:varlist[nvar]})


        # calculate 2m specific humidity
        mixing_ratio = metpy.calc.mixing_ratio_from_relative_humidity(
                        ds_merge['bp'].values*units.hPa,
                        ds_merge['airt'].values*units.degC,
                        ds_merge['rh'].values*0.01
                        )
        q_2m = metpy.calc.specific_humidity_from_mixing_ratio(mixing_ratio)

        # calculate surface saturated specific humidity
        mixing_ratio_surf= metpy.calc.saturation_mixing_ratio(
                             ds_merge['bp'].values*units.hPa,
                             (ds_merge['sst'].values-0.2)*units.degC)
        q_surf = metpy.calc.specific_humidity_from_mixing_ratio(mixing_ratio_surf)

        # calculate del q
        del_q = 0.98*q_surf-q_2m

        # initialization of xr.DataArray
        da_q_2m = ds_merge['sst']*np.nan
        da_q_surf = da_q_2m.copy()
        da_del_q = da_q_2m.copy()

        # unit for mixing ratio and specific humidity is kg/kg
        da_q_2m[:] = q_2m.magnitude
        da_q_surf[:] = q_surf.magnitude
        da_del_q[:] = del_q.magnitude

        ds_merge['Q2m'] = da_q_2m
        ds_merge['Qsurf'] = da_q_surf
        ds_merge['dQ'] = da_del_q

        ds_mlist[stn_loc] = ds_merge
        
    # crop time period
    if year_lim is not None:
        for nstn,stn_loc in enumerate(stn_locs):
            ds_mlist[stn_loc] = ds_mlist[stn_loc].where(
                       (ds_mlist[stn_loc]['time.year']>=np.array(year_lim).min())&
                       (ds_mlist[stn_loc]['time.year']<=np.array(year_lim).max()),
                       drop=True)
        


    # stack all station
    for nstn,stn_loc in enumerate(stn_locs):
        if nstn == 0:
            ds_merge = ds_mlist[stn_loc]
        else:
            ds_merge=xr.concat([ds_merge,ds_mlist[stn_loc]],dim='stn')
            
    if len(stn_locs) == 1:
        ds_merge = ds_merge
    else: 
        ds_merge = ds_merge.stack(allstn=('stn','time'))
    
    location = []
    for loc in stn_locs:
        lat_index = loc.find('n')
        if lat_index == -1 :
            lat_index = loc.find('s')            

        # latitude
        if loc[lat_index] in ['n']:
            lat_loc = np.float(loc[:lat_index])
        else :
            lat_loc = -np.float(loc[:lat_index])

        # longitude
        if loc[-1] in ['e']:
            lon_loc = np.float(loc[lat_index+1:-1])
        else:
            lon_loc = -np.float(loc[lat_index+1:-1])+360.
            
        location.append([lon_loc,lat_loc])
    
    # change varname to be consistent with model
    ds_merge = ds_merge.rename({'wzs':'sfcWind','dQ':'del_q','qlat':'hfls'})

    # change dq unit from kg/kg to g/kg
    ds_merge['del_q'] = ds_merge['del_q']*1e3
    
    return ds_merge,location



def rama(obs_data_dir,lon_lim,lat_lim,year_lim=None):
    """
    The observational data io for latent heat flux corrections. 
    If there are more needed model variables, a manual 
    added variable in the setting section is available.
    
    The RAMA daily observation is downloaded from 
    https://www.pmel.noaa.gov/tao/drupal/flux/index.html. 
    The year limit argument is to let the user 
    to set their time period based on different analysis period.
    
    
    The io function also calculate the 
        1. surface saturated specific humidity (qsurf)
        2. specific humidity difference between qsurf and huss (del_q)
    
    To acomplish the calculation of qsurf
        - ts (surface temperature)
        - psl (sea level pressure)
    are nesessary variables in this model io. 
    
    Inputs:
    =================
    lon_lim (list) : a list object containing the min and max value of 
                     longitude of the desired region.
                     
    lat_lim (list) : a list object containing the min and max value of 
                     latitude of the desired region.
                     
    year_lim (list) : a list object containing the min and max value of 
                     year of the desired period. Default is None, which 
                     means all available data will be used.
                     
                     
    Outputs:
    =================
    ds_all_ts (xr.Dataset) : a xarray dataset in the form of dask array 
                     
    
    """

    # original variable name for dir name
    dirlist = ['WindSpeed10m','SST','RH','Latent','airT','SLP']

    # original variable name for file name
    varlist = ['wzs','sst','rh','qlat','airt','bp']

    # original variable name in netcdf
    varname = ['WZS_2401','T_25','RH_910','QL_137','AT_21','BP_915']

    var_file_dict = {}
    for nvar,var in enumerate(varlist):
        var_file = []
        location = []
        files = os.listdir(os.path.join(obs_data_dir,dirlist[nvar],'daily'))
        for file in files:
            if file.startswith(var) and file.endswith('_dy.cdf'):
                startlen = len(var)
                endlen = len('_dy.cdf')
                loc = file[startlen:-endlen]

                lat_index = loc.find('n')
                if lat_index == -1 :
                    lat_index = loc.find('s')            

                # latitude
                if loc[lat_index] in ['n']:
                    lat_loc = np.float(loc[:lat_index])
                else :
                    lat_loc = -np.float(loc[:lat_index])

                # longitude
                if loc[-1] in ['e']:
                    lon_loc = np.float(loc[lat_index+1:-1])
                else:
                    lon_loc = -np.float(loc[lat_index+1:-1])+360.

                # make sure station in the region limit
                if lon_loc >= np.array(lon_lim).min() and lon_loc <= np.array(lon_lim).max():
                    if lat_loc >= np.array(lat_lim).min() and lat_loc <= np.array(lat_lim).max():
                        var_file.append(loc)
        var_file_dict[var] = var_file


    # pick only overlapping stations
    for nvar,var in enumerate(varlist):
        if nvar == 0:
            final_list = var_file_dict[var]
        else:
            final_list = list(set(final_list) & set(var_file_dict[var]))  

    stn_locs = final_list   

    ds_mlist = {}
    print('RAMA stations:')
    for stn_loc in stn_locs:
        data_files = []
        for nvar,var in enumerate(varlist):
            path = os.path.join(obs_data_dir,dirlist[nvar],'daily')
            file = var+stn_loc+'_dy.cdf'
            data_files.append(os.path.join(path,file))
        try :
            ds_list = [xr.open_dataset(file) for file in data_files]
            ds_mlist[stn_loc] = ds_list
            print("%s included"%stn_loc)
        except FileNotFoundError:
            print('%s not enough data'%stn_loc)


    ### clean fill_value
    for stn_loc in stn_locs:
        for nvar,var in enumerate(varname):
            ds_mlist[stn_loc][nvar][var] = ds_mlist[stn_loc][nvar][var]\
                        .where(ds_mlist[stn_loc][nvar][var] != 1e35,other=np.nan)


    # # Calculate $\Delta$q
    #
    # $\delta$ q is the specific humidity difference between
    #   saturation q near surface determined by SST and 2m(3m) q.
    #
    # - To calculate the q near surface, I use the slp and dewpoint
    #    assuming the same as SST.
    # - To calculate the q at 2m, I use the RH at 2m, T at 1m, and
    #    slp to determine the mix ratio and then the specific humidity
    #


    for stn_loc in stn_locs:
        temp_list = [ds_mlist[stn_loc][nvar][varname[nvar]].squeeze() for nvar in range(len(varname))]

        ds_merge = xr.merge(temp_list,compat='override')

        for nvar in range(len(varlist)):
            ds_merge = ds_merge.rename_vars({varname[nvar]:varlist[nvar]})


        # calculate 2m specific humidity
        mixing_ratio = metpy.calc.mixing_ratio_from_relative_humidity(
                        ds_merge['bp'].values*units.hPa,
                        ds_merge['airt'].values*units.degC,
                        ds_merge['rh'].values*0.01
                        )
        q_2m = metpy.calc.specific_humidity_from_mixing_ratio(mixing_ratio)

        # calculate surface saturated specific humidity
        mixing_ratio_surf= metpy.calc.saturation_mixing_ratio(
                             ds_merge['bp'].values*units.hPa,
                             (ds_merge['sst'].values-0.2)*units.degC)
        q_surf = metpy.calc.specific_humidity_from_mixing_ratio(mixing_ratio_surf)

        # calculate del q
        del_q = 0.98*q_surf-q_2m

        # initialization of xr.DataArray
        da_q_2m = ds_merge['sst']*np.nan
        da_q_surf = da_q_2m.copy()
        da_del_q = da_q_2m.copy()

        # unit for mixing ratio and specific humidity is kg/kg
        da_q_2m[:] = q_2m.magnitude
        da_q_surf[:] = q_surf.magnitude
        da_del_q[:] = del_q.magnitude

        ds_merge['Q2m'] = da_q_2m
        ds_merge['Qsurf'] = da_q_surf
        ds_merge['dQ'] = da_del_q

        ds_mlist[stn_loc] = ds_merge
        
    # crop time period
    if year_lim is not None:
        for nstn,stn_loc in enumerate(stn_locs):
            ds_mlist[stn_loc] = ds_mlist[stn_loc].where(
                       (ds_mlist[stn_loc]['time.year']>=np.array(year_lim).min())&
                       (ds_mlist[stn_loc]['time.year']<=np.array(year_lim).max()),
                       drop=True)
        


    # stack all station
    for nstn,stn_loc in enumerate(stn_locs):
        if nstn == 0:
            ds_merge = ds_mlist[stn_loc]
        else:
            ds_merge=xr.concat([ds_merge,ds_mlist[stn_loc]],dim='stn')
    ds_merge = ds_merge.stack(allstn=('stn','time'))
    
    location = []
    for loc in stn_locs:
        lat_index = loc.find('n')
        if lat_index == -1 :
            lat_index = loc.find('s')            

        # latitude
        if loc[lat_index] in ['n']:
            lat_loc = np.float(loc[:lat_index])
        else :
            lat_loc = -np.float(loc[:lat_index])

        # longitude
        if loc[-1] in ['e']:
            lon_loc = np.float(loc[lat_index+1:-1])
        else:
            lon_loc = -np.float(loc[lat_index+1:-1])+360.
            
        location.append([lon_loc,lat_loc])
        
    # change varname to be consistent with model
    ds_merge = ds_merge.rename({'wzs':'sfcWind','dQ':'del_q','qlat':'hfls'})

    # change dq unit from kg/kg to g/kg
    ds_merge['del_q'] = ds_merge['del_q']*1e3
    
    
    return ds_merge,location
