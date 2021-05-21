Flow-Dependent Model Diagnostic Documentation
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

.. and pre-digested observational data under mdtf/inputdata/obs_data/convective_transition_diag

