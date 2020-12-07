#!/usr/bin/env python
# coding: utf-8

# # MDTF tool
#
#
# The script generate the tropical Pacific dynamic sea level
# and wind stress curl scatter plots at different time scale
# due to their strong dependency from Ekman pumping/suction
# and barotropic response over the ocean
#
# input files
# ============
# Ocean model : tauuo, tauvo, zos
#
#
# function used
# ==================
# - spherical_area.da_area     : generate area array based on the lon lat of data
# - dynamical_balance2.curl_var_3d : calculate wind stress curl in obs (for Dataset with time dim)
# - dynamical_balance2.curl_var    : calculate wind stress curl in obs (for Dataset without time dim)
# - dynamical_balance2.curl_tau_3d : calculate wind stress curl in model (for Dataset with time dim)
# - dynamical_balance2.curl_tau    : calculate wind stress curl in model (for Dataset without time dim)
# - xr_ufunc.da_linregress : linregress for Dataset with time dim
#


import os
import cftime
# import dask
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

import spherical_area as sa
from xr_ufunc import da_linregress
from dynamical_balance2 import curl_tau, curl_tau_3d
from dynamical_balance2 import curl_var, curl_var_3d

# from dask.distributed import Client
# client = Client(n_workers=1, threads_per_worker=8, processes=False)
# client


import warnings
warnings.simplefilter("ignore")

# from mem_track import used_memory
# used_memory()


# #### possible input info from external text file
# # constant setting
# syear = 1993                 # crop model and obs data from year
# fyear = 2009                 # crop model and obs data to year
# tp_lat_region = [-30,30]     # extract model till latitude

# # regional average box
# lon_range_list = [120,150]   # 0-360
# lat_range_list = [10,20]

# # Model label
# Model_name = ['CESM2_CORE']        # model name in the dictionary
# Model_legend_name = ['CESM2-CORE'] # model name appeared on the plot legend



# # initialization
# modelin = {}
# path = {}
# #####################
# ori_syear = 1948
# ori_fyear = 2009
# modeldir = os.getenv('MODEL_DATA_ROOT')+'/CESM2_omip1_r1i1p1f1_gn/mon/'
# modelfile = [['CESM2_omip1_r1i1p1f1_gn.tauuo.mon.nc'],
#              ['CESM2_omip1_r1i1p1f1_gn.tauvo.mon.nc'],
#              ['CESM2_omip1_r1i1p1f1_gn.zos.mon.nc']]
# areafile = 'CESM2_omip1_r1i1p1f1_gn.areacello.mon.nc'
# path[Model_name[0]]=[modeldir,modelfile]

# Model_varname = ['tauuo','tauvo','zos']
# Model_dimname = ['time','nlat','nlon']
# Model_coordname = ['lat','lon']

# xname = Model_dimname[2]
# yname = Model_dimname[1]

print('--------------------------')
print('Start reading set parameter (pod_env_vars)')
print('--------------------------')
# print(str(os.getenv('OBS_DATA')))
#### possible input info from external text file
# constant setting
syear = np.int(os.getenv('syear'))                 # crop model and obs data from year
fyear = np.int(os.getenv('fyear'))                  # crop model and obs data to year
tp_lat_region = [-30,30]                 # extract model till latitude

# regional average box
lon_range_list = [np.float(os.getenv('lon_min')),
                  np.float(os.getenv('lon_max'))]   # 0-360
lat_range_list = [np.float(os.getenv('lat_min')),
                  np.float(os.getenv('lat_max'))]

# Model label
Model_name = [os.getenv('Model_name')]        # model name in the dictionary
Model_legend_name = [os.getenv('Model_legend_name')] # model name appeared on the plot legend



