**Information about Level 3 – MSE variance diagnostics**

At this level the code calculates terms of MSE variance/covariance
diagnostics.

To select this level set the parameter ENSO_MSE_VAR = 1 in
~/diagnostics/ENSO_MSE/settings.jsonc file.

The necessary input data are already estimated in **Level 2** and
**Level 1.**

**Level 3** diagnostics are estimated as:

:math:`s_{x} = \frac{\left\| x \cdot \left\langle h \right\rangle \right\|}{\left\| \left\langle h \right\rangle^{2} \right\|}`

Where *x* can be any one of the following MSE budget term:

moist advection:
:math:`x = - \left\langle V \cdot \nabla q \right\rangle`

MSE vertical advection:
:math:`x = - \left\langle \omega\frac{\partial h}{\partial p} \right\rangle`

net shortwave flux: :math:`x = \left\langle \text{SW} \right\rangle`

net longwave flux: :math:`x = \left\langle \text{LW} \right\rangle`

sensible heat flux: :math:`x = \left\langle \text{SHF} \right\rangle`

latent heat flux: :math:`x = \left\langle \text{LHF} \right\rangle`

The column MSE is, :math:`h = C_{P}T + \text{gz} + Lq` where *C\ p*\ is
specific heat at constant pressure, *T* is temperature, *g* is the
gravitational acceleration\ *, z* is geopotential height, *L* is latent
heat of vaporization, and *q* is specific humidity.
:math:`\left\| \right\|` represents area averages.

There are two default and one custom selected areas for averaging the
MSE variances:

a) Equatorial Central Pacific (180\ :sup:`o`–200\ :sup:`o`\ E;
10\ :sup:`o`\ S – 5\ :sup:`o`\ N)

b) Equatorial Eastern Pacific (220\ :sup:`o`–280\ :sup:`o`\ E;
5\ :sup:`o`\ S – 5\ :sup:`o`\ N)

c) user prescribed area defined by environmental variables **slon1,
slon2 , slat1** and **slat2** (longitudes, latitudes) in
~/diagnostics/ENSO_MSE/settings.jsonc file.

*Final output directories:*

The output data are saved in

~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/

$diag_name/model/netCDF .

Graphical output is in :
~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/model

(e.g., $model = CESM1, $fist_year= 1950, $last_year = 2005, $diag_name =
MSE_VAR)

The calculated co-variances are scaled by MSE variance and plotted as a
bar chart.
