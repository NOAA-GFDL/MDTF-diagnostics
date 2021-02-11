Instructions for ENSO Moist Static Energy Process­-oriented diagnostics (POD)
============================================================================

This POD package consists of four levels. With a focus on identifying leading processes that
determine ENSO­-related precipitation anomalies, main module of the POD estimates
vertically integrated moist static energy (MSE) budget and its variance diagnostics. In that
pursuit, POD is applied to monthly data (climate model or reanalysis products), and budget
terms are estimated for “composite” El Niño or La Nina events (either for monthly or seasonal
anomalies). To estimate MSE budget, along with surface and radiation fluxes, 3-­dimensional
atmospheric variables are required. Hence, ERA-­Interim is “considered” as “observations”
here, and diagnostics obtained from ERA­-Interim are used for model validation. In this
general README document, brief descriptions of the four levels of the POD are provided but
detailed information (e.g., input variables) is provided at each level.

See also the :doc:`diagnostic overview documentation <./ENSO_MSE>`.

Level 1 – Basic ENSO diagnostics
--------------------------------

Composites, regression and correlation etc: Reference index (e.g., Nino3.4 SST)

- Monthly and seasonal averages
- 2 Year life cycle of ENSO: Year(0) and Year(1)
   Year (0) = developing phase and Year (1) = decaying phase

To select Level 1 diagnostics, set: COMP = 1 in the mdtf.py file.

*Note: Level 1 diagnostics is required to perform Level 2 diagnostics.*

Level 2 – MSE (Moist Static Energy) budget analysis (for composite ENSO)
------------------------------------------------------------------------

Vertically integrated MSE and its budget are estimated here:

.. math::

   \text{MSE is defined as: } h = C_P T + gz + Lq

where :math:`C_P` is specific heat at constant pressure, :math:`T` is temperature, :math:`g` is the gravitational
acceleration, :math:`z` is geopotential height, :math:`L` is latent heat of vaporization, and :math:`q` is specific
humidity.

The vertically integrated MSE tendency budget is approximately given by

.. math::

   \left\langle \frac{\partial h}{\partial t} \right\rangle = - \langle V \cdot \nabla h \rangle - \left\langle \omega \frac{\partial h}{\partial p} \right\rangle + LH +SH + \langle LW \rangle + \langle SW \rangle + R

where :math:`SH` is the sensible heat flux, :math:`LH` is latent heat flux, :math:`\langle LW \rangle` and :math:`\langle SW \rangle`
are net column longwave and shortwave heating rates. :math:`- \langle V \cdot \nabla h \rangle` and :math:`- \left\langle \omega \frac{\partial h}{\partial p} \right\rangle`
are horizontal and vertical MSE advection terms respectively. :math:`R` is the residual term.

At seasonal time scales considered here, the tendency term :math:`\left\langle \frac{\partial h}{\partial t} \right\rangle \approx 0`.

To select Level 2 diagnostics, set MSE = 1 in the mdtf.py file.

*Note: Level 2 requires pre­-calculated results (e.g., composites) from Level 1.*

Level 3 – MSE variance diagnostics (for composite ENSO)
-------------------------------------------------------

Vertically integrated MSE variance is estimated here. Outputs are co­variances scaled by
MSE variance and given by:

.. math::

   s_x = \frac{|| x \cdot \langle h \rangle ||}{|| \langle h \rangle^2 ||}

where :math:`x` is a given component of MSE budget, and :math:`h` is MSE.

To select Level 3 diagnostics, set MSE_VAR = 1 in the mdtf.py file.

*Level 3 requires pre-­calculated results from Level 1 and Level 2.* 

Level 4 – MSE scatter plots (Metrics).
--------------------------------------

At this level, results from Level 2 (CMIP­-era models) are condensed into scatter plots.
Specifically, estimates of each MSE budget term (e.g., :math:`- \left\langle \omega \frac{\partial h}{\partial p} \right\rangle`)
is plotted against precipitation. In these plots, also shown are inter-­model correlations and best­-fit regression line.