# initialization
modelin = {}
path = {}
#####################
ori_syear = int(os.getenv('FIRSTYR'))
ori_fyear = int(os.getenv('LASTYR'))
modeldir = str(os.getenv('DATADIR'))+"/../"+str(os.getenv('Model_path'))
# print(modeldir)
modelfile = [[os.getenv('tauuo_file')],
             [os.getenv('tauvo_file')],
             [os.getenv('zos_file')]]
areafile = os.getenv('areacello_file')
path[Model_name[0]]=[modeldir,modelfile]

Model_varname = [os.getenv('tauuo_var'),os.getenv('tauvo_var'),os.getenv('zos_var')]
Model_dimname = [os.getenv('Model_dim0'),os.getenv('Model_dim1'),os.getenv('Model_dim2')]
Model_coordname = [os.getenv('Model_coord0'),os.getenv('Model_coord1')]

xname = Model_dimname[2]
yname = Model_dimname[1]




for nmodel,model in enumerate(Model_name):
    modeldir = path[model][0]
    modelfile = path[model][1]
    multivar = []
    for file in modelfile :
        if len(file) == 1 :
            multivar.append([os.path.join(modeldir,file[0])])
        elif len(file) > 1 :
            multifile = []
            for ff in file :
                multifile.append(os.path.join(modeldir,ff))
            multivar.append(multifile)
    modelin[model] = multivar

#### create time axis (datatime.datetime)
timeax = xr.cftime_range(start=cftime.datetime(ori_syear,1,1),end=cftime.datetime(ori_fyear,12,1),freq='MS')
timeax = timeax.to_datetimeindex()    # cftime => datetime64

print('--------------------------')
print('Start processing model outputs')
print('--------------------------')
# initialization of dict and list  (!!!!!!!! remove all previous read model info if exec !!!!!!!!!!)
nmodel = len(Model_name)
nvar = len(Model_varname)

ds_model_mlist = {}
mean_mlist = {}
season_mlist = {}
linear_mlist = {}
#### models
for nmodel,model in enumerate(Model_name):
    ds_model_list = {}
    mean_list = {}
    season_list = {}
    linear_list = {}
    for nvar,var in enumerate(Model_varname):
        print('read %s %s'%(model,var))

#         # read input data
#         ds_model = xr.open_mfdataset(modelin[model][nvar],
#                                      chunks={Model_dimname[0]:100,
#                                              Model_dimname[1]:100,
#                                              Model_dimname[2]:100},
#                                      use_cftime=True)
        print(modelin[model][nvar][0])
        # read input data
        ds_model = xr.open_dataset(modelin[model][nvar][0],use_cftime=True)


        # crop data (time)
        ds_model['time'] = timeax
        da_model = ds_model[var].where((ds_model['time.year'] >= syear)&
                                       (ds_model['time.year'] <= fyear)
                                       ,drop=True)
        # crop data (space)
        da_model = da_model.where((ds_model.lat >= np.min(np.array(tp_lat_region)))&
                                  (ds_model.lat <= np.max(np.array(tp_lat_region)))
                                  ,drop=True)

        # remove land value
        da_model['lon'] = da_model.lon.where(da_model.lon<1000.,other=np.nan)
        da_model['lat'] = da_model.lat.where(da_model.lat<1000.,other=np.nan)

        # store all model data
        ds_model_list[var] = da_model

        # calculate mean
        mean_list[var] = ds_model_list[var].mean(dim='time').compute()
        ds_model_list[var] = ds_model_list[var]-mean_list[var]

        # calculate seasonality
        season_list[var] = ds_model_list[var].groupby('time.month').mean(dim='time').compute()
        ds_model_list[var] = ds_model_list[var].groupby('time.month')-season_list[var]

        # remove linear trend
        linear_list[var] = da_linregress(ds_model_list[var],stTconfint=0.99)

    linear_mlist[model] = linear_list
    mean_mlist[model] = mean_list
    season_mlist[model] = season_list
    ds_model_mlist[model] = ds_model_list

