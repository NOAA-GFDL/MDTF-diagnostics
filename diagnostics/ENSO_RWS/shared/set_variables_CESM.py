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
os.environ["va_var"] = "V"
os.environ["zg_var"] = "Z3"
os.environ["ta_var"] = "T" # 3D temperature, units = K
os.environ["qa_var"] = "Q"
os.environ["omega_var"] = "OMEGA"

os.environ["ts_var"] = "TS"

os.environ["pr_var"] = "PRECT"  
os.environ["pr_conversion_factor"] = "1000"   # units in CAM (m/s), convert to kg/m2/s (mm/s)
os.environ["ps_var"] = "PS"
os.environ["hfls_var"] = "LHFLX" 
os.environ["hfss_var"] = "SHFLX"

os.environ["prc_var"] = "PRECC"
os.environ["prls_var"] = "PRECL"
os.environ["rlut_var"] = "FLUT"
os.environ["FSNTOA_var"] = "FSNTOA"
os.environ["LANDFRAC_var"] = "LANDFRAC"
os.environ["tauu_var"] = "TAUX"
os.environ["CLDTOT_var"] = "CLDTOT"
os.environ["ICEFRAC_var"] = "ICEFRAC"
os.environ["psl_var"] = "PSL"
os.environ["u200_var"] = "U200"
os.environ["v200_var"] = "V200"
os.environ["u850_var"] = "U850"
os.environ["v850_var"] = "V850"
os.environ["omega500_var"] = "OMEGA500"

###  os.environ["pr_conversion_factor"] = "1000" # units in CAM (m/s), convert to kg/m2/s (mm/s)
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
