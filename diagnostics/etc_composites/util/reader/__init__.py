import scipy.io as sio
import numpy as np 
from netCDF4 import Dataset
import datetime as dt

import matplotlib.pyplot as plt

class dot_dict(dict):
  __getattr__ = dict.__getitem__
  __setattr__ = dict.__setitem__
  __delattr__ = dict.__delitem__

  def __init__(self, dict):
    for key, value in dict.items():
      if hasattr(value, 'keys'):
        value = dot_dict(value)
      self[key] = value

  def find_centers_for_date(self, date):
    ind = (self.yy == date.year) & (self.mm == date.month) & (self.dd == date.day) & (self.hh == date.hour)
  
    return dot_dict({'lat': self.lat[ind], 'lon': self.lon[ind], 'date': self.date[ind], 
      'yy': self.yy[ind], 'mm': self.mm[ind], 'dd': self.dd[ind], 'hh': self.hh[ind], 
      'warm_flag': self.warm_flag[ind], 'obs_flag': self.obs_flag[ind], 'lm_flag': self.lm_flag[ind],
      'all_select_flag': self.all_select_flag[ind], 'obs_select_flag': self.obs_select_flag[ind]})

def get_date(matlab_datenum):
  date = dt.datetime.fromordinal(int(matlab_datenum) - 366) + dt.timedelta(hours=int((matlab_datenum-int(matlab_datenum))*24))
  return date

def read_center_from_mat_file(in_file):
  '''
  Code to read in the center's matlab file that is created using main_create_dict.py
  '''
  data = sio.loadmat(in_file)['cyc']

  lat = []
  lon = []
  date = []
  yy = []
  mm = []
  dd = []
  hh = []
  warm_flag = []
  obs_flag = []
  lm_flag = []
  all_select_flag = []
  obs_select_flag = []

  for i in range(data['fulllat'].shape[1]):

    track_lat = np.squeeze(data['fulllat'])[i]
    track_lon = np.squeeze(data['fulllon'])[i]
    track_fulldate = np.squeeze(data['fulldate'])[i]
    track_yy = np.squeeze(data['fullyr'])[i]
    track_mm = np.squeeze(data['fullmon'])[i]
    track_dd = np.squeeze(data['fullday'])[i]
    track_warm_flag = np.squeeze(data['warm_flag'])[i]
    track_obs_flag = np.squeeze(data['obs_flag'])[i]
    track_lm_flag = np.squeeze(data['lm_flag'])[i]

    track_date = [get_date(date) for date in np.squeeze(track_fulldate)]
    track_hh = [int((date - int(date))*24) for date in np.squeeze(track_fulldate)]
    
    track_obs_select_flag = np.zeros((len(track_hh), 1))
    track_all_select_flag = np.zeros((len(track_hh), 1))

    lat.extend(np.squeeze(track_lat))
    lon.extend(np.squeeze(track_lon))
    date.extend(np.squeeze(track_date))
    yy.extend(np.squeeze(track_yy))
    mm.extend(np.squeeze(track_mm))
    dd.extend(np.squeeze(track_dd))
    hh.extend(np.squeeze(track_hh))
    all_select_flag.extend(track_all_select_flag)
    obs_select_flag.extend(track_obs_select_flag)
    warm_flag.extend(np.squeeze(track_warm_flag))
    obs_flag.extend(np.squeeze(track_obs_flag))
    lm_flag.extend(np.squeeze(track_lm_flag))

  lat = np.squeeze(np.asarray(lat))
  lon = np.squeeze(np.asarray(lon))
  date = np.squeeze(np.asarray(date))
  yy = np.squeeze(np.asarray(yy))
  mm = np.squeeze(np.asarray(mm))
  dd = np.squeeze(np.asarray(dd))
  hh = np.squeeze(np.asarray(hh))
  warm_flag = np.squeeze(np.asarray(warm_flag))
  obs_flag = np.squeeze(np.asarray(obs_flag))
  lm_flag = np.squeeze(np.asarray(lm_flag))
  all_select_flag = np.squeeze(np.asarray(all_select_flag))
  obs_select_flag = np.squeeze(np.asarray(obs_select_flag))


  return dot_dict({'lat': lat, 'lon': lon, 'date': date, 'yy':yy, 'mm':mm, 'dd':dd, 'hh':hh, 'all_select_flag': all_select_flag, 'obs_select_flag': obs_select_flag, 'warm_flag': warm_flag,
      'obs_flag': obs_flag, 'lm_flag': lm_flag})
