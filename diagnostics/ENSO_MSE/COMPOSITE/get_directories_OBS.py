import numpy as np
import os.path
import math
import sys

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
