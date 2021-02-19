#driver file
import os
import glob

#specifying file structure for each var
os.environ["pr_file"] = "*."+os.environ["pr_var"]+".1hr.nc"
os.environ["hgt_file"] = "*."+os.environ["hgt_var"]+".1hr.nc"
os.environ["t2m_file"] = "*."+os.environ["t2m_var"]+".1hr.nc"

os.environ["MODEL_OUTPUT_DIR"]=os.environ["DATADIR"]+"/1hr"

missing_file=0
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["pr_file"]))==0:
    print("Required Precipitation anomaly data missing!")
    missing_file=1
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["hgt_file"]))==0:
    print("Required Geopotential height anomaly data missing!")
    missing_file=1
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["t2m_file"]))==0:
    print("Required temperature anomaly data missing!")
    missing_file=1

if missing_file==1:
    print("Flow-Dependent, Cross-Timescale Model Diagnostics Package will NOT be executed!")
else:

    ##### Functionalities in Diagnostic Package #####
    # ======================================================================

    #  See WeatherTypes.py for detailed info
    try:
        os.system("python3 "+os.environ["POD_HOME"]+"/"+"WeatherTypes.py")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("Flow-Dependent, Cross-Timescale Model Diagnostics (WeatherTypes.py) is NOT Executed as Expected!")		
        print("**************************************************")