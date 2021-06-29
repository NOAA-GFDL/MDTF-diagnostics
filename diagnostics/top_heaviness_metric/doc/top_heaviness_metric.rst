Top-Heaviness Metric Diagnostic Documentation
================================

Last update: 5/30/2021

The vertical profiles of diabatic heating have important implications for large-scale dynamics, especially for the coupling between the large-scale atmospheric circulation and precipitation processes. We adopt an objective approach to examine the top-heaviness of vertical motion (Back et al. 2017), which is closely related to the heating profiles and a commonly available model output variable. The diagnostic metric can also be used to evaluate the diabatic heating profile.

Version & Contact info
----------------------

.. '-' starts items in a bulleted list:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#bullet-lists

- Version/revision information: version 1.0 (6/28/2021)
- Developer/point of contact (Jiacheng Ye, jye18@illinois.edu, DAS UIUC; Zhuo Wang, zhuowang@illinois.edu, DAS UIUC)

.. Underline with '^'s to make a third-level heading.

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

The current package consists of following functionalities:

(1) Calculation of the fractional variance of vertical velocity at each grid point explained by two base functions - Q1 (~= idealized deep convection profile) and Q2 (~= idealized deep stratiform profile)

(2) Calculation of the top-heaviness ratio (O2/O1)

As a module of the MDTF code package, all scripts of this package can be found under
``mdtf/MDTF_$ver/diagnostics/top_heaviness_ratio``

Required programming language and libraries
-------------------------------------------

Python3 packages: "netCDF4", "xarray", "numpy", "scipy", "matplotlib", "basemap"

Required model output variables
-------------------------------

3-D spatial dimension Omega (units: Pa/s), which can be either the monthly mean in a certain year or the long-term monthly mean (or seasonal) mean.


References
----------

.. _ref-Muñoz1:

Back, L. E., Hansen, Z., & Handlos, Z. (2017). Estimating vertical motion profile top-heaviness: Reanalysis compared to satellite-based observations and stratiform rain fraction. Journal of the Atmospheric Sciences, 74(3), 855-864. https://doi.org/10.1175/JAS-D-16-0062.1

Jiacheng and Zhuo's paper is under developing...

More about this diagnostic
--------------------------

Q1 and Q2 (Figure 1a) are two prescribed base functions. Following Back et al. (2017), Q1 as a half sine function, and Q2 as a full sine function, which represent the idealized deep convection profile and the idealized deep stratiform profile, respectively. The vertical velocity can be approximated by Q1 and Q2:
ω'(x,y,p) = O1(x,y) * Q1(p) + O2(x,y)*Q2(p) 


Holding O1 as positively defined, when the ratio of r=O2/O1 increases from -1 to 1, ω' transitions from a bottom-heavy profile to a top-heavy profile (Figure 1b). 
To assess how well ω' approximates ω, the fractional variance (R2 between the reconstructed Omega and original Omega profiles) is calculated over each grid point. The fractional variance is defined as the square of the pearson correlation between ω' and ω. As shown in Figure 2,  ω' explains more than 80% of the vertical variability over most tropical/subtropical oceanic grid points.

The top-heaviness ratio (r) is presented in Figure 3. Since we are interested in the deep convective regions, grid points with O1 less than zero are not shown. The Western Pacific is dominated by more top-heavy vertical profiles while the Eastern Pacific and Atlantic are characterized by more bottom-heavy profiles, exhibiting a great contrast.   

.. figure:: Q1&Q2_R.png
   :align: center
   :width: 75 %
   
   Figure 1. Left: Q1 and Q2; Right: Vertical motion profiles constructed from the varying top-heaviness ratio (r; r=-1: dark blue, r=1: dark red).
   

.. figure:: R2_Between_Recon_Omega&Original.png
   :align: center
   :width: 75 %

   Figure 2. R2 between the reconstructed Omega and original Omega profiles.
   

.. figure:: Top_Heaviness_Ratio.png
   :align: center
   :width: 75 %
   
   Figure 3. Top-Heaviness Ratio in of the long-term mean omega in July (2000-2019). The ratio is only calculated over grid points where O1 is no less than 0.01 which is very close to zero.
