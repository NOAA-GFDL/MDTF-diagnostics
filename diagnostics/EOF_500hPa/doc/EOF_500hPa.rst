EOF of Geopotential Height Diagnostic Module From NCAR
======================================================
Last update: 03/11/2019

Contact info
------------
- Current Developer: Dani Coleman (​bundy@ucar.edu​), NCAR
- Contributors: Dennis Shea, Andrew Gettleman, Jack Chen (NCAR)

This computes the climatological anomalies of 500 hPa geopotential height, then calculates the EOFs using ​NCL's eofunc​. The code is in ​NCL​ and requires model input: 

1. monthly averaged surface pressure (ps),
2. monthly averaged geopotential height (zg).

- Generates a netcdf file of climatological anomalies of 500 hPa geopotential height (compute_anomalies.ncl) 
- Calculates and plot EOFs of North Atlantic (eof_natlantic.ncl) and North Pacific regions using NCL function eofunc
- Uses pre-made figures of eofs of NCEP observational data for comparison.

Open source copyright agreement
-------------------------------
This package is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------
All scripts can be found at: ``mdtf/MDTF_$ver/var_code/EOF_500hPa``

1. Make anomalies (compute_anomalies.ncl)

2. Calculated and plots EOFs in N. Atlantic (eof_natlantic.ncl) and N. Pacific
(eof_npacific.ncl)

Preprocessed observational data from NCEP as gif images are located in
``mdtf/``inputdata/obs_data/EOF_500hPa``

Place your input data at: ``inputdata/model/$model_name/day``
index.html can be found at: ``mdtf/MDTF_$ver/wkdir/MDTF_$model_name``

Required Programing Language and libraries
------------------------------------------
All these scripts required NCAR Command Language Version 6.3.0 or higher

Required input data to the module:

1) Monthly averaged surface pressure (ps)
2) Monthly averaged geopotential height (zg)

References
----------

None

More About the Diagnostic
-------------------------

