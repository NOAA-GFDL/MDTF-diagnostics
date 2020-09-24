import numpy as np 
import xarray as xr 
import os 
import matplotlib.pyplot as plt 

print('Start of ETC-Composites...')

os.system('ls -lhtr')
print(os.environ['POD_HOME'])
cmd = "python %s/util/run_tracker.py"%(os.environ['POD_HOME'])
os.system(cmd)

print('Done Completing ETC-composites driver code.')
