**Information about Level 4 – MSE scatter plots (Metric)**

At this level the code produces scatter plots between MSE budget terms
and precipitation.

The necessary input data are calculated in **Level 1** and **Level 2.**
To run this level diagnostic a user needs to process the data at **Level
1** and **Level 2** first. The CMIP5 model results are already provided
as “predigested data”. The results of the current model diagnosed will
be incorporated and scatter plots are made along with the “predigested
data”. Users can infer the current/new model’s ability in representing
the MSE processes compared to CMIP5 models.

To select this level set the parameter ENSO_SCATTER = 1 in
~/diagnostics/ENSO_MSE/settings.jsonc file.

At this level the following scatter plots are generated:

a) precipitation (x-axis) *versus* horizontal moisture advection (y-axis)

b) precipitation (x-axis) *versus* net radiative flux divergence (y-axis)

c) precipitation (x-axis) *versus* vertical advection of MSE (y-axis)

d) precipitation (x-axis) *versus* total heat flux (latent + sensible) THF (y-axis)

All are seasonal El Niño composite anomalies averaged over:

a) Equatorial Central Pacific (180\ :sup:`o`–200\ :sup:`o`\ E;
10\ :sup:`o`\ S – 5\ :sup:`o`\ N)

b) Equatorial Eastern Pacific (220\ :sup:`o`–280\ :sup:`o`\ E;
5\ :sup:`o`\ S – 5\ :sup:`o`\ N)

All variables are expressed in W/m\ :sup:`-2`.

The list of models + observation data included in the scatter plots is
given in:

~/diagnostics/inputdata/obs_data/ENSO_MSE/SCATTER/list-models-historical-obs.

*Final output directories:*

Graphical output is in
~/diagnostics/wkdir/MDTF_$model_$first_year_$last_year/ENSO_MSE/model

(e.g. $model = CESM1, $first_year = 1950, $last_year = 2005).
