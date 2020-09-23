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
      'yy': self.yy[ind], 'mm': self.mm[ind], 'dd': self.dd[ind], 'hh': self.hh[ind]})

def get_date(matlab_datenum):
  date = dt.datetime.fromordinal(int(matlab_datenum) - 366) + dt.timedelta(hours=int((matlab_datenum-int(matlab_datenum))*24))
  return date

def read_center_from_mat_file(in_file):

  # year = 2007
  # in_file = '/mnt/drive1/processed_data/tracks/merra2_tracks/ERAI_%d_cyc.mat'%(year)

  data = sio.loadmat(in_file)['cyc']

  lat = []
  lon = []
  date = []
  yy = []
  mm = []
  dd = []
  hh = []

  for i in range(data['fulllat'].shape[1]):

    track_lat = np.squeeze(data['fulllat'])[i]
    track_lon = np.squeeze(data['fulllon'])[i]
    track_fulldate = np.squeeze(data['fulldate'])[i]
    track_yy = np.squeeze(data['fullyr'])[i]
    track_mm = np.squeeze(data['fullmon'])[i]
    track_dd = np.squeeze(data['fullday'])[i]

    track_date = [get_date(date) for date in np.squeeze(track_fulldate)]
    track_hh = [int((date - int(date))*24) for date in np.squeeze(track_fulldate)]

    lat.extend(np.squeeze(track_lat))
    lon.extend(np.squeeze(track_lon))
    date.extend(np.squeeze(track_date))
    yy.extend(np.squeeze(track_yy))
    mm.extend(np.squeeze(track_mm))
    dd.extend(np.squeeze(track_dd))
    hh.extend(np.squeeze(track_hh))

  lat = np.squeeze(np.asarray(lat))
  lon = np.squeeze(np.asarray(lon))
  date = np.squeeze(np.asarray(date))
  yy = np.squeeze(np.asarray(yy))
  mm = np.squeeze(np.asarray(mm))
  dd = np.squeeze(np.asarray(dd))
  hh = np.squeeze(np.asarray(hh))

  # lon[lon > 180] -= 360.

  return dot_dict({'lat': lat, 'lon': lon, 'date': date, 'yy':yy, 'mm':mm, 'dd':dd, 'hh':hh})

def read_center_from_txt_file(in_file):
  '''Read the centers from the output text files from the TRACKER code.'''
  pass

def create_intermediate_file(lat, lon, time):
  '''
  Create a netcdf file that can be accessed by the front detection code.
  An Alternative method to just getting in the read in files.
  '''
  pass
