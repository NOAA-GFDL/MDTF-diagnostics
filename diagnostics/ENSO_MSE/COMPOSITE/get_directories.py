import numpy as np
import os
import math
import sys

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
os.sys.path.insert(0, shared_dir)
from util import check_required_dirs

###   
###  def get_directories():


modeldir = os.environ["ENSO_MSE_WKDIR_COMPOSITE"]+"/model"    #defined in ENSO_MSE.py

dirs_to_create = [ modeldir,
                   modeldir+"/PS",
                   modeldir+"/netCDF/DATA" ,
                   modeldir+"/netCDF/CLIMA" ,
                   modeldir+"/netCDF/ELNINO" ,
                   modeldir+"/netCDF/LANINA" ,
                   modeldir+"/netCDF/24MONTH_ELNINO" ,
                   modeldir+"/netCDF/24MONTH_LANINA" ,
                   modeldir+"/netCDF/24MONTH_ELNINO/BIN" ,
                   modeldir+"/netCDF/24MONTH_LANINA/BIN"]
 
###  create if necessary
check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=2)
       
###   copy  obs file to respective run directory 
#DRB taken out because it is now written to the wkdir
#obs_dir = os.environ["OBS_DATA"] + "/COMPOSITE/"
#os.system("cp "+  obs_dir + "/*.png " +  obs_dir01 + "/." + " 2> /dev/null")
####
