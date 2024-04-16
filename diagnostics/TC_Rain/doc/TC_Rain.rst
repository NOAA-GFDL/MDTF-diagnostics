.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank 
   line. This means the source code can be hard-wrapped to 80 columns for ease 
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

TC Rain Rate Azimuthal Average Documentation
============================================

Last update: 5/27/2022

This POD calculates and plots azimuthal averages for tropical cyclone (TC) rain rates 
from TC track data and model output precipitation. 


.. Underline with '-'s to make a second-level heading.

Version & Contact info
----------------------

- Version/revision information: version 1 (5/06/2020)
- PI Daehyun Kim, University of Washington, daehyun@uw.edu
- Developer/point of contact Nelly Emlaw, University of Washington, gnemlaw@uw.edu


Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 
Unless you've distributed your script elsewhere, you don't need to change this.

Functionality
-------------

In the current draft code, the data is loaded in first. The netcdf file for the total 
precipitation is loaded in through xarray. The TC track data is read in line by line from a 
txt file. 

Then the azimuthal average is calulated for a set of discrete radii by measuring the 
distance between a data point and the center of the storm for each snapshot. 

A plot showing TC rain rate as a function of radius is made for select snapshopts that 
reach 35-45 knot max wind speeds.

Required programming language and libraries
-------------------------------------------

matplotlib, numpy, netcdf, xarray, scipy

Required model output variables
-------------------------------

Total Precipitation 

TC Track Data (required: storm center latitude and longitufe, time for each snapshot,
optional: max windspeed, minimum central surface pressure, sst, etc)

References
----------

1. Kim, D., Y. Moon, S. Camargo, A. Sobel, A. Wing, H. Murakami, G. Vecchi, M. Zhao, 
and E. Page, 2018: Process-oriented diagnosis of tropical cyclones in high-resolution
climate models. J. Climate, 31, 1685–1702, https://doi.org/10.1175/JCLI-D-17-0269.1.

2. Moon, Y., D. Kim, S. Camargo, A. Wing, A. Sobel, H. Murakami, K. Reed, G. Vecchi, 
M. Wehner, C. Zarzycki, and M. Zhao, 2020: Azimuthally averaged wind and 
thermodynamic structures of tropical cyclones in global climate models and their 
sensitivity to horizontal resolution. J. Climate, 33, 1575–1595, 
https://doi.org/10.1175/JCLI-D-19-0172.1

3. Moon, Y., D. Kim, A. A. Wing, S. J. Camargo, M. Zhao, L. R. Leung, M. J. Roberts, 
D.-H. Cha, and J. Moon: An evaluation of global climate model-simulated tropical 
cyclone rainfall structures in the HighResMIP against the satellite observations, J.
Climate, Accepted.


More about this diagnostic
--------------------------

This POD calculates the azimuthally averaged precipitation rate of tropical cyclones (TCs) as 
a function of distance from the center of a TC from hourly (1,3,6, or 12 hr)  model 
precipitation output and model TC track output. 

In its current version the POD requires TC track input and cannot track TCs from model output 
alone. The track data must provide the latitude and longitude of the storm center and the 
time of track snapshot and optionally a characteristic of the storm at that snapshot to use
as a threshold to use the storm in the plotted average (here max wind is used and the default 
threshold is set to 35-45 knots to capture weak storms which meet the requirements to be 
considered a tropical cyclone - this threshold can be changed in the setting.jsonc file in the 
POD directory). 

The POD takes track data separated by basin. The basin longitude regions are determined by the 
ECMWF TC tracking standards and are as follows:
Atlantic Ocean (atl) : 100 - 350 W
Eastern Central Pacific (enp) : 0 - 100 W
Western North Pacific (wnp) : 100 - 180 E
Indian Ocean (nin : 40 - 100 E
South Indian Ocean (sin) : 30 - 90 E
Australian Ocean (aus) : 90 - 160 East
South Pacific Ocean (spc) : 160 E - 120 W
The latitude range for all basins is 0 - 30 N or S depending on the hemispehre. 

The output of this POD will be a plot of the azimuthally averaged rain rate (vertical axis) as a 
fuction of distance from the center of the storm (horizontal axis). The result should always be 
the highest rain rates at or just off center of the storm. Rain rate distributions with greatest 
inner-core rainfall tend to simulate stronger TCs more often. The distribution will vary greatly 
depending on model characteristics and threshold to determine snapshops used in average. For 
example was speculated in Moon et. al, 2020 that low resolution models require more energy to 
sustain themselves through induced precipitation. 
