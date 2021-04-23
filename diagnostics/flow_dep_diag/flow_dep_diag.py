#driver file
import os
import glob

os.system("python3 "+os.environ["POD_HOME"]+"/"+"WeatherTypes.py")

#specifying file structure for each var
#os.environ["PRECT_FILE"] = "*."+os.environ["PRECT_var"]+".day.nc"
#os.environ["Z250_FILE"] = "*."+os.environ["Z250_var"]+".day.nc"
#os.environ["T250_FILE"] = "*."+os.environ["T250_var"]+".day.nc"

#os.environ["MODEL_OUTPUT_DIR"]=os.environ["DATADIR"]+"/day"

#missing_file=0
#if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["PRECT_FILE"]))==0:
#    print("Required Precipitation data missing!")
#    missing_file=1
#if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["Z250_FILE"]))==0:
#    print("Required Geopotential height data missing!")
#    missing_file=1
#if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["T250_FILE"]))==0:
#    print("Required temperature data missing!")
#    missing_file=1

#if missing_file==1:
#    print("Flow-Dependent, Cross-Timescale Model Diagnostics Package will NOT be executed!")
#else:

    ##### Functionalities in Diagnostic Package #####
    # ======================================================================

    #  See WeatherTypes.py for detailed info
#    try:
#        os.system("python3 "+os.environ["POD_HOME"]+"/"+"WeatherTypes.py")
#    except OSError as e:
#        print('WARNING',e.errno,e.strerror)
#        print("**************************************************")
#        print("Flow-Dependent, Cross-Timescale Model Diagnostics (WeatherTypes.py) is NOT Executed as Expected!")
#        print("**************************************************")
