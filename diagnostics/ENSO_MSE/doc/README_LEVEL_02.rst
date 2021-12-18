**Information about Level 2 – MSE budget analysis**

At this level, the code estimates vertically integrated MSE budget
terms.

Required input data are calculated in **Level 1.** To execute this
level, set the parameter

ENSO_MSE = 1 in ~/diagnostics/ENSO_MSE/settings.jsonc

file. Users need to complete **Level 1** diagnostics first before
running **Level 2**.

The following terms are calculated as vertical integrals:

MSE: :math:`h = C_{P}T + \text{gz} + \text{Lq}`

MSE vertical advection:
:math:`- \left\langle \omega\frac{\partial h}{\partial p} \right\rangle`

moisture divergence: :math:`\left\langle q\nabla \cdot V \right\rangle`

moisture advection:
:math:`- \left\langle V \cdot \nabla q \right\rangle`

temperature advection:
:math:`- \left\langle V \cdot \nabla T \right\rangle`

*Note that vertically integrated moisture divergence is also estimated
here*.

Note also that surface and radiative fluxes, are already estimated in
Level 1. All MSE terms are expressed in W/m\ :sup:`2`.

*Final output directories:*

The El Niño/La Nina composites are under directories:

~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/MSE/model/netCDF/ELNINO
(or LANINA)

Graphical output files reside in :
~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/model

(e.g. $model = CESM1, $first_year = 1950, $last_year = 2005)
