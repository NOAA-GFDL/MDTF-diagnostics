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

obsdir = os.environ["ENSO_MSE_WKDIR_COMPOSITE"]+"/obs"


###  check the directories 
dirs_to_create =  [obsdir+"/PS",
                   obsdir+"/netCDF/DATA",
                   obsdir+"/netCDF/CLIMA",
                   obsdir+"/netCDF/ELNINO",
                   obsdir+"/netCDF/LANINA",
                   obsdir+"/netCDF/24MONTH_ELNINO",
                   obsdir+"/netCDF/24MONTH_LANINA",
                   obsdir+"/netCDF/24MONTH_ELNINO/BIN",
                   obsdir+"/netCDF/24MONTH_LANINA/BIN"]

check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=3)
       
####
