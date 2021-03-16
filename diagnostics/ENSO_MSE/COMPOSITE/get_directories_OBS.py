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

obsdir = os.environ["ENSO_MSE_WKDIR"]+"/obs"
dirs_to_create =  [obsdir+"/PS" ]
check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=3)

obsdir = os.environ["ENSO_MSE_WKDIR_COMPOSITE"]+"/obs"

###  check the directories  , since we have pre-calculated data only directory 
##    which is needed is  obsdir+"/PS" 
dirs_to_create =  [obsdir+"/PS" ]

check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=3)
       
####
