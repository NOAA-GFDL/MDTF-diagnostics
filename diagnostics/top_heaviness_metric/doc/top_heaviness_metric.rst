Top-Heaviness Metric Diagnostic Documentation
================================

Last update: 5/21/2021

The vertical profiles of diabatic heating have important implications for large-scale dynamics, especially for the coupling between the large-scale atmospheric circulation and precipitation processes. We adopt an objective approach to examine the top-heaviness of vertical motion, which is closely related to the heating profiles and a commonly available model output variable. The diagnostic metric can also be used to evaluate the diabatic heating profile.

Version & Contact info
----------------------

.. '-' starts items in a bulleted list:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#bullet-lists

- Version/revision information: version 1.0 (5/21/2021)
- PI (Jiacheng Ye, Department of Atmospheric Sciences UIUC, jye18@illinois.edu)
- Developer/point of contact (Jiacheng Ye, jye18@illinois.edu and Zhuo Wang, zhuowang@illinois.edu, DAS UIUC)

.. Underline with '^'s to make a third-level heading.

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

The currently package consists of following functionalities:

(1) Calculation of percentage of variance explained by two base functions (idealized deep convection profile, idealized deep stratiform profile)

(2) Calculation of top-heaviness ratio (O2/O1)

(3) Other analysis (to be added soon)

(**) cropping.py can be referenced if code is needed to either shift the grid of your data
or to crop your data to a specified region

As a module of the MDTF code package, all scripts of this package can be found under
``mdtf/MDTF_$ver/diagnostics/top_heaviness_ratio``

Required programming language and libraries
-------------------------------------------

Python3 packages: "netCDF4", "xarray", "numpy", "pandas", "sklearn", "cartopy", "matplotlib",
"numba", "datetime", "typing"

Required model output variables
-------------------------------

(1) Geopotential height anomalies at 500 hPa (units: HPa, daily resolution)

(2) Rainfall (units: mm/day, daily resolution)

(3) Temperature (units: Celsius, daily resolution)


References
----------

.. _ref-Muñoz1:

Back, L. E., Hansen, Z., & Handlos, Z. (2017). Estimating vertical motion profile top-heaviness: Reanalysis compared to satellite-based observations and stratiform rain fraction. Journal of the Atmospheric Sciences, 74(3), 855-864. https://doi.org/10.1175/JAS-D-16-0062.1

Jiacheng and Zhuo's paper is under developing...

More about this diagnostic
--------------------------

Q1 and Q2 (Figure 1) are two prescribed base functions. Q1 is characterized by idealized deep convection profile and Q2 is characterized by idealized deep stratiform profile. The concept of percentage of explained variance is similar to that of EOF analysis where we can regard Q1 and Q2 as two leading EOFs. Through such approximation, figure 2 reveals that using these two base functions can help tp explain most of the tropical and subtropical ocean. Top-heaviness ratio in figure 3 shows that the WP is characterized by more top-heavy circulation while EP and ATL are described by more bottom-heavy circulation. 

The top-heaviness is a useful tool to diagnose the coupling between diabatic process and large-scale circulation. If the model is not able to reproduce correct pattern of top-heaviness ratio, this would imply potential deficiencies in deep convection and stratiform scheme. In the future POD develop, we are considering adding shallow convection as a third base function. By doing so will enable us to further investigate the bias source of tropical and subtropical predicability. 

.. Explained_Variance_by_Q1&Q2_ERA5:

.. figure:: Q1&Q2_R.png
   :align: center
   :width: 75 %
   

   Figure 1. Left: Q1 and Q2; Right: Vertical motion profiles constructed from varying top-heviness ratio (r; r=-1: dark blue, r=1: dark red).
   
For example, :ref:`Figure 1 <figure1>` exhibits atmospheric circulation patterns for North Eastern North America,
as analyzed by :ref:`Muñoz (2017) <ref-Muñoz1>`, in a reanalysis and in different model experiments produced using GFDL models
LOAR and FLOR. The POD permits for the calculation of the atmospheric circulation patterns :ref:`Figure 1 <figure1>` as well as
for the rainfall and temperature anomaly fields related to each “flow”, computed via a composite analysis.
It’s also possible to identify the typical sea-surface temperature patterns related to the occurrence of each
pattern :ref:`Figure 2 <figure2>`.

Beyond the analysis of spatial biases in the modeled atmospheric circulation patterns, the POD can help assess biases
in temporal characteristics. A variety of metrics have been suggested by Muñoz et al (2017), and are summarized
in :ref:`Figure 3 <figure3>`.

.. _figure2:

.. figure:: Explained_Variance_by_Q1&Q2_ERA5.png
   :align: left
   :width: 75 %

   Figure 2. Percentage of variance explained by Q1 and Q2.

.. _figure3:

.. figure:: Top-Heaviness_Ratio_July_ERA5.png
   :align: left
   :width: 75 %

   Figure 3. Top-Heaviness Ratio.  
