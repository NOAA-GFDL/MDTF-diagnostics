Precipitation Buoyancy Diagnostic Package
========================================

The precipitation-buoyancy diagnostics module relates precipitation to a
measure of lower-tropospheric averaged buoyancy and its two components:
a measure of lower-tropospheric Convective Available Potential Energy (CAPE<sub>L</sub>) and
lower-tropospheric sub saturation (SUBSAT<sub>L</sub>). The module evaluates the
model precipitation sensitivity to thermodynamic variations by
conditionally-averaging tropical oceanic precipitation by CAPE<sub>L</sub> and
SUBSAT<sub>L</sub>, and visualizing the result in 3D as a precipitation surface. A
metric called &gamma;<sub>Tq</sub> assesses the CAPE<sub>L</sub> vs. SUBSAT<sub>L</sub> precipitation sensitivity. This metric is
used to assess model performance compared to observations and a suite of
CMIP6 models.

Version & Contact info
----------------------

- Fiaz Ahmed (UCLA)
- PI: J. David Neelin (UCLA; neelin@atmos.ucla.edu)
- Current developer: Fiaz Ahmed

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This package is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

The currently package consists of following functionalities:

#. Precipitation Buoyancy curve and surface


As a module of the MDTF code package, all scripts of this package can be found under the `precipitaton_buoyancy_diag`

Required programming language and libraries
-------------------------------------------

The is package is written in Python 3.7, and requires the following Python packages:
numpy, scipy, matplotlib, cython, numba, & xarray. These Python packages are already included in the standard Anaconda installation.


Required model output variables
-------------------------------

The following high-frequency model fields are required\:

1. Precipitation rate 

2. Vertical profile of temperature

3. Vertical profile of specific humidity

4. Surface pressure (optional)

References
----------


More about this diagnostic
--------------------------

