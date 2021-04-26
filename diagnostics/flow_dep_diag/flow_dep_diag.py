#driver file
import os
import glob

#os.system("python3 "+os.environ["POD_HOME"]+"/"+"WeatherTypes.py")

os.environ["MODEL_OUTPUT_DIR"]=os.environ["DATADIR"]+"/1hr"
if not os.path.exists(os.environ["MODEL_OUTPUT_DIR"]):
    os.makedirs(os.environ["MODEL_OUTPUT_DIR"])

missing_file=0
if len(glob.glob(os.environ["PRECT_FILE"]))==0:
    print("Required Precipitation data missing!")
    missing_file=1
if len(glob.glob(os.environ["Z250_FILE"]))==0:
    print("Required Geopotential height data missing!")
    missing_file=1
if len(glob.glob(os.environ["T250_FILE"]))==0:
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

    print("**************************************************")
    print("Flow-Dependent, Cross-Timescale Model Diagnostics (WeatherTypes.py) Executed!")
    print("**************************************************")
