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

modeldir  = os.environ["ENSO_MSE_WKDIR_MSE_VAR"]+"/model"   #wkdir, defined in ENSO_MSE.py

dirs_to_create = [ modeldir+"/PS",
                   modeldir+"/netCDF/ELNINO" ,
                   modeldir+"/netCDF/LANINA" ]

check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=2) 
    
####

