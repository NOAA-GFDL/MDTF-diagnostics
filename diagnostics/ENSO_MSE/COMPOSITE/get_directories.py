import os
import sys

shared_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'shared'
)
sys.path.insert(0, shared_dir)
from util import check_required_dirs

modeldir = os.environ["ENSO_MSE_WKDIR"]+"/model" #defined in ENSO_MSE.py
dirs_to_create = [modeldir,
                  modeldir+"/PS"]
check_required_dirs( already_exist =[], create_if_nec = dirs_to_create, verbose=2)
# defined in ENSO_MSE.py
mse_wkdir_composite = os.environ["ENSO_MSE_WKDIR_COMPOSITE"]
print("ENSO_MSE_WKDIR_COMPOSITE:", mse_wkdir_composite)
modeldir2 = os.path.join(mse_wkdir_composite,"model")

dirs_to_create = [modeldir2,
                  modeldir2+"/PS",
                  modeldir2+"/netCDF/DATA" ,
                  modeldir2+"/netCDF/CLIMA" ,
                  modeldir2+"/netCDF/ELNINO" ,
                  modeldir2+"/netCDF/LANINA" ,
                  modeldir2+"/netCDF/24MONTH_ELNINO" ,
                  modeldir2+"/netCDF/24MONTH_LANINA" ,
                  modeldir2+"/netCDF/24MONTH_ELNINO/BIN" ,
                  modeldir2+"/netCDF/24MONTH_LANINA/BIN"]

check_required_dirs( already_exist =[], create_if_nec=dirs_to_create, verbose=2)

