#!/usr/bin/env python
# coding: utf-8

# In[3]:

import os
#import netCDF4 as nc
#import numpy as np
#import xarray as xr
import warnings

from postprocessing import *
from calculate_index import *
from draw_figure import *

warnings.simplefilter("ignore")

# In[4]:


#input_path_low = '/glade/work/jshin/mdtf/inputdata/WBC_var/model/CESM-CAM5-BGC-LE/'
#input_path_low = '/glade/work/jshin/mdtf/inputdata/WBC_var/model/CESM-CAM5-BGC-LE/test/'
#input_path_obs = '/glade/work/jshin/mdtf/inputdata/obs_data/WBC_var/'
#input_path_low = '/glade/work/jshin/mdtf/inputdata/WBC_var/model/CESM2_historical_r11i1p1f1_gr_195001-201412/mon/'
#input_path_high = '/glade/work/jshin/mdtf/inputdata/WBC_var/model/CESM1-CAM5-SE-HR/'


# In[5]:

work_dir = os.environ["WORK_DIR"]
input_path = os.environ["ZOS_FILE"]
input_path_obs = os.environ["OBS_DATA"]
print('ZOS_FILE is:', input_path)
print('work dir is:', work_dir)
print('input data path is:', input_path_obs)


input_path_obs2 = '/glade/work/jshin/mdtf/inputdata/obs_data/WBC_var/'
input_path_low = '/glade/work/jshin/mdtf/inputdata/WBC_var/model/MME-LR/'
input_path_high = '/glade/work/jshin/mdtf/inputdata/WBC_var/model/MME-HR/'
#input_path_low = '/glade/work/jshin/mdtf/inputdata/WBC_var/model/MME-LR/test/'
#input_path_high = '/glade/work/jshin/mdtf/inputdata/WBC_var/model/MME-HR/test/'


# In[6]:


data_obs_raw = read_data(input_path_obs2) 
data_model_raw = read_data(input_path_low)
data_hi_model_raw = read_data(input_path_high)

# In[7]:

#work_dir = './'
#save_dir = work_dir+'/figures/'
save_dir = work_dir+'/obs/'

# In[8]:


REGION = ["gulf", "kuroshio", "australia", "agulhas", "brazil"]
CURRENT = ["Gulf Stream", "Kuroshio Current", "East Australia Current", "Agulhas Current", "North Brazil Current"]
MODEL_NAME = ["CESM1", "EC-Earth3P","ECMWF-IFS", "HadGEM3-GC31"]
#MODEL_NAME = ["CESM1"]



# In[14]:



for region in REGION:
    
# 선택한 REGION에 대한 데이터 선택
    bounds = region_define(region)
    data_obs = data_obs_raw.sel(lon=bounds["lon"], lat=bounds["lat"], time=slice('1993-01-01', '2020-12-31'))
    data_model = data_model_raw.sel(lon=bounds["lon"], lat=bounds["lat"], time=slice('1993-01-01', '2020-12-31'))
    data_hi_model = data_hi_model_raw.sel(lon=bounds["lon"], lat=bounds["lat"], time=slice('1993-01-01', '2020-12-31'))
 
    data_obs['msl'] = data_obs['zos'].mean(dim='time', skipna=True)
    data_model['msl'] = data_model['zos'].mean(dim='time', skipna=True)
    data_hi_model['msl'] = data_hi_model['zos'].mean(dim='time', skipna=True)

    data_obs['sla_std'] = data_obs['sla'].std(dim='time', skipna=True)
    data_model['sla_std'] = data_model['sla'].std(dim='time', skipna=True)
    data_hi_model['sla_std'] = data_hi_model['sla'].std(dim='time', skipna=True)

    gs_index(data_obs,region)
    gs_index(data_model,region)
    gs_index(data_hi_model,region)

    gsp_index(data_obs, region)
    gsp_index(data_model, region)
    gsp_index(data_hi_model, region)

    EOF_index(data_obs, region)
    EOF_index(data_model, region)
    EOF_index(data_hi_model, region)

    
    FIG1(data_obs,data_model,data_hi_model,MODEL_NAME,save_path=save_dir,save_name=region)
    FIG2(data_obs,data_model,data_hi_model,MODEL_NAME,save_path=save_dir,save_name=region)
    FIG3(data_obs,data_model,data_hi_model,MODEL_NAME,save_path=save_dir,save_name=region)

"""
region = 'gulf'
    
# 선택한 REGION에 대한 데이터 선택
bounds = region_define(region)
data_obs = data_obs_raw.sel(lon=bounds["lon"], lat=bounds["lat"], time=slice('1993-01-01', '2020-12-31'))
data_model = data_model_raw.sel(lon=bounds["lon"], lat=bounds["lat"], time=slice('1993-01-01', '2020-12-31'))
data_hi_model = data_hi_model_raw.sel(lon=bounds["lon"], lat=bounds["lat"], time=slice('1993-01-01', '2020-12-31'))
 
data_obs['msl'] = data_obs['zos'].mean(dim='time', skipna=True)
data_model['msl'] = data_model['zos'].mean(dim='time', skipna=True)
data_hi_model['msl'] = data_hi_model['zos'].mean(dim='time', skipna=True)

data_obs['sla_std'] = data_obs['sla'].std(dim='time', skipna=True)
data_model['sla_std'] = data_model['sla'].std(dim='time', skipna=True)
data_hi_model['sla_std'] = data_hi_model['sla'].std(dim='time', skipna=True)

gs_index(data_obs,region)
gs_index(data_model,region)
gs_index(data_hi_model,region)

gsp_index(data_obs, region)
gsp_index(data_model, region)
gsp_index(data_hi_model, region)

EOF_index(data_obs, region)
EOF_index(data_model, region)
EOF_index(data_hi_model, region)

    
FIG1(data_obs,data_model,data_hi_model,MODEL_NAME,save_path=save_dir,save_name=region)
FIG2(data_obs,data_model,data_hi_model,MODEL_NAME,save_path=save_dir,save_name=region)
FIG3(data_obs,data_model,data_hi_model,MODEL_NAME,save_path=save_dir,save_name=region)
"""
