# Extra-tropical Cyclone Diagnostic Tool 
## Created by Jeyavinoth Jeyaratnam (The City College of New York, CUNY)

Last Modified: Jan 24th, 2020

# Custom Notes:

All needed data is in /localdrive/drive6/.

the code for the converts are in /localdrive/drive10/mcms\_tracker/data\_preprocessing




# Modules

This code has many parts (the main driver codes for each part is in the main folder):

1. Tracker (run\_tracker.py)- Tracks ETCs using Re-analysis/Model Data
2. Statistics (run\_track\_stats.py) - Diagnositics on the tracked cyclones (i.e. track density, feature density, genesis, lysis).
3. Composite Analysis (run\_composites.py) - Creates figures of composites for the selected variables.
4. Front Detection (run\_front\_detection.py) - Tracks ETC fronts on Re-analysis/Model Data
5. Transect Analysis (run\_transect.py) - Diagnostics on the tracked fronts (i.e. transect anlaysis based on front)
6. TODO: create front density plots

# Tracker

** This Tracker module has to be run for this entire diagnostic tool to work. **


To get the tracker running, check the tracker\_readme.md file. All the necessary steps to install the tracker is provided here.

After setting up the python environment, chnage the defines.py file to match your local system.

You can then run the following code:

python run\_tracker.py

## Variables needed: 
* Lon and Lat values must for all variables must be the left edges, NOT the middle value of the grid box

### Topography file 
* variable 'hgt' should be in meters
* variable 'lsm' should be in fractional value in the range 0-1

### Sea-level pressure (SLP)
* Naming connvention should be slp.{year}.nc
* The variable name inside the netcdf file must match the varname in the filename.
* Lon should be from 0 to 360 (though -180 to 180 should work, but not thoroughly tested)
* Lat can be from -90 to 90 or 90 to -90 (again latter not tested thoroughly)
* Units must be mb/hPa
* Fillvalues assumed to be np.nan
* Time variable should have attribute "delta\_t" set in the format YYYY-MM-DD hh:mm:ss
* Units of time should be 'proleptic\_gregorian' or 'julian' or 'standard', if not specified it is * assumed to be 'standard'. ***hours since start of the current year.***

# Front Detection

The front detection does not need any settings in defines.py, unless you want to detect fronts only for a subset of years.

## Variables needed:
* Naming connvention should be {var\_name}.{year}.nc
* The variable name inside the netcdf file must match the varname in the filename.
* U, V at 850 hPa [m/s]
* Z at all levels [m]
* T at all levels [k]
* mean sea level pressure [hPa/mb]
* Surface Pressure [Pa]
* time variable should be the same as above (units should be hours since start of year)

# Transect Analysis

You have to provide the list of variables you need to run the transect analysis in defines.py file. 
And specify the hemispheres in which you want to run the analysis on.

This code automatically separates land and ocean for you.

## Variables needed:
* Naming connvention should be {var\_name}.{year}.nc
* The variable name inside the netcdf file must match the varname in the filename.
* Provide variables in the format [time x level x lat x lon], and the appropriate units that you want the outputs in.

# Composite Analysis

You have to provide the list of variables you need to run the composite analysis in defines.py file.
And specify the hemispheres in which you want to run the analysis on.

The default area to create composites are 100 km x 100 km. You can change this to your liking in defines.py, under area and circ.

This code automatically separates land and ocean for you.

## Variables needed:
* Naming connvention should be {var\_name}.{year}.nc
* The variable name inside the netcdf file must match the varname in the filename.
* Provide variables in the format [time x lat x lon], and the appropriate units that you want the outputs in.


**Notes:**

Make sure the create\_matlab\_dictionaries is set to True, if you want to run the other modules. You need the temporary matfiles for this to work.
