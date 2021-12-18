Information about Level 4 – Scatter plots for multi-model assessment (Metric)
=============================================================================
At this level the code produces scatter plots between physically-linked variables that 
underscore models’ fidelity in representing “chain of processes” that deem responsible 
for ENSO-induced teleconnection.  The necessary input data are calculated in **Levels 1-3.** 
To run this level diagnostic a user needs to process the data at **Levels 1-3** first. 
The AMIP5/6 model results are already provided as “predigested data”. The results of 
the current model diagnosed will be incorporated and scatter plots are made along with the
“predigested data”. Users can infer the current/new model’s ability in representing 
processes compared to AMIP5/6 models.


At this level the following scatter plots are generated:

    • Equatorial Pacific precipitation (x-axis) *versus* subtropical upper-level divergence (yaxis)
    • subtropical upper-level divergence (x-axis) *versus* RWS terms (y-axis)
    • east Asian monsoon precipitation (x-axis) *versus* RWS terms (y-axis)
    • east Asian monsoon precipitation (x-axis) *versus* total RWS along jet (y-axis)
    • subtropical upper-level divergence (x-axis) *versus* PNA index (y-axis)
    • total RWS subtropics (x-axis) *versus* PNA index (y-axis)
    • total RWS subtropics east of dateline (x-axis) *versus* PNA index (y-axis)
    • Beta* longitudinal shift (x-axis) *versus* standardized PNA index (y-axis)
    • Beta* longitudinal shift (x-axis) *versus* standardized Aleutian low index (y-axis)
    • Equatorial Pacific precipitation (x-axis) *versus* standardized PNA index (y-axis)

In each of the scatter plots, number 5 corresponds to AMIP5 and, 6 corresponds to AMIP6 models,
and the color of the numbers correspond to the model’s name. The list of models + observation 
data included in the scatter plots are given at: 
~/diagnostics/inputdata/obs_data/ENSO_RWS/SCATTER/

Final output directories:
==========================
Graphical output is in ~/wkdir/MDTF_$model_$first_year_$last_year/ENSO_RWS/model
(e.g. $model = CESM1, $first_year = 1950, $last_year = 2005).


