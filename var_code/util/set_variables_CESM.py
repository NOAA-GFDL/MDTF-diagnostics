# This file is part of the util module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

import os

os.environ["hyam_var"] = "hyam"
os.environ["hybm_var"] = "hybm"  
os.environ["lat_coord"] = "lat"   
os.environ["lon_coord"] = "lon"
os.environ["lev_coord"] = "lev"
os.environ["time_coord"] = "time"   
os.environ["lat_var"] = "lat"   
os.environ["lon_var"] = "lon"
os.environ["time_var"] = "time"  

os.environ["ua_var"] = "U"   
os.environ["zg_var"] = "Z3"
os.environ["pr_var"] = "PRECT"  
os.environ["prc_var"] = "PRECC"
os.environ["prls_var"] = "PRECL"
os.environ["rlut_var"] = "FLUT"
os.environ["FSNTOA_var"] = "FSNTOA"
os.environ["tas_var"] = "TREFHT"
os.environ["ts_var"] = "TS"
os.environ["LANDFRAC_var"] = "LANDFRAC"
os.environ["tauu_var"] = "TAUX"
os.environ["CLDTOT_var"] = "CLDTOT"
os.environ["ICEFRAC_var"] = "ICEFRAC"
os.environ["ps_var"] = "PS"
os.environ["psl_var"] = "PSL"
os.environ["qa_var"] = "Q"   #Specific humidity
os.environ["u_var"] = "U"
os.environ["v_var"] = "V"
os.environ["u200_var"] = "U200"
os.environ["v200_var"] = "V200"
os.environ["u250_var"] = "U250"
os.environ["v250_var"] = "V250"
os.environ["u850_var"] = "U850"
os.environ["v850_var"] = "V850"
os.environ["omega500_var"] = "OMEGA500"
os.environ["z250_var"] = "Z250"
os.environ["pr_conversion_factor"] = "1000" # units in CAM (m/s), convert to kg/m2/s (mm/s)
os.environ["prc_conversion_factor"] = "1000" # units in CAM (m/s), convert to kg/m2/s (mm/s)
os.environ["prls_conversion_factor"] = "1000" # units in CAM (m/s), convert to kg/m2/s (mm/s)

# ------------------------------------------------------------------------
# Variables for Convective Transition Diagnostics module:
os.environ["ta_var"] = "T" # 3D temperature, units = K   
os.environ["prw_var"] = "prw" # Column Water Vapor (precipitable water vapor), units = mm (or kg/m^2)
os.environ["tave_var"] = "tave" # Mass-Weighted Column Average Tropospheric Temperature, units = K
os.environ["qsat_int_var"] = "qsat_int" # Vertically-Integrated Saturation Specific Humidity, units = mm (or kg/m^2)
# End - Variables for Convective Transition Diagnostics package
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------
# Variables name setting MJO Teleconnection Diagnostics module:(for USE of SpCCSM4 model)
# ------------------------------------------------------------------------------------------------------------------
#os.environ["pr_var"] = "prec" # Total precipitation (mm/day)   
#os.environ["rlut_var"] = "olr" # Outgoing longwave radiation (w/m2)
#os.environ["u850_var"] = "u850" #Zonal wind at 850-hPa level(m/s)
#os.environ["u250_var"] = "u250" # Zonal wind at 250-hPa level(m/s)
#os.environ["z250_var"] = "z3250" #Geopotential height at 250-hPa level(m)
os.environ["pr_conversion_mm/day"] = "86400000" # units in CAM (m/s), convert to (mm/day) required for plotting

# ------------------------------------------------------------------------
# Variables for mjo_diag (MJO propogation)
