Surface Albedo Feedback
================================

Last update: 1/26/2021

This POD calculates the top of atmosphere radiative impact of surface albedo changes associated with Arctic sea ice loss under global warming. Four quantities are calculated: 

- **Climatological surface albedo**: the ratio of upwelling to downwelling shortwave radiation at the surface expressed as a :math:`\%`.

- **Radiative sensitivity**: the change in reflected shortwave radiation at the top of the atmosphere (in W :math:`m^{-2}`) per  0.01 increase in surface albedo. This quantity, akin to a surface albedo radiative kernel, is calculated from the climatological radiative fluxes at the top of atmosphere and surface using a simplified shortwave radiation model. Higher values generally correspond to less cloudy mean states.

- **Ice sensitivity** : the change in surface albedo normalized by the global mean surface temperature change. This quantity is equal the change in sea ice concentration times the average albedo contrast between ocean and sea ice. The model values are calculated from :math:`4XCO_{2}` simulations and observations are calculated from trends over the historic satellite record.

- **Radiative impact of sea ice loss** : the change in top of atmosphere radiation (positive downward) due to changes in surface albedo normalized by global mean surface temperature change, in in W :math:`m^{-2}` :math:`K^{-1}`. This quantity is equal to the product of the **Radiative sensitivity** and **Ice sensitivity**. The global and annual average of this quantity is equal to the ice albedo feedback of the Arctic.

All calculated quantities are averages over the boreal summer, defined as May, June, July and August.
  

Version & Contact info
----------------------

.. '-' starts items in a bulleted list: 
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#bullet-lists

Here you should describe who contributed to the diagnostic, and who should be
contacted for further information:

- Version 1 (1/26/2021)
- PI (Cecilia Bitz, University of Washington, bitz@uw.edu)
- Developer/point of contact (Aaron Donohoe, University of Washington, adonohoe@u.washington.edu)
- Other contributors: Ed Blanchard, Wei Cheng, Lettie Roach  

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt). 

Functionality
-------------

Model climatological albedo and radiative sensitivity is calculated from the pre-industrial control simulation climatological radiative fluxes at the top of atmosphere and surface. Observational calculations use the CERES EBAF top of atmosphere and surface radiative fluxes (version 4.0)

Model ice sensitivity is calculated from the climatological surface albedo (ratio of upwelling to downwelling surface shortwave fluxes) of the :math:`4XCO_{2}` simulations minus that in the pre-industrail divided by the annual and global mean surface temperature change. Observational ice sensitivity estimates are from a developer provided file and are a blended product of historical trends in sea ice concentrations provided by the National Snow and surface albedo provided by the Advanced Very High Resolution Radiometer (AVHRR) Polar Pathfinder (APP-X).

The radiative sensitivity is the local product of the radiative sensitivity and ice sensitivity. 
    

Required programming language and libraries
-------------------------------------------

Standard Python libraries.

Required model output variables
-------------------------------

Monthly mean shortwave radiative fluxes at the top of atmosphere and surface (FSDT, FSUT, FSDS, FSUS) and surface air temperature (TAS) from pre-industrial simulations and abrupt :math:`4XCO_{2}` simulations are used.  


References
----------

1. A. Donohoe, E. Blanchard-Wrigglesworth, A. Schweiger and P.J. Rasch (2020): The Effect of Atmospheric Transmissivity on Model and Observational Estimates of the Sea Ice Albedo Feedback. *J. Climate*, **33** (12), 5743-5765, 
` <https://journals.ametsoc.org/view/journals/clim/33/13/jcli-d-19-0674.1.xml>