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
print("      Start of Composite Module calculations " + now.strftime("%Y-%m-%d %H:%M") )
print("      (preprocess.py)                  ")
print("      Based on the years, and domain selected                  ")
print("      the preprocessing calculations may take many minutes,    ")
print("      in some cases up to 20-30  minutes.                       ")
print("===============================================================")

prefix = os.environ["POD_HOME"] + "/COMPOSITE/"

this_wrk_dir = os.environ["WK_DIR"]+"/COMPOSITE"
prefix1 = this_wrk_dir+"/model/netCDF/DATA/"
prefix2 = this_wrk_dir+"/model/netCDF/CLIMA/"

iy1 = os.environ["FIRSTYR"]
iy2 = os.environ["LASTYR"]
iy1 = int(iy1)
iy2 = int(iy2)

###   check for th flag file and read - that is if pre-processing is needed.

convert_file = prefix1 + "/preprocess.txt"

## print( convert_file)

flag0 = -1

if( os.path.isfile( convert_file) ):
    f = open(convert_file , 'r')
    flag0  = f.read()
    print( " preprocessing flag =",  flag0)
    print( "preprocess.py: read preprocessing flag = "+ flag0+" ,in: "+convert_file)

    f.close()

if( flag0 == '1'):
### print diagnostic message
    print "  The NetCDF data have already been converted (preprocess.py)  "
    print "   "
    print " "
else:
### print diagnostic message 
    print "  The NetCDF data are being converted (preprocess.py) "
    print "   "
    print " " 
###   prepare the directories 

#os.system("mkdir " +  os.environ["DATADIR"]  + "/DATA/" + " 2> /dev/null") 
#os.system("mkdir " +  os.environ["DATADIR"]  + "/CLIMA/" + " 2> /dev/null")

#DRB should be done elsewhere    
#    os.system("mkdir " +  os.environ["WK_DIR"]+"/COMPOSITE/model/netCDF/DATA/" + " 2> /dev/null") 
#    os.system("mkdir " +  os.environ["WK_DIR"]+"/COMPOSITE/model/netCDF/CLIMA/" + " 2> /dev/null")

##   need to check for missing input data 

    for iy in range( iy1, iy2+1):
        os.system("mkdir " + prefix1 + str(iy) + " 2> /dev/null" ) 

## print os.environ["POD_HOME"] + "/COMPOSITE/NCL_CONVERT/data_routine.ncl"
    print " conversion routine started  "
    print " 3-D atmospheric variables conversion "
    print " depending on the data input volume the process can take over 15 minutes "
    generate_ncl_call(os.environ["POD_HOME"] + "/COMPOSITE/NCL_CONVERT/data_routine.ncl")
    now = datetime.datetime.now()
    print"  conversion routine finished " + now.strftime("%Y-%m-%d %H:%M") 

    print " NET radiation routine started "
    generate_ncl_call(os.environ["POD_HOME"] + "/COMPOSITE/NCL_CONVERT/data_radiation_routine.ncl")
    now = datetime.datetime.now()
    print"  NET radiation routine finished " + now.strftime("%Y-%m-%d %H:%M")      

    print " clima routine started "
    generate_ncl_call(os.environ["POD_HOME"] + "/COMPOSITE/NCL_CONVERT/clima_routine.ncl")
    now = datetime.datetime.now()
    print"  clima routine finished " + now.strftime("%Y-%m-%d %H:%M")

###     print " preprocessing completed "
##  print the flag to  external file so once preprocess it could be skipped
    convert_file = prefix1 + "/preprocess.txt"
    f = open(convert_file , 'w')
    f.write("1")
    f.close()

##  os.system("cp +os.environ["DATADIR"]+/COMPOSITE/DATA/* "+os.environ["WK_DIR"]+"/COMPOSITE/model/netCDF/DATA/.")

    now = datetime.datetime.now()
    print " Preprocessing completed  " + now.strftime("%Y-%m-%d %H:%M")
    print " ===========================================  " 