To select Level 4 diagnostics, set SCATTER = 1 in the mdtf.py file.

*Level 4 requires pre­-calculated results from Level 1 and Level 2.*

Contact Information:
--------------------

PI: Dr. H. Annamalai,
International Pacific Research Center,
University of Hawaii at Manoa.
E­mail: hanna@hawaii.edu

Programming: Jan Hafner, jhafner@hawaii.edu

References
----------

   .. _1: 
   
1. Annamalai, H., J. Hafner, A. Kumar, and H. Wang, 2014: A Framework for Dynamical Seasonal Prediction of Precipitation over the Pacific Islands. *J. Climate*, **27** (9), 3272-3297,  https://doi.org/10.1175/JCLI-D-13-00379.1.

   .. _2: 
   
2. Annamalai, H., 2019: ENSO precipitation anomalies along the equatorial Pacific: Moist static energy framework diagnostics. Submitted to special collection on Process-based diagnostics (J. Climate).


.. _enso_mse_sec_level_1:

Information about Level 1 – Basic ENSO diagnostics
--------------------------------------------------

At this level, POD calculates simple seasonal averages, composites, regression and
correlations.

Based on a reference ENSO index (e.g., area­-averaged SST anomalies over Nino3.4 region),
seasonal composites of variables relevant to MSE budget are constructed for the entire 2­-year
life­cycle of ENSO. Here, Y (0) refers to the developing, and Y (1) the decaying phase of
ENSO.

To execute this level, data need to be preprocessed to calculate monthly climatologies and
anomalies for all the required input variables listed below. It is executed only once at the
beginning of a new diagnostic run (e.g., when a new model dataset is considered). The
preprocessing is switched on by setting PREPROCESS = 1 in mdtf.py file. Then to turn off
preprocessing, set PREPROCESS = 0 in mdtf.py file.

To perform composites set COMP = 1 in the mdtf.py file. Note CCSM4 solutions are
considered as an example here.

The code files related to this Level 1 are stored in the ``~/var_code/ENSO_MSE/COMPOSITE``
directory. All input data should be under ``~/{case_name}`` (for instance ``~/CCSM4/mon``), the
intermediate output data are in: ``~/wkdir/MDTF_{case_name}/COMPOSITE/model/netCDF``,
while graphics is under ``~/wkdir/MDTF_{case_name}/COMPOSITE/model``.

The required input variables are:

====================== =====================================
Z(x,y,z,t)             geopotential height,
U(x,y,z,t), V(x,y,z,t) u and v wind components
T(x,y,z,t)             temperature
Q(x,y,z,t)             specific humidity
OMG(x,y,z,t)           vertical velocity
PR(x,y,t)              precipitation
SST(x,y,t)             surface temperature
SHF(x,y,t)             sensible heat flux
LHF(x,y,t)             latent heat flux
RSDT(x,y,t)            top of the atmosphere shortwave down
RSUT(x,y,t)            top of the atmosphere shortwave up
RLUT(x,y,t)            top of the atmosphere longwave up
RSDS (x,y,t)           surface shortwave down
RSUS(x,y,t)            surface shortwave up
RLUS(x,y,t)            surface longwave up
RLDS(x,y,t)            surface longwave down
====================== =====================================

The individual options at the Level 1 are set in
``~/var_code/ENSO_MSE/COMPOSITE/parameters.txt file``.
The selectable switches in the ``~/var_code/ENSO_MSE/COMPOSITE/parameters.txt`` are as
follows:

*Instructions for composite calculation*

========================== ======================================================================================================================================
**lon1, lon2, lat1, lat2** lat/lon coordinates for ENSO reference index (e.g., Nino3.4). Reference index is used in selection of ENSO years.
**sigma**                  Threshold for reference index. For example, sigma = 1 selects years with SST anomaly > 1.0 std. of the reference index.
**imindx1, imindx2**       Calendar months used in the construction of ENSO reference index (e.g. Nino3.4 boreal winter (DJF) index: imindx1 = 12, imindx2 = 2).
**composite­**              El Niño/La Nina composites: 0 : off [no composite output], 1 : on [composite output].
**composite24**            to construct for 2­year life cycle of ENSO monthly composites: 0 : off [no 2­year life cycle output], 1 : on [ 2­year life cycle output].
**im1, im2**               Calendar months for user preferred seasonal composites (e.g., DJF, JJA).DJF: im1 = 12, im2 = 2, JJA: im1 = 6 , im2 = 8.
========================== ======================================================================================================================================

