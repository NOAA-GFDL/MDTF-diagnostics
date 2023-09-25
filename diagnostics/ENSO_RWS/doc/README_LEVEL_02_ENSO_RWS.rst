Information about Level 2 – Ambient flow diagnostics
====================================================

At this level, the code estimates basic state or climatological flow properties that 
determine generation and propagation of stationary Rossby waves. Specifically, restoring effect 
for Rossby waves ( *β*\ :sub:`\*`)  that is dependent on meridional gradient in absolute 
vorticity (*β*) and meridional curvature of the climatological zonal flow or gradients 
in relative vorticity :math:`\frac{\partial^{2}{{U}}}{\partial{y}^{2}}`, and resultant
stationary wave number :math:`K_{s}` are diagnosed.

Required input data are calculated in **Level 1.**

Users need to complete **Level 1** diagnostics first before running **Level 2.**
The following terms are calculated at an appropriate upper tropospheric level:

*β*\ :sub:`\*` = (*β* - :math:`\frac{\partial^{2}{{U}}}{\partial{y}^{2}}`)    (1)

:math:`K_{s}` = (*β*\ :sub:`\*`/ 𝑈 ) :sup:`\1/2`    (2) 


where *β* is  :math:`\frac{\partial{{f}}}{\partial{y}}` latitudinal variations in planetary
vorticity (𝑓), 𝑈  is the basic-state zonal wind velocity, and :math:`\frac{\partial^{2}{{U}}}{\partial{y}^{2}}`  is the curvature of the ambient zonal flow. Stationary Rossby waves are possible
if the flow is westerly (𝑈  positive) and *β* is positive.


Final output directories:
=========================

The seasonal climatologies are under directories:
~/wkdir/MDTF_$model_$first_year_$last_year/ENSO_RWS/model/netCDF/
Graphical output files reside in: ~/wkdir/MDTF_$model_$first_year_$last_year/ENSO_RWS/model
(e.g. $model = CESM1, $first_year = 1950, $last_year = 2005)
