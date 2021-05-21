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

Common approaches to diagnose systematic errors involve the computation of metrics aimed at providing
an overall summary of the performance of the model in reproducing the particular variables of interest
in the study, normally tied to specific spatial and temporal scales.

However, the evaluation of model performance is not always tied to the understanding of the physical
processes that are correctly represented, distorted or even absent in the model world. As the physical
mechanisms are more often than not related to interactions taking place at multiple time and spatial scales,
cross-scale model diagnostic tools are not only desirable but required. Here, a recently proposed
circulation-based diagnostic framework is extended to consider systematic errors in both spatial and temporal
patterns at multiple timescales.

The framework, which uses a weather-typing dynamical approach, quantifies biases in shape, location and tilt of
modeled circulation patterns, as well as biases associated with their temporal characteristics, such as frequency
of occurrence, duration, persistence and transitions. Relationships between these biases and climate
teleconnections (e.g., ENSO and MJO) are explored using different models.


.. Explained_Variance_by_Q1&Q2_ERA5:

.. figure:: Explained_Variance_by_Q1&Q2_ERA5.pdf
   :align: left
   :width: 75 %

   Figure 1. Weather types (WT, or “flows”) in the MERRA reanalysis and in a suite of GFDL model experiments
   (for details, see Muñoz et al 2017). Some biases in magnitude and spatial rotation in WT3 and WT5 are indicated.

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

.. figure:: figure2.png
   :align: left
   :width: 75 %

   Figure 2. Atmospheric circulation, rainfall and sea-surface temperature (SST) patterns associated to weather type 5 (WT5).

.. _figure3:

.. figure:: figure3.png
   :align: left
   :width: 75 %

   Figure 3. A brief list of suggested metrics to evaluate flow-dependent temporal characteristics in models.
