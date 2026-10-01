import os
import sys

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)
from util import check_required_dirs

###   
###  def get_directories():
####

print( os.environ["ENSO_RWS_WKDIR"])
modeldir2 = os.environ["ENSO_RWS_WKDIR"]+"/model"    #defined in ENSO_MSE.py

dirs_to_create = [ modeldir2,
                   modeldir2+"/PS",
                   modeldir2+"/netCDF/ELNINO" ,
                   modeldir2+"/netCDF/LANINA" ]
 
###  create if necessary
check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=2)
####