#
# # detrend
# for nmodel,model in enumerate(Model_name):
#     for nvar,var in enumerate(Model_varname):
#         da_time = ds_model_mlist[model][var].time.copy()
#         year = ds_model_mlist[model][var]['time.year'].values
#         month = ds_model_mlist[model][var]['time.month'].values
#         da_time.values = year+month/12.
#         ds_model_mlist[model][var] = ds_model_mlist[model][var]-                                     (da_time*linear_mlist[model][var]['slope']+linear_mlist[model][var]['intercept'])


# # Observation
# constant setting
obs_year_range = [[1950,2011],[1993,2018,9]]
Obs_varname = [['tx','ty'],['adt']]
Obs_name = ['WASwind','CMEMS']

# inputs
obsin = {}
obspath = {}

obs = Obs_name[0]
obsdir = str(os.getenv('OBS_DATA'))
obsfile = [['waswind_v1_0_1.monthly.nc'],['waswind_v1_0_1.monthly.nc']]
obspath[obs]=[obsdir,obsfile]

obs = Obs_name[1]
obsdir = str(os.getenv('OBS_DATA'))
obsfile = [['dt_global_allsat_phy_l4_monthly_adt.nc']]
obspath[obs]=[obsdir,obsfile]


for nobs,obs in enumerate(Obs_name):
    obsdir = obspath[obs][0]
    obsfile = obspath[obs][1]
    multivar = []
    for file in obsfile :
        if len(file) == 1 :
            multivar.append([os.path.join(obsdir,file[0])])
        elif len(file) > 1 :
            multifile = []
            for ff in file :
                multifile.append(os.path.join(obsdir,ff))
            multivar.append(multifile)
    obsin[obs] = multivar


# initialization of dict and list
ds_obs_mlist = {}
obs_mean_mlist = {}
obs_season_mlist = {}
obs_linear_mlist = {}

for nobs,obs in enumerate(Obs_name):
    ds_obs_list = {}
    obs_mean_list = {}
    obs_season_list = {}
    obs_linear_list = {}
    for nvar,var in enumerate(Obs_varname[nobs]):
        print('read %s %s'%(obs,var))

        # read input data
        #-- single file
        if len(obsin[obs][nvar]) == 1 :

            # find out dimension name
            da = xr.open_dataset(obsin[obs][nvar][0])
            obsdims = list(da[var].dims)

#             ds_obs = xr.open_dataset(obsin[obs][nvar][0],chunks={obsdims[0]:50,obsdims[1]:50,obsdims[2]:50},use_cftime=True)
            ds_obs = xr.open_dataset(obsin[obs][nvar][0])

        #-- multi-file merge (same variable)
        elif len(obsin[obs][nvar]) > 1 :
            for nf,file in enumerate(obsin[obs][nvar]):
                # find out dimension name
                da = xr.open_dataset(file,chunks={})
                obsdims = list(da[var].dims)

