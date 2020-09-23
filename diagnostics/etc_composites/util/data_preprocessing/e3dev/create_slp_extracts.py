#!/usr/bin/python
import os
import glob
import numpy as np 

for i_file in glob.glob('./2013/2D/*.nc'):

  split_file = os.path.split(i_file)
  fname = split_file[-1]
  folder = split_file[0]

  pre_fname = fname.split('.')[0][0:8]

  in_fname = os.path.join(folder, fname)
  out_fname = os.path.join(folder, 'slp', pre_fname + '.slp.nc')

  cmd = 'cdo selname,slp %s %s'%(in_fname, out_fname)
  print cmd
  ret_val = os.system(cmd)
  print ret_val
