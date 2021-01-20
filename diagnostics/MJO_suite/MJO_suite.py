# This file is part of the MJO_suite module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

#============================================================
# EOF of 500hPa Height Diagnostics
# Sample code to call NCL from python 
#============================================================

import os
import subprocess
import time

#============================================================
# generate_ncl_plots - call a nclPlotFile via subprocess call
#============================================================
def generate_ncl_plots(nclPlotFile):
    """generate_plots_call - call a nclPlotFile via subprocess call
   
    Arguments:
    nclPlotFile (string) - full path to ncl plotting file name
    """
    # check if the nclPlotFile exists - 
    # don't exit if it does not exists just print a warning.
    try:
        pipe = subprocess.Popen(['ncl {0}'.format(nclPlotFile)], shell=True, stdout=subprocess.PIPE)
        output = pipe.communicate()[0]
        print('NCL routine {0} \n {1}'.format(nclPlotFile,output))            
        while pipe.poll() is None:
            time.sleep(0.5)
    except OSError as e:
        print('WARNING',e.errno,e.strerror)

    return 0

# HACK for merging in SPEAR code before we have general level extraction working
if '200' in os.environ.get('u200_var','') and '200' in os.environ.get('v200_var',''):
    print('\tDEBUG: assuming 3D u,v ({},{})'.format(
        os.environ['u200_var'], os.environ['v200_var']
    ))
    os.environ['MDTF_3D_UV'] = '1'
else:
    print('\tDEBUG: assuming 4D u,v ({},{})'.format(
        os.environ['u200_var'], os.environ['v200_var']
    ))
    os.environ['MDTF_3D_UV'] = '0'

#============================================================
# Call NCL code here
#============================================================
print("OBTAINING DAILY OUTPUT")
generate_ncl_plots(os.environ["POD_HOME"]+"/daily_netcdf.ncl")

print("COMPUTING DAILY ANOMALIES")
generate_ncl_plots(os.environ["POD_HOME"]+"/daily_anom.ncl")

print("COMPUTING MJO EOF")
generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_EOF.ncl")

print("MJO lag plots")
generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_lag_lat_lon.ncl")

print("MJO spectra")
generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_spectra.ncl")

if os.path.isfile( os.environ["WK_DIR"]+"/model/netCDF/MJO_PC_INDEX.nc"):
    print("WARNING: MJO_PC_INDEX.nc already exists!")
else:
    generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_EOF_cal.ncl")
   
print("MJO life cycle composite")
generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_life_cycle.ncl")
generate_ncl_plots(os.environ["POD_HOME"]+"/mjo_life_cycle_v2.ncl")

generate_ncl_plots(os.environ["POD_HOME"]+"/mjo.ncl")