#                 ds_obs_sub = xr.open_dataset(file,chunks={obsdims[0]:50,obsdims[1]:50,obsdims[2]:50},use_cftime=True)
                ds_obs_sub = xr.open_dataset(file,use_cftime=True)
                if nf == 0 :
                    ds_obs = ds_obs_sub
                else:
                    ds_obs = xr.concat([ds_obs,ds_obs_sub],dim='time',data_vars='minimal')

        ############## CMEMS ##############
        if obs in ['CMEMS']:
            syear_obs = obs_year_range[nobs][0]
            fyear_obs = obs_year_range[nobs][1]
            fmon_obs = obs_year_range[nobs][2]
            #### create time axis for overlapping period
            timeax = xr.cftime_range(start=cftime.datetime(syear_obs,1,1),
                                     end=cftime.datetime(fyear_obs,fmon_obs,1),
                                     freq='MS')
            timeax = timeax.to_datetimeindex()    # cftime => datetime64
            ds_obs['time'] = timeax

            # calculate global mean sea level
            da_area = sa.da_area(ds_obs, lonname='longitude', latname='latitude',
                                 xname='longitude', yname='latitude', model=None)
            da_glo_mean = (ds_obs*da_area)\
                                .sum(dim=['longitude','latitude'])/\
                           da_area\
                                .sum(dim=['longitude','latitude'])
            ds_obs = ds_obs-da_glo_mean

            # rename
            ds_obs = ds_obs.rename({'longitude':'lon','latitude':'lat'})

        else:
            syear_obs = obs_year_range[nobs][0]
            fyear_obs = obs_year_range[nobs][1]
            #### create time axis for overlapping period
            timeax = xr.cftime_range(start=cftime.datetime(syear_obs,1,1),
                                     end=cftime.datetime(fyear_obs,12,31),
                                     freq='MS')
            timeax = timeax.to_datetimeindex()    # cftime => datetime64
            ds_obs['time'] = timeax


        # crop data (time)
        ds_obs = ds_obs[var]\
                          .where((ds_obs['time.year'] >= syear)&
                                 (ds_obs['time.year'] <= fyear)
                                 ,drop=True)
        ds_obs = ds_obs\
                          .where((ds_obs.lat >= np.min(np.array(tp_lat_region)))&
                                 (ds_obs.lat <= np.max(np.array(tp_lat_region)))
                                 ,drop=True)

        # store all model data
        ds_obs_list[var] = ds_obs

        # calculate mean
        obs_mean_list[var] = ds_obs_list[var].mean(dim='time').compute()
        ds_obs_list[var] = ds_obs_list[var]-obs_mean_list[var]

        # calculate seasonality
        obs_season_list[var] = ds_obs_list[var].groupby('time.month').mean(dim='time').compute()
        ds_obs_list[var] = ds_obs_list[var].groupby('time.month')-obs_season_list[var]

        # remove linear trend
        obs_linear_list[var] = da_linregress(ds_obs_list[var],stTconfint=0.99)

    obs_linear_mlist[obs] = obs_linear_list
    obs_mean_mlist[obs] = obs_mean_list
    obs_season_mlist[obs] = obs_season_list
    ds_obs_mlist[obs] = ds_obs_list


# # detrend
# for nobs,obs in enumerate(Obs_name):
#     for nvar,var in enumerate(Obs_varname[nobs]):
#         da_time = ds_obs_mlist[obs][var].time.copy()
#         year = ds_obs_mlist[obs][var]['time.year'].values
#         month = ds_obs_mlist[obs][var]['time.month'].values
#         da_time.values = year+month/12.
#         ds_obs_mlist[obs][var] = ds_obs_mlist[obs][var]-                                     (da_time*obs_linear_mlist[obs][var]['slope']+obs_linear_mlist[obs][var]['intercept'])



# # Ocean basin mask
# from create_ocean_mask import levitus98
#
# # # calculate zonal mean in the Pacific Basin
# # from create_ocean_mask import levitus98
#
# da_pacific = levitus98(da_model_standard,
#                        basin=['pac'],
#                        reuse_weights=True,
#                        newvar=True,
#                        lon_name='nlon',
#                        lat_name='nlat',
#                        new_regridder_name='')
#
# da_pacific = da_pacific*da_model_standard[Variable_standard]/da_model_standard[Variable_standard]



