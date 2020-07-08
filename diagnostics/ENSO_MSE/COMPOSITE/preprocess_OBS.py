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

from read_netcdf import read_netcdf

'''
    to pre-process the data for the diagnostic package 
    the code extract the necessary variables from NetCDF files
    and constructs monthly climatologies and anomalies needed 
    for further processing

'''

now = datetime.datetime.now()
print("===============================================================")
print("      Starting Pre-processing Observational Data " + now.strftime("%Y-%m-%d %H:%M") )
print("      (preprocess_OBS.py)                  ")
print("      Based on the years, and domain selected                  ")
print("      the preprocessing calculations may take many minutes,    ")
print("      in some cases up to 20-30  minutes.                       ")
print("===============================================================")

### 
prefix = os.environ["POD_HOME"] + "/COMPOSITE/"

###  output directory 
this_wrk_dir = os.environ["ENSO_MSE_WKDIR_COMPOSITE"]
prefix1 = this_wrk_dir+"/obs/netCDF/DATA/"
prefix2 = this_wrk_dir+"/obs/netCDF/CLIMA/"

###   years for Era-Interim only !!
iy1 = 1982
iy2 = 2011

###   check for the flag file and read - that is if pre-processing is needed.

convert_file = prefix1 + "/preprocess.txt"

## print( convert_file)

flag0 = '0'

if( os.path.isfile( convert_file) ):
##        print("preprocess_OBS.py found existing "+convert_file)
    f = open(convert_file , 'r')
    flag0  = f.read()
    print( "preprocess_OBS.py preprocessing flag ="+ flag0+" , "+convert_file)
    f.close()
        
if( flag0 == '1'):
### print diagnostic message
    print "  The Observational NetCDF data have already been converted (preprocess_OBS.py) "
    print "   "
    print " "
else:
### print diagnostic message 
    print "  The Observational NetCDF data are being converted (preprocess_OBS.py) "
    print "   "
    print " " 
###   prepare the directories 

#os.system("mkdir " +  os.environ["DATADIR"]  + "/DATA/" + " 2> /dev/null") 
#os.system("mkdir " +  os.environ["DATADIR"]  + "/CLIMA/" + " 2> /dev/null")
    

#    os.system("mkdir " +  os.environ["OBS_DATA"] + "/COMPOSITE/netCDF/DATA/"  + " 2> /dev/null") 
#    os.system("mkdir " +  os.environ["OBS_DATA"] + "/COMPOSITE/netCDF/CLIMA/"  + " 2> /dev/null") 

###    the annual directories are created in NCL  scrip data_routine.ncl
##    for iy in range( iy1, iy2+1):
##        os.system("mkdir " + prefix1 + str(iy) + " 2> /dev/null" ) 

## print os.environ["POD_HOME"] + "/COMPOSITE/NCL_CONVERT/data_routine_OBS.ncl"
    print " Observational Data conversion routine started  "
    print " 3-D atmospheric variables conversion "
    print " depending on the data input volume the process can take over 15 minutes "
    generate_ncl_call(os.environ["POD_HOME"] + "/COMPOSITE/NCL_CONVERT/data_routine_OBS.ncl")
    now = datetime.datetime.now()
    print"  Observational Data conversion routine finished " + now.strftime("%Y-%m-%d %H:%M") 
    print " Observational Data NET radiation routine started "
    generate_ncl_call(os.environ["POD_HOME"] + "/COMPOSITE/NCL_CONVERT/data_radiation_routine_OBS.ncl")
    now = datetime.datetime.now()
    print" Observational Data NET radiation routine finished " + now.strftime("%Y-%m-%d %H:%M")      

    now = datetime.datetime.now()
    print " Observational Data  Clima routine started " + now.strftime("%Y-%m-%d %H:%M")
    generate_ncl_call(os.environ["POD_HOME"] + "/COMPOSITE/NCL_CONVERT/clima_routine_OBS.ncl")
    now = datetime.datetime.now()
    print" Observational Data  clima routine finished " + now.strftime("%Y-%m-%d %H:%M")

###     print " preprocessing completed "
##  print the flag to  external file so once preprocess it could be skipped
    convert_file = prefix1 + "/preprocess.txt"
    f = open(convert_file , 'w')
    f.write("1")
    f.close()

##  os.system("cp +os.environ["DATADIR"]+/COMPOSITE/DATA/* "+os.environ["WK_DIR"]+"/COMPOSITE/model/netCDF/DATA/.")

    now = datetime.datetime.now()
    print " Observational Data Preprocessing completed  " + now.strftime("%Y-%m-%d %H:%M")
    print " ===========================================  " 
