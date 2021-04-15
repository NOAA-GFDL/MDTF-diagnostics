#driver file
import os
import glob

#specifying file structure for each var
os.environ["PREC_FILE"] = "*."+os.environ["prec_var"]+".day.nc"
os.environ["HGT_FILE"] = "*."+os.environ["hgt_var"]+".day.nc"
os.environ["TAS_FILE"] = "*."+os.environ["t_ref_var"]+".day.nc"

os.environ["MODEL_OUTPUT_DIR"]=os.environ["DATADIR"]+"/1hr"

missing_file=0
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["PREC_FILE"]))==0:
    print("Required Precipitation data missing!")
    missing_file=1
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["HGT_FILE"]))==0:
    print("Required Geopotential heightdata missing!")
    missing_file=1
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["TAS_FILE"]))==0:
    print("Required temperature data missing!")
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
