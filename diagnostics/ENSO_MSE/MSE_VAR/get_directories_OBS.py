import numpy as np
import os.path
import math
import sys

from util import check_required_dirs

###   
###  def get_directories():

outdir  = os.environ["ENSO_MSE_WKDIR_MSE_VAR"]+"/obs"   #wkdir, defined in ENSO_MSE.py, figures created by COMPOSITE for obs
dirs_to_create = [ outdir+"/PS",
                   outdir+"/netCDF/ELNINO" ,
                   outdir+"/netCDF/LANINA" ]

check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=2) 

###  DRB: sym link to obs no longer necessary because everything is written/read to/from WKDIR
