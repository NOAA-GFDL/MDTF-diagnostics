#!/usr/bin/python

import numpy as np 
import scipy.io as sio
import matplotlib.pyplot as plt
import os
import datacycs as dc
import dataload as dl
import pdb
from netCDF4 import Dataset
import defines

# Defining variables
model_name = defines.model_name
year_list = defines.year_list
var_names = defines.var_names
hem_list = defines.hem_list

# global var variables used by the program
flip_lon_flag = False

# reading in the datacycs
for i_year in year_list:
  for var_name_ind, var_name in enumerate(var_names):
    for hemis in hem_list:
      
      print ('Processing %d for %s in the %s !'%(i_year, var_name.upper(), hemis))

      ############## READING MODEL SAMPLE LAT AND LON
      reflon, reflat, flip_lon_flag, flip_lon_val = dl.load_model_cdt(i_year, var_name)

      ############## SETTING GRID LENGTHS
      boxlen = 45
      gridlen, gridleny = dc.set_gridlengths(reflon, reflat, boxlen)

      ############# LOAD IN CYCLONE DICTIONARY
      cyc_file = dl.file_format_parser(defines.datacyc_file_format, var_name, i_year)
      cyc = sio.loadmat(cyc_file)['cyc'][0]

      ############ GETTING ONLY THE CYCLONES IN THE GIVEN HEMISPHERE
      cyc = dc.select_region(cyc, hemis)

      ############ LOAD TOPOGRAPHIC & LAND MASK INFORMATION
      topo, lm = dl.load_topo_lm()

      ############ LOAD IN MODEL VARIABLE
      var_data, full_date = dl.load_model_var(var_name_ind, i_year, flip_lon_flag, flip_lon_val)

      ############ Create Dataframe with all the cyclones and dates, creates netcdf as well
      datacycs = dl.grab_data(cyc, [gridlen, gridleny], var_data, full_date, reflon, reflat, var_name, topo, lm, i_year, hemis)

      # pdb.set_trace()

      ############ GRAB THE DATA FOR THE VARIABLES FOR ALL THE CYCS

      # in_file = '/mnt/drive1/jj/'



# notes
'''
major issues:

minor issues:
* Right now if the track goes into the next year, we have nan values, have to fix this later


** created defines.py, make it so that you only have to change this file if you want to run this datacyc creation code
'''