*Instructions for plotting*

============== ===========================================================================================================================================================================
**season** ­     “Figure label”. For example, plotting composite for boreal winter season set season = DJF.
**seasonindx** designator used in plotting routines. If a user selects boreal winter reference index (e.g. imindx1 = 12 and imindx2 = 2), then seasonindx = DJF (footnote in the figures).
============== ===========================================================================================================================================================================

*Instructions for regression/correlation*

=============== ==================================================================================================================
**regression**  switch to calculate and plot regressions: 0 : off [no regression output], 1 : on [ regression output].
                Based on Nino3.4 reference index POD calculates and plots the simultaneous regression for the following variables:
                   - precipitation
                   - sensible heat flux
                   - latent heat flux
                   - net shortwave radiative flux
                   - net longwave radiative flux

**correlation** ­switch to calculate and plot correlations: 0 : off [no correlation output], 1 : on [ correlation output].
                Based on Nino3.4 reference index POD calculates and plots the simultaneous regression for the following variables:
                   - precipitation
                   - sensible heat flux
                   - latent heat flux
                   - net shortwave radiative flux
                   - net longwave radiative flux

=============== ==================================================================================================================

Final output directories:
^^^^^^^^^^^^^^^^^^^^^^^^^

Based on setup in the parameters.txt the output files and corresponding graphics are
generated. The output files are under ``~/wkdir/MDTF_{case_name}/{diag_name}/model/netCDF``. diag_name = COMPOSITE.

The composites for El Niño/La Nina are under ``~/wkdir/MDTF_{case_name}/{diag_name}/model/netCDF/ELNINO``
or ``~/wkdir/MDTF_{case_name}/{diag_name}/model/netCDF/LANINA``.

Similarly 2­-year life cycle ENSO composite results are under:
``~/wkdir/MDTF_{case_name}/{diag_name}/model/netCDF/24MONTH_ELNINO``
or ``~/wkdir/MDTF_{case_name}/{diag_name}/model/netCDF/24MONTH_LANINA``.

Graphical output is now set to be all global and for all surface variables. The actual files are
in ``~/wkdir/MDTF_{case_name}/{diag_name}/model``.


.. _enso_mse_sec_level_2:

Information about Level 2 – MSE budget analysis
-----------------------------------------------

At this level, the code estimates vertically integrated MSE budget terms.

Required input data are calculated in **Level 1**. To execute this level, set the parameter
MSE = 1 in mdtf.py python file. Users need to complete **Level 1** diagnostics first before
running **Level 2**.

The following terms are calculated as vertical integrals:

======================= =========================================================================
MSE:                    :math:`h = C_P T + gz + Lq`
MSE vertical advection: :math:`- \left\langle \omega \frac{\partial h}{\partial p} \right\rangle`
moisture divergence:    :math:`\langle q \nabla \cdot V \rangle`
moisture advection:     :math:`- \langle V \cdot \nabla q \rangle`
temperature advection:  :math:`- \langle V \cdot \nabla T \rangle`
======================= =========================================================================

*Note that vertically integrated moisture divergence is also estimated here.*

Note also that surface and radiative fluxes, are already estimated in Level 1. All MSE terms
are expressed in W/ m\ |^-2|.

Final output directories:
^^^^^^^^^^^^^^^^^^^^^^^^^

The El Niño/La Nina composites are under directories: ``~/wkdir/MDTF_{case_name}/MSE/model/netCDF/ELNINO``
and ``~/wkdir/MDTF_{case_name}/MSE/model/netCDF/LANINA`` respectively.

