.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank 
   line. This means the source code can be hard-wrapped to 80 columns for ease 
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

TC Rain Rate Azimuthal Average Documentation
================================

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
precipitatin is loaded in through xarray. The TC track data is read in line by line from a 
txt file. 

Then the azimuthal average is calulated for a set of discrete radii by measuring the 
distance between a data point and the center of the storm for each snapshot. 

A plot showing TC rain rate as a function of radius is made for select snapshopts that 
reach 30-40 knot max wind speeds.

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

Will concult advisor to find what referene would be good to include here. 

More about this diagnostic
--------------------------

""

