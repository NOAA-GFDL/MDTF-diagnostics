import numpy as np
import sys
import math

import datetime
 
import os

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)
from util import check_required_dirs
from generate_ncl_call import generate_ncl_call

'''
    to pre-process the data for the diagnostic package 
    the code extract the necessary variables from NetCDF files
    and constructs monthly climatologies and anomalies needed 
    for further processing

'''

now = datetime.datetime.now()
print("===============================================================")
print("      Start of Level 1 Module calculations " + now.strftime("%Y-%m-%d %H:%M") )
print("      Based on the years, and domain selected                  ")
print("      the preprocessing calculations may take several minutes.    ")
print("===============================================================")


prefix = os.environ["POD_HOME"] + "/LEVEL_01/"

this_wrk_dir = os.environ["ENSO_RWS_WKDIR"]
prefix1 = this_wrk_dir+"/model/netCDF/DATA/"
prefix2 = this_wrk_dir+"/model/netCDF/CLIMA/"

iy1 = os.environ["FIRSTYR"]
iy2 = os.environ["LASTYR"]
iy1 = int(iy1)
iy2 = int(iy2)

##   need to check for missing input data 

for iy in range( iy1, iy2+1):
    os.system("mkdir " + prefix1 + str(iy) + " 2> /dev/null" ) 

print (" Data routines started  ")
print (" 3-D atmospheric variables conversion ")
print (" depending on the data input volume the process can take few minutes ")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/data_routine.ncl")
generate_ncl_call(os.environ["POD_HOME"] + "/LEVEL_01/NCL/dTdt_routine.ncl")

now = datetime.datetime.now()
print("  Data routine finished " + now.strftime("%Y-%m-%d %H:%M") )

