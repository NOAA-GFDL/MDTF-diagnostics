# This file is part of the MJO_suite module of the MDTF code package (see LICENSE.txt)

#============================================================
# EOF of 500hPa Height Diagnostics
# Sample code to call NCL from python 
#============================================================

import os
import subprocess
import time

# ============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
# ============================================================


def generate_ncl_plots(nclPlotFile):
    """generate_plots_call - call a nclPlotFile via subprocess call
   
    Arguments:
    nclPlotFile (string) - full path to ncl plotting file name
    """
    # check if the nclPlotFile exists - 
    # don't exit if it does not exists just print a warning.
    try:
        pipe = subprocess.Popen(['ncl {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0].decode()
        print('NCL routine {0} \n {1}'.format(nclPlotFile,output))            
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING', e.errno, e.strerror)
    return 0

# ============================================================
# Call NCL code here
# ============================================================


if not os.path.exists(os.path.join(os.environ['DATADIR'], 'day')):
    os.makedirs(os.path.join(os.environ['DATADIR'], 'day'))

print("OBTAINING DAILY OUTPUT")
generate_ncl_plots(os.environ["POD_HOME"]+"/daily_netcdf.ncl")

print("COMPUTING DAILY ANOMALIES")
generate_ncl_plots(os.environ["POD_HOME"]+"/daily_anom.ncl")

print("COMPUTING MJO EOF (may take a while for long time samples)")
generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_EOF.ncl")

print("MJO lag plots")
generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_lag_lat_lon.ncl")

print("MJO spectra")
generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_spectra.ncl")

if os.path.isfile( os.environ["WORK_DIR"]+"/model/netCDF/MJO_PC_INDEX.nc"):
    print("WARNING: MJO_PC_INDEX.nc already exists. Not re-running.")
else:
    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_EOF_cal.ncl")
   
print("MJO life cycle composite")

# This has a loop to generate two sets of figures, on with -1*PC
generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_life_cycle.ncl")

generate_ncl_plots(os.environ["POD_HOME"]+"/mjo.ncl")

print("MJO_suite.py finished.")
