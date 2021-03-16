import numpy as np
import os
import math
import sys

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)
from util import check_required_dirs

###   
###  def get_directories():

modeldir = os.environ["ENSO_MSE_WKDIR"]+"/model"    #defined in ENSO_MSE.py

dirs_to_create = [ modeldir,
                   modeldir+"/PS"]
check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=2)

####

print( os.environ["ENSO_MSE_WKDIR_COMPOSITE"])
modeldir2 = os.environ["ENSO_MSE_WKDIR_COMPOSITE"]+"/model"    #defined in ENSO_MSE.py

dirs_to_create = [ modeldir2,
                   modeldir2+"/PS",
                   modeldir2+"/netCDF/DATA" ,
                   modeldir2+"/netCDF/CLIMA" ,
                   modeldir2+"/netCDF/ELNINO" ,
                   modeldir2+"/netCDF/LANINA" ,
                   modeldir2+"/netCDF/24MONTH_ELNINO" ,
                   modeldir2+"/netCDF/24MONTH_LANINA" ,
                   modeldir2+"/netCDF/24MONTH_ELNINO/BIN" ,
                   modeldir2+"/netCDF/24MONTH_LANINA/BIN"]
 
###  create if necessary
check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=2)
       
###   copy  obs file to respective run directory 
#DRB taken out because it is now written to the wkdir
#obs_dir = os.environ["OBS_DATA"] + "/COMPOSITE/"
#os.system("cp "+  obs_dir + "/*.png " +  obs_dir01 + "/." + " 2> /dev/null")
####