# # Derive Ekman upwelling/downwelling and wind stress curl
#########
# Model
#########
for nmodel,model in enumerate(Model_name):
    linear_mlist[model]['curl_tauuo'],linear_mlist[model]['curl_tauvo'] = curl_tau(
                                               linear_mlist[model]['tauuo'].slope,
                                               linear_mlist[model]['tauvo'].slope,
                                               xname=xname,yname=yname)

    linear_mlist[model]['curl_tau'] = linear_mlist[model]['curl_tauuo']+linear_mlist[model]['curl_tauvo']

    mean_mlist[model]['curl_tauuo'],mean_mlist[model]['curl_tauvo'] = curl_tau(
                                               mean_mlist[model]['tauuo'],
                                               mean_mlist[model]['tauvo'],
                                               xname=xname,yname=yname)

    mean_mlist[model]['curl_tau'] = mean_mlist[model]['curl_tauuo']+mean_mlist[model]['curl_tauvo']

    season_mlist[model]['curl_tauuo'],season_mlist[model]['curl_tauvo'] = curl_tau_3d(
                                               season_mlist[model]['tauuo'],
                                               season_mlist[model]['tauvo'],
                                               xname=xname,yname=yname)

    season_mlist[model]['curl_tau'] = season_mlist[model]['curl_tauuo']+season_mlist[model]['curl_tauvo']

#########
# Obs
#########
obs = 'WASwind'
obs_linear_mlist[obs]['curl_tx'],obs_linear_mlist[obs]['curl_ty'] = curl_var(
                                           obs_linear_mlist[obs]['tx'].slope,
                                           obs_linear_mlist[obs]['ty'].slope,
                                           x_name='lon',y_name='lat')

obs_linear_mlist[obs]['curl_tau'] = obs_linear_mlist[obs]['curl_tx']+obs_linear_mlist[obs]['curl_ty']

obs_mean_mlist[obs]['curl_tx'],obs_mean_mlist[obs]['curl_ty'] = curl_var(
                                           obs_mean_mlist[obs]['tx'],
                                           obs_mean_mlist[obs]['ty'],
                                           x_name='lon',y_name='lat')

obs_mean_mlist[obs]['curl_tau'] = obs_mean_mlist[obs]['curl_tx']+obs_mean_mlist[obs]['curl_ty']

obs_season_mlist[obs]['curl_tx'],obs_season_mlist[obs]['curl_ty'] = curl_var_3d(
                                           obs_season_mlist[obs]['tx'],
                                           obs_season_mlist[obs]['ty'],
                                           xname='lon',yname='lat')

obs_season_mlist[obs]['curl_tau'] = obs_season_mlist[obs]['curl_tx']+obs_season_mlist[obs]['curl_ty']


# # Regional averaging
#### setting regional range
lon_range  = lon_range_list
lat_range  = lat_range_list

# correct the lon range
lon_range_mod = np.array(lon_range)
lonmin = ds_model_mlist[model]['zos'].lon.min()
ind1 = np.where(lon_range_mod<np.float(0))[0]
lon_range_mod[ind1] = lon_range_mod[ind1]+360.  # change Lon range to 0-360


