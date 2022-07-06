Precipitation Buoyancy Diagnostic Package
=========================================

The precipitation-buoyancy diagnostics POD is used to assess the thermodynamic sensitivity of model precipitation fields. 

Scientific basis
----------------------
Observations show that over tropical oceans, a lower tropospheric buoyancy metric :math:`B_L` has a strong relationship to precipitation ( :ref:`Ahmed and Neelin 2018 <ref-AN18>`, :ref:`Ahmed et al. 2020 <ref-AAN>`). This buoyancy metric can further be decomposed into two components:

1. A measure of undilute buoyancy termed CAPE :subscript:`L`, which measures the difference between boundary layer moist enthalpy and the free-tropospheric temperature. If convection were non-entraining, this would be the dominant thermodynamic measure affecting precipitation. 
2. A measure of lower-free tropospheric sub-saturation SUBSAT :subscript:`L`, which is computed as a departure from saturation in the lower free-troposphere. The influence of entrainment on convection is expressed through this measure.

In observations (ERA re-analysis and TRMM precipitation), precipitation appears to about equally sensitive to CAPE :subscript:`L` and SUBSAT :subscript:`L`. However, climate models can show diverging behavior. To measure this relative sensitivity of precipitation to CAPE :subscript:`L` and SUBSAT :subscript:`L`, a vector :math:`\gamma_{CS}` is introduced. This has a direction that is expressed in degrees and takes values ranging from 0 to 90. 


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

 .. _ref-AN18: 

   1. Ahmed, F., & Neelin, J. D. (2018). Reverse engineering the tropical precipitation–buoyancy relationship. Journal of the Atmospheric Sciences, 75(5), 1587-1608.`__.

 .. _ref-AAN: 

  2. Ahmed, F., Adames, Á. F., & Neelin, J. D. (2020). Deep convective adjustment of temperature and moisture. Journal of the Atmospheric Sciences, 77(6), 2163-2186.`__.

More about this diagnostic
--------------------------
