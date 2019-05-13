# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

import os

os.environ["lat_coord"] = "lat"
os.environ["lon_coord"] = "lon"   
os.environ["lev_coord"] = "pfull" # or "pfull" # must be on pressure levels (hPa)
os.environ["time_coord"] = "time"   
os.environ["lat_var"] = "lat"   
os.environ["lon_var"] = "lon"
os.environ["time_var"] = "time"
os.environ["ps_var"] = "PS"
os.environ["pr_conversion_factor"] = "1" #units = m/s
os.environ["prc_conversion_factor"] = "1" #units = m/s
os.environ["prls_conversion_factor"] = "1" #units = m/s

# ------------------------------------------------------------------------
# Variables for Convective Transition Diagnostics module:
os.environ["ta_var"] = "ta" # 3D temperature, units = K   
os.environ["prw_var"] = "prw" # Column Water Vapor (precipitable water vapor), units = mm (or kg/m^2)
os.environ["tave_var"] = "tave" # Mass-Weighted Column Average Tropospheric Temperature, units = K
os.environ["qsat_int_var"] = "qsat_int" # Vertically-Integrated Saturation Specific Humidity, units = mm (or kg/m^2)
# End - Variables for Convective Transition Diagnostics package
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# Variables for Xianan Jiang mjo diagnostic
os.environ["pr_var"]   = "precip" # 3D temperature, units = K   
os.environ["qa_var"]   = "sphum" # 3D temperature, units = K   
#os.environ["prw_var"] = "prw" # Column Water Vapor (precipitable water vapor), units = mm (or kg/m^2)
os.environ["prw_var"]  = "WVP" #Column integrated water vapor, kg/m2

print "DRBDBG set_variables_AM4 setting pr_var ",os.environ["pr_var"]