#####################
# MODEL
#####################
regionalavg_mlist = {}
for nmodel,model in enumerate(Model_name):
    regionalavg_list = {}
    for nvar,var in enumerate(['curl_tau','zos']):

        # read areacello
        da_area = xr.open_dataset(path[Model_name[0]][0]+areafile)['areacello']

        # crop region
        ds_mask = mean_mlist[model][var].where(
                      (mean_mlist[model][var].lon>=np.min(lon_range_mod))&
                      (mean_mlist[model][var].lon<=np.max(lon_range_mod))&
                      (mean_mlist[model][var].lat>=np.min(lat_range))&
                      (mean_mlist[model][var].lat<=np.max(lat_range))
                      ,drop=True).compute()
        ds_mask = ds_mask/ds_mask


        # calculate regional mean
        regionalavg_list['%s_%i_%i_%i_%i_season'%(var,lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
          = ((season_mlist[model][var]*ds_mask*da_area).sum(dim=[xname,yname])/(ds_mask*da_area).sum(dim=[xname,yname])).compute()

        regionalavg_list['%s_%i_%i_%i_%i_mean'%(var,lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
          = ((mean_mlist[model][var]*ds_mask*da_area).sum(dim=[xname,yname])/(ds_mask*da_area).sum(dim=[xname,yname])).compute()

        regionalavg_list['%s_%i_%i_%i_%i_linear'%(var,lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
          = ((linear_mlist[model][var]*ds_mask*da_area).sum(dim=[xname,yname])/(ds_mask*da_area).sum(dim=[xname,yname])).compute()

    regionalavg_mlist[model] = regionalavg_list

#####################
# OBS
#####################
obs_regionalavg_mlist = {}
for nobs,obs in enumerate(Obs_name):
    obs_regionalavg_list = {}
    if obs in ['CMEMS']:
        var = 'adt'
        obs_xname = 'lon'
        obs_yname = 'lat'

    elif obs in ['WASwind']:
        var = 'curl_tau'
        obs_xname = 'lon'
        obs_yname = 'lat'


    da_area = sa.da_area(obs_mean_mlist[obs][var], lonname='lon', latname='lat',
                                 xname=obs_xname, yname=obs_yname, model=None)

    # crop region
    ds_obs_mask = obs_mean_mlist[obs][var].where(
                  (obs_mean_mlist[obs][var].lon>=np.min(lon_range_mod))&
                  (obs_mean_mlist[obs][var].lon<=np.max(lon_range_mod))&
                  (obs_mean_mlist[obs][var].lat>=np.min(lat_range))&
                  (obs_mean_mlist[obs][var].lat<=np.max(lat_range))
                  ,drop=True).compute()
    ds_obs_mask = ds_obs_mask/ds_obs_mask

    # calculate regional mean
    obs_regionalavg_list['%s_%i_%i_%i_%i_season'%(var,lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
      = ((obs_season_mlist[obs][var]*ds_obs_mask*da_area).sum(dim=[obs_xname,obs_yname])/ \
         (ds_obs_mask*da_area).sum(dim=[obs_xname,obs_yname])).compute()

    obs_regionalavg_list['%s_%i_%i_%i_%i_mean'%(var,lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
      = ((obs_mean_mlist[obs][var]*ds_obs_mask*da_area).sum(dim=[obs_xname,obs_yname])/ \
         (ds_obs_mask*da_area).sum(dim=[obs_xname,obs_yname])).compute()

    obs_regionalavg_list['%s_%i_%i_%i_%i_linear'%(var,lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
      = ((obs_linear_mlist[obs][var]*ds_obs_mask*da_area).sum(dim=[obs_xname,obs_yname])/ \
         (ds_obs_mask*da_area).sum(dim=[obs_xname,obs_yname])).compute()

    obs_regionalavg_mlist[obs] = obs_regionalavg_list


#### plotting
fig = plt.figure(1)


#######
# mean
#######
ax1 = fig.add_axes([0,0,1,1])
obscolor = 'k'

all_wsc = []
all_ssh = []

wsc = obs_regionalavg_mlist['WASwind']['%s_%i_%i_%i_%i_mean'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]
ssh = obs_regionalavg_mlist['CMEMS']['%s_%i_%i_%i_%i_mean'%('adt',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]
ax1.scatter(wsc,ssh,c='k',label='Observation')
all_wsc.append(wsc)
all_ssh.append(ssh)

for nmodel,model in enumerate(Model_name):
    wsc = regionalavg_mlist[model]['%s_%i_%i_%i_%i_mean'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]
    ssh = regionalavg_mlist[model]['%s_%i_%i_%i_%i_mean'%('zos',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]
    ax1.scatter(wsc,ssh,label='%s'%(Model_legend_name[nmodel]))
    all_wsc.append(wsc)
    all_ssh.append(ssh)

all_wsc = np.array(all_wsc)
all_ssh = np.array(all_ssh)

#### setting the plotting format
ax1.set_ylabel('SSH (m)',{'size':'20'},color='k')
ax1.set_ylim([all_ssh.min()-all_ssh.min()/5.,all_ssh.max()+all_ssh.max()/5.])
ax1.set_xlabel('WSC (N/m$^3$)',{'size':'20'},color='k')
ax1.set_xlim([all_wsc.min()-all_wsc.min()/5.,all_wsc.max()+all_wsc.max()/5.])
ax1.tick_params(axis='y',labelsize=20,labelcolor='k',rotation=0)
ax1.tick_params(axis='x',labelsize=20,labelcolor='k',rotation=0)
ax1.set_title("Mean state",{'size':'24'},pad=24)
# ax1.legend(loc='upper left',bbox_to_anchor=(1.05, 1),fontsize=14,frameon=False)
ax1.grid(linestyle='dashed',alpha=0.5,color='grey')

#########
# Linear
#########
ax1 = fig.add_axes([1.3,0,1,1])
# obscolor = 'k'

all_wsc = []
all_ssh = []

wsc = obs_regionalavg_mlist['WASwind']['%s_%i_%i_%i_%i_linear'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]
ssh = obs_regionalavg_mlist['CMEMS']['%s_%i_%i_%i_%i_linear'%('adt',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].slope
ax1.scatter(wsc,ssh,c='k',label='Observation')
all_wsc.append(wsc)
all_ssh.append(ssh)

for nmodel,model in enumerate(Model_name):
    wsc = regionalavg_mlist[model]['%s_%i_%i_%i_%i_linear'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]
    ssh = regionalavg_mlist[model]['%s_%i_%i_%i_%i_linear'%('zos',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].slope
    ax1.scatter(wsc,ssh,label='%s'%(Model_legend_name[nmodel]))
    all_wsc.append(wsc)
    all_ssh.append(ssh)

all_wsc = np.array(all_wsc)
all_ssh = np.array(all_ssh)


#### setting the plotting format
ax1.set_ylabel('SSH (m)',{'size':'20'},color='k')
ax1.set_ylim([all_ssh.min()-all_ssh.min()/5.,all_ssh.max()+all_ssh.max()/5.])
ax1.set_xlabel('WSC (N/m$^3$)',{'size':'20'},color='k')
ax1.set_xlim([all_wsc.min()-all_wsc.min()/5.,all_wsc.max()+all_wsc.max()/5.])
ax1.tick_params(axis='y',labelsize=20,labelcolor='k',rotation=0)
ax1.tick_params(axis='x',labelsize=20,labelcolor='k',rotation=0)
ax1.set_title("Linear trend",{'size':'24'},pad=24)
ax1.legend(loc='upper left',bbox_to_anchor=(1.05, 1),fontsize=14,frameon=False)
ax1.grid(linestyle='dashed',alpha=0.5,color='grey')



#########
# Annual amp
#########
ax1 = fig.add_axes([0,-1.5,1,1])
# obscolor = 'k'

all_wsc = []
all_ssh = []

wsc = obs_regionalavg_mlist['WASwind']['%s_%i_%i_%i_%i_season'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].max()\
      -obs_regionalavg_mlist['WASwind']['%s_%i_%i_%i_%i_season'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].min()
ssh = obs_regionalavg_mlist['CMEMS']['%s_%i_%i_%i_%i_season'%('adt',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].max()\
      -obs_regionalavg_mlist['CMEMS']['%s_%i_%i_%i_%i_season'%('adt',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].min()
wsc = np.abs(wsc)
ssh = np.abs(ssh)
ax1.scatter(wsc,ssh,c='k',label='Observation')
all_wsc.append(wsc)
all_ssh.append(ssh)

for nmodel,model in enumerate(Model_name):
    wsc = regionalavg_mlist[model]['%s_%i_%i_%i_%i_season'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].max()\
          -regionalavg_mlist[model]['%s_%i_%i_%i_%i_season'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].min()
    ssh = regionalavg_mlist[model]['%s_%i_%i_%i_%i_season'%('zos',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].max()\
          -regionalavg_mlist[model]['%s_%i_%i_%i_%i_season'%('zos',lon_range[0],lon_range[1],lat_range[0],lat_range[1])].min()
    ax1.scatter(wsc,ssh,label='%s'%(Model_legend_name[nmodel]))
    wsc = np.abs(wsc)
    ssh = np.abs(ssh)
    all_wsc.append(wsc)
    all_ssh.append(ssh)



all_wsc = np.array(all_wsc)
all_ssh = np.array(all_ssh)


#### setting the plotting format
ax1.set_ylabel('SSH (m)',{'size':'20'},color='k')
ax1.set_ylim([all_ssh.min()-all_ssh.min()/5.,all_ssh.max()+all_ssh.max()/5.])
ax1.set_xlabel('WSC (N/m$^3$)',{'size':'20'},color='k')
ax1.set_xlim([all_wsc.min()-all_wsc.min()/5.,all_wsc.max()+all_wsc.max()/5.])
ax1.tick_params(axis='y',labelsize=20,labelcolor='k',rotation=0)
ax1.tick_params(axis='x',labelsize=20,labelcolor='k',rotation=0)
ax1.set_title("Annual amplitude",{'size':'24'},pad=24)
# ax1.legend(loc='upper left',fontsize=14,frameon=False)
ax1.grid(linestyle='dashed',alpha=0.5,color='grey')


#########
# Annual phase
#########
ax1 = fig.add_axes([1.3,-1.5,1,1])
# obscolor = 'k'


all_wsc = []
all_ssh = []

ind = obs_regionalavg_mlist['WASwind']['%s_%i_%i_%i_%i_season'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
      .argmax()
wsc = obs_regionalavg_mlist['WASwind']['%s_%i_%i_%i_%i_season'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
      .isel(month=ind).month.values
ind = obs_regionalavg_mlist['CMEMS']['%s_%i_%i_%i_%i_season'%('adt',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
      .argmax()
ssh = obs_regionalavg_mlist['CMEMS']['%s_%i_%i_%i_%i_season'%('adt',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
      .isel(month=ind).month.values

ax1.scatter(wsc,ssh,c='k',label='Observation')
all_wsc.append(wsc)
all_ssh.append(ssh)

for nmodel,model in enumerate(Model_name):
    ind = regionalavg_mlist[model]['%s_%i_%i_%i_%i_season'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
          .argmax()
    wsc = regionalavg_mlist[model]['%s_%i_%i_%i_%i_season'%('curl_tau',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
          .isel(month=ind).month.values
    ind = regionalavg_mlist[model]['%s_%i_%i_%i_%i_season'%('zos',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
          .argmax()
    ssh = regionalavg_mlist[model]['%s_%i_%i_%i_%i_season'%('zos',lon_range[0],lon_range[1],lat_range[0],lat_range[1])]\
          .isel(month=ind).month.values

    ax1.scatter(wsc,ssh,label='%s'%(Model_legend_name[nmodel]))
    all_wsc.append(wsc)
    all_ssh.append(ssh)



all_wsc = np.array(all_wsc)
all_ssh = np.array(all_ssh)


#### setting the plotting format
ax1.set_ylabel('SSH (month)',{'size':'20'},color='k')
ax1.set_ylim([0.5,12.5])
ax1.set_xlabel('WSC (month)',{'size':'20'},color='k')
ax1.set_xlim([0.5,12.5])
ax1.tick_params(axis='y',labelsize=20,labelcolor='k',rotation=0)
ax1.tick_params(axis='x',labelsize=20,labelcolor='k',rotation=0)
ax1.set_title("Annual phase",{'size':'24'},pad=24)
# ax1.legend(loc='upper left',fontsize=14,frameon=False)
ax1.grid(linestyle='dashed',alpha=0.5,color='grey')



fig.savefig(os.getenv('WK_DIR')+'/model/PS/example_model_plot.eps', facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches="tight", pad_inches=None,
                frameon=None)
fig.savefig(os.getenv('WK_DIR')+'/obs/PS/example_obs_plot.eps', facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches="tight", pad_inches=None,
                frameon=None)
