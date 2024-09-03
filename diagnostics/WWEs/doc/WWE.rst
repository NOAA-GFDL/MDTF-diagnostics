.. This is a comment in RestructuredText format (two periods and a space).
Westerly Wind Event Diagnostic Documentation
================================

Last update: 08/27/2024

The zonal surface stress diagnostic makes a longitude vs. time plot of
the equator zonal surface stress. Observations from TropFlux are
compared to climate model output.

Version & Contact info
----------------------

- PI: Emily M. Riley Dellaripa (Emily.Riley@colostate.edu), Colorado State University
- Current Developer: Emily M. Riley Dellaripa (Emily.Riley@colostate.edu), Colorado State University
- Contributors: Charlotte A. DeMott (CSU); Eric D. Maloney (CSU)


Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 

Functionality
-------------

The main script generates the longitude vs. time plot of zonal surface
stress.

Required programming language and libraries
-------------------------------------------

This POD is written in Python 3.10 and requires the os, numpy, xarray,
and matplotlib Python packages. These dependencies are included in the
python3_base environment provided by the automated installation script
for the MDTF Framework.

Required model output variables
-------------------------------

This POD requires the zonal wind stress (TAUX) in 3D (time-lat-lon) in
units of Pa.

References
----------
1.Riley Dellaripa et al. (2024): Evaluation of Equatorial Westerly
Wind Events in the Pacific Ocean in CMIP6 Models. *J. Climate*,
`doi: 10.1175/JCLI-D-23-0629.1 < https://doi.org/10.1175/JCLI-D-23-0629.1>`__.


More about this diagnostic
--------------------------


Links to external sites
^^^^^^^^^^^^^^^^^^^^^^^


More references and citations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