Graphical output files reside in : ``~/wkdir/MDTF_{case_name}/MSE/model`` directory.
(e.g. ``{case_name} = CCSM4``).


.. _enso_mse_sec_level_3:

Information about Level 3 – MSE variance diagnostics
----------------------------------------------------

At this level the code calculates terms of MSE variance/covariance diagnostics.

To select this level set the parameter MSE_VAR = 1 in ~/mdtf.py python file.

The necessary input data are already estimated in **Level 2** and **Level 1**.

**Level 3** diagnostics are estimated as:

.. math::

   s_x = \frac{|| x \cdot \langle h \rangle ||}{|| \langle h \rangle^2 ||}

Where x can be any one of the following MSE budget terms:

======================= ===========================================================================
moist advection:        :math:`x=- \langle V \cdot \nabla q \rangle`
MSE vertical advection: :math:`x=- \left\langle \omega \frac{\partial h}{\partial p} \right\rangle`
net shortwave flux:     :math:`x= \langle SW \rangle`
net longwave flux:      :math:`x= \langle LW \rangle`
sensible heat flux:     :math:`x= \langle SHF \rangle`
latent heat flux:       :math:`x= \langle LHF \rangle`
======================= ===========================================================================


The column MSE is, :math:`h = C_P T + gz + Lq` where :math:`C_P` is specific heat at constant pressure, :math:`T` is temperature, 
:math:`g` is the gravitational acceleration, :math:`z` is geopotential height, :math:`L` is latent heat of
vaporization, and :math:`q` is specific humidity. :math:`|| \cdot ||` represents area averages.

There are two default and one custom selected areas for averaging the MSE variances:

   a) Equatorial Central Pacific 180°–200°E 10°S – 5°N
   b) Equatorial Eastern Pacific 220°–280°E 5°S – 5°N
   c) user prescribed area defined by environmental variables **slon1, slon2, slat1** and **slat2** (longitudes, latitudes) in ~/mdtf.py file in the MSE_VAR section.

Final output directories:
^^^^^^^^^^^^^^^^^^^^^^^^^

The output data are saved in ``~/wkdir/MDTF_{case_name}/MSE_VAR/model/netCDF``.
Graphical output is in ``~/wkdir/MDTF_{case_name}/{MSE_VAR}/model`` (e.g. ``case_name = CCSM4``).

The calculated co­variances are scaled by MSE variance and plotted as a bar chart.


.. _enso_mse_sec_level_4:

Information about Level 4 – MSE scatter plots (Metric)
------------------------------------------------------

At this level the code produces scatter plots between MSE budget terms and precipitation.

The necessary input data are calculated in **Level 1** and **Level 2**. To run this level diagnostic
a user needs to process the data at **Level 1** and **Level 2** first and for all models considered.

To select this level set the parameter SCATTER = 1 in mdtf.py python file.

At this level the following scatter plots are generated:

   a) precipitation (x­axis) versus horizontal moisture advection (y­axis)
   b) precipitation (x­axis) versus net radiative flux divergence (y­axis)
   c) precipitation (x­axis) versus vertical advection of MSE (y­axis)
   d) precipitation (x­axis) versus total heat flux (latent + sensible) THF (y­axis)

All are seasonal El Niño composite anomalies averaged over:

   a) Equatorial Central Pacific 180°–200°E 10°S – 5°N
   b) Equatorial Eastern Pacific 220°–280°E 5°S – 5°N

All variables are expressed in W/ m\ |^-2|.
The list of models and observation data included in the scatter plots is given in:
``~/var_code/ENSO_MSE/SCATTER/list­-models­-historical­-obs``.

Final output directories:
^^^^^^^^^^^^^^^^^^^^^^^^^

Graphical output is in ``~/wkdir/MDTF_SCATTER``.


.. |^2| replace:: \ :sup:`2`\ 
.. |^3| replace:: \ :sup:`3`\ 
.. |^-1| replace:: \ :sup:`-1`\ 
.. |^-2| replace:: \ :sup:`-2`\ 
.. |^-3| replace:: \ :sup:`-3`\ 
