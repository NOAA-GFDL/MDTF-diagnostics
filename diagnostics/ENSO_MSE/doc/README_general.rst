**Instructions for ENSO Moist Static Energy Process-oriented diagnostics
(POD)**

This POD package consists of four levels. With a focus on identifying
leading processes that determine ENSO-related precipitation anomalies,
main module of the POD estimates vertically integrated moist static
energy (MSE) budget and its variance diagnostics. In that pursuit, POD
is applied to monthly data (climate model or reanalysis products), and
budget terms are estimated for “composite” El Niño or La Nina events
(either for monthly or seasonal anomalies). To estimate MSE budget,
along with surface and radiation fluxes, 3-dimensional atmospheric
variables are required. Hence, ERA-Interim is “considered” as
“observations” here, and diagnostics obtained from ERA-Interim are used
for model validation. In this general README document, brief
descriptions of the four levels are provided but detailed information
(e.g., input variables) is provided at each level.

**Level 1 – Basic ENSO diagnostics**

Composites, regression and correlation etc., Reference index (e.g.,
Nino3.4 SST)

-  Monthly and seasonal averages

-  2 Year life cycle of ENSO: Year (0) and Year(1)

..

   Year (0) = developing phase and Year (1) = decaying phase

To select Level 1 diagnostics, set: ENSO_COMPOSITE = 1 in the
~/diagnostics/ENSO_MSE/settings.jsonc file.

*Note: Level 1 diagnostics is required to perform Level 2 diagnostics*

**Level 2 – MSE (Moist Static Energy) budget analysis (for composite
ENSO)**

Vertically integrated MSE and its budget are estimated here:

MSE is defined as: :math:`h = C_{P}T + \text{gz} + \text{Lq}`

where *C\ p*\ is specific heat at constant pressure, *T* is temperature,
*g* is the gravitational acceleration\ *, z* is geopotential height, *L*
is latent heat of vaporization, and *q* is specific humidity.

The vertically integrated MSE tendency budget is approximately given by

.. math:: \left\langle \frac{\partial h}{\partial t} \right\rangle = - \left\langle V \cdot \nabla h \right\rangle - \left\langle \omega\frac{\partial h}{\partial p} \right\rangle + \text{LH} + \text{SH} + \left\langle \text{LW} \right\rangle + \left\langle \text{SW} \right\rangle + R

where *SH* is the sensible heat flux, *LH* is latent heat flux,
:math:`\left\langle \text{LW} \right\rangle` and
:math:`\left\langle \text{SW} \right\rangle` are net column longwave and
shortwave heating rates.
:math:`- \left\langle V \cdot \nabla h \right\rangle` and
:math:`- \left\langle \omega\frac{\partial h}{\partial p} \right\rangle`
are horizontal and vertical MSE advection terms respectively. *R* is the
residual term. At seasonal time scales considered here, the tendency
term :math:`\left\langle \frac{\partial h}{\partial t} \right\rangle`\ ≈
0.

To select Level 2 diagnostics, set ENSO_MSE = 1 in the
~/diagnostics/ENSO_MSE/settings.jsonc file.

*Note: Level 2 requires pre-calculated results (e.g., composites) from
Level 1.*

**Level 3 – MSE variance diagnostics (for composite ENSO)**

Vertically integrated MSE variance is estimated here. Outputs are
co-variances scaled by MSE variance and given by:

   :math:`s_{x} = \frac{\left\| x \cdot \left\langle h \right\rangle \right\|}{\left\| \left\langle h \right\rangle^{2} \right\|}`

where x is a given component of MSE budget, and *h* is MSE.

To select Level 3 diagnostics, set ENSO_MSE_VAR = 1 in the
~/diagnostics/ENSO_MSE/settings.jsonc file.

*Level 3 requires pre-calculated results from Level 1 and Level 2.*

**Level 4 – MSE scatter plots (Metrics).**

At this level, results from Level 2 (CMIP-era models) are condensed into
scatter plots. Specifically, estimates of each MSE budget term (e.g.,
:math:`- \left\langle \omega\frac{\partial h}{\partial p} \right\rangle`)
is plotted against precipitation. In these plots, also shown are
inter-model correlations and best-fit regression line.

To select Level 4 diagnostics, set ENSO_SCATTER = 1 in the
~/diagnostics/ENSO_MSE/settings.jsonc file.

*Level 4 requires pre-calculated results from Level 1 and Level 2.*

**Contact Information:**

PI : Dr. H. Annamalai,

International Pacific Research Center,

University of Hawaii at Manoa

E-mail: hanna@hawaii.edu

Programming: Jan Hafner

Email: jhafner@hawaii.edu

**References:**

Annamalai, H., 2020: ENSO precipitation anomalies along the equatorial
Pacific: Moist static energy framework diagnostics. *J. Climate*,
**33**, 9103-9127, doi:10.1175/JCLI-D-19.0374.1

Annamalai, H., J. Hafner, A. Kumar and H. Wang, 2014: A framework for
dynamical seasonal prediction of precipitation over Pacific islands. *J.
Climate*, **27**, 3272-3297, https://doi.org/10.1175/JCLI-D-13-00379.1
