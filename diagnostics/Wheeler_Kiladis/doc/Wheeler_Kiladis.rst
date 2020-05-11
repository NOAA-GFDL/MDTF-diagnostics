Wavenumber Frequency Spectra Diagnostic Module From NCAR
========================================================
Last update: 03/11/2019

Produces wavenumber-frequency spectra for OLR, Precipitation, 500hPa Omega, 200hPa wind
and 850hPa Wind.

Contact info
------------

- Current Developer: Dani Coleman (​bundy@ucar.edu​), NCAR
- Contributors: Dennis Shea, Andrew Gettleman, Jack Chen, Rich Neale (NCAR)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This package is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

Python code calls NCL wkSpaceTime_driver.ncl code for each of the variables in turn.
Preprocessed observational data in the form of gif figures from NCEP precipitation, OLR,
Omega and winds, and TRMM precipitation are in the
``mdtf/inputdata/obs_data/Wheeler_Kiladis directory``
Place your input data at: ``mdtf/inputdata/model/$model_name/day``
index.html can be found at: ``mdtf/MDTF_$ver/wkdir/MDTF_$model_name``

Required Programing Language and libraries
------------------------------------------

All these scripts required NCAR Command Language Version 6.3.0 or higher

Required input data to the module
---------------------------------

Daily U200, U850, OMEGA500, OLR, PRECT

References
----------

   .. _1:

1. Wheeler, Matthew, and George N. Kiladis. “Convectively Coupled Equatorial Waves: Analysis of Clouds and Temperature in the Wavenumber–Frequency Domain.” ​*Journal of the Atmospheric Sciences​* **56**, no. 3 (February 1, 1999): 374–99. https://doi.org/10.1175/1520-0469(1999)056<0374:CCEWAO>2.0.CO;2​.


More About the Diagnostic
-------------------------
