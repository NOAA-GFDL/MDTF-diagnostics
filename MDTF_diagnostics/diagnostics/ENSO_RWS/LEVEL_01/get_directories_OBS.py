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

obsdir = os.environ["ENSO_RWS_WKDIR"]+"/obs"
dirs_to_create =  [obsdir,
                   obsdir+"/PS" ]
check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=3)

####
