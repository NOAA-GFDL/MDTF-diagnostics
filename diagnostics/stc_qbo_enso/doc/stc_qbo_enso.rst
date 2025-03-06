.. This is a comment in RestructuredText format (two periods and a space).

.. Note that all "statements" and "paragraphs" need to be separated by a blank
   line. This means the source code can be hard-wrapped to 80 columns for ease
   of reading. Multi-line comments or commands like this need to be indented by
   exactly three spaces.

.. Underline with '='s to set top-level heading:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html#section-structure

Stratosphere-Troposphere Coupling: QBO and ENSO stratospheric teleconnections
=============================================================================

Last update: 2023-10-03

This script and its helper scripts (“stc_qbo_enso_plottingcodeqbo.py” and 
“stc_qbo_enso_plottingcodeenso.py”) do calculations to assess the representation
of stratospheric telconnections associated with the Quasi-Biennial Oscillation
(QBO) and the El Nino Southern Oscillation (ENSO). This POD uses monthly 4D
(time x plev x lat x lon) zonal wind, 4D meridional wind, 4D temperature, 3D
(time x lat x lon) sea level pressure, and 3D sea surface temperature data.
Coupling between the QBO and the boreal polar stratosphere takes place during 
boreal fall and winter whereas coupling between the QBO and the austral polar 
stratosphere takes place mainly during austral spring and summer. By default, 
the POD defines the QBO for NH (SH) analyses using the Oct-Nov (Jul-Aug) 5S-5N 
30 hPa zonal winds. The QBO is thought to influence the polar stratospheres, 
the so-called “polar route,” by modulating the lower stratospheric (~100-50 hPa) 
and middle stratospheric (~20-5 hPa) mid-latitude circulation. The aforementioned 
lower stratospheric teleconnection is also associated with a change in the strength 
and position of the tropospheric jet; the so-called “subtropical route.” In addition, 
evidence continues to show that the QBO directly influences the underlying tropical 
tropospheric circulation, referred to as the “tropical route.” These three 
teleconnections allow the QBO to elicit surface impacts globally. Said teleconnections 
are visualized herein by using a metric of planetary wave propagation (eddy heat flux), 
circulation response (zonal wind), and surface impact (sea level pressure). 
Additionally, metrics of model QBOs (e.g., amplitude, height, width) are produced.
ENSO’s coupling with the polar stratospheres takes place as the amplitude of ENSO 
maximizes during boreal fall and winter. By default, the POD defines ENSO for NH 
(SH) analyses using the Nov-Mar (Sep-Jan) Nino3.4 SSTs. Though ENSO’s teleconnections 
are global, it interacts with the stratosphere by stimulating tropical-extratropical 
Rossby waves that constructively interfere with the climatological extratropical 
stationary wave mainly over the Pacific, promoting enhanced upward planetary wave 
propagation into the  stratosphere. Similar to the QBO code, ENSO’s teleconnections 
are visualized using the eddy heat flux, the zonal wind, and the sea level pressure.

This POD makes six kinds of figures and one text file from provided model data:

- Zonal-mean zonal wind anomalies (deviations from seasonal cycle) composited 
  based on El Nino and La Nina years are shown in red/blue shading. Nina minus
  Nino differences are shown in shading as well and climatological winds are 
  overlaid on all aforementioned plots in black contours
- Zonal-mean eddy heat flux anomalies composited based on El Nino and La Nina
  years are shown in red/blue shading. Nina minus Nino differences are shown 
  in shading as well and climatological heat flux is overlaid on all aforementioned
  plots in black contours
- Sea level pressure anomalies composited based on El Nino and La Nina
  years are shown in red/blue shading. Nina minus Nino differences are shown 
  in shading as well and climatological sea level pressure is overlaid on all aforementioned
  plots in black contours
- A text file of QBO metrics (min/mean/max QBO periodicity, easterly/westerly/total 
  amplitude, lowest altitude tropical stratospheric isobar that the QBO reaches,
  the height or vertical extent of the QBO, and its latitudinal width) is produced.
- Should the above QBO metrics code detect a QBO in the model data, similar plots as
  the aforementioned three ENSO plots, but composited based on easterly
  and westerly QBO years, are made

These plots are made for both hemispheres, with a focus on winter and spring, the seasons
when upward propagating planetary waves couple the troposphere and stratosphere. 
The metrics are designed to reveal the extratropical circulation response to two forms 
of tropical internal variability, which are generally difficult to represent spontaneously 
in climate models (QBO+ENSO). Though ENSO's representation in climate models as well as the 
representation of its teleconnections has significantly improved over multiple generations 
of CMIP experiments (Bellenger et al. 2014; Planton et al. 2021), it is less clear how 
ENSO's coupling with the polar stratosphere is represented by models. The sea level 
pressure ENSO responses reveal the precursor tropospheric forcing patterns 
(e.g., Aleutian Low response) that should stimulate or reduce upward planetary wave 
propagation into the stratosphere. The zonal wind and eddy heat flux plots reveal if the 
reinforced or suppressed upward planetary wave propagation due to ENSO is actually "felt"
in the stratosphere and the sea level pressure plots can again be referenced for evidence 
of a downward propagating winter/spring annular mode response to ENSO modulating the polar vortex.

Similar plots to the ones made based on El Nino and La Nina years are made for easterly
and westerly QBO years if and when a QBO is detected in the model data; e.g., models with
too-coarse vertical resolution may not simulate a QBO (Zhao et al. 2018). It should be
interesting to compare the QBO metrics with the representation of QBO teleconnections in 
models. Models struggle to represent several QBO attributes (Richter et al. 2020) and 
since the structure of the QBO (e.g., its amplitude or latitudinal width) is intimately 
tied to the representation of QBO teleconnections (Garfinkel and Hartmann 2011; Hansen
et al. 2013), models generally have a difficult time representing the extratropical 
impacts of the QBO (Rao et al. 2020). 


Version & Contact info
----------------------

- Version/revision information: v1.0 (Oct 2023)
- Project PIs: Amy H. Butler (NOAA CSL) and Zachary D. Lawrence (CIRES/NOAA PSL)
- Developer/point of contact: Dillon Elsbury (dillon.elsbury@noaa.gov)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt).


Functionality
-------------

This POD is driven by the file ``stc_qbo_enso.py``, with two helper scripts called
``stc_qbo_enso_plottingcodeenso.py`` and ``stc_qbo_enso_plottingcodeqbo.py``.
The driver script reads in the model fields, identifies El Nino/La Nina years and
easterly/westerly QBO years, computes the eddy heat flux, retrieves the QBO metrics,
and then uses the two helper scripts to make the associated zonal wind, eddy heat 
flux, and sea level pressure plots.

The atmospheric observational data this POD uses is based on ERA5 reanalysis
(Hersbach, et al., 2020), and includes pre-computed monthly zonal-mean zonal winds, zonal-
mean eddy heat fluxes, and sea level pressure. The oceanic observational data that
this POD uses is from HadiSST (Rayner et al. 2003) and includes pre-computed monthly sea
surface temperature.


Required programming language and libraries
-------------------------------------------

This POD requires Python 3, with the following packages:

- numpy
- xarray
- xesmf
- os
- matplotlib
- cartopy
- scipy

Required model output variables
-------------------------------

The following monthly mean fields are required:

- Zonal Winds, ``ua`` as ``(time,lev,lat,lon)`` (units: m/s)
- Meridional Winds, ``va`` as ``(time,lev,lat,lon)`` (units: m/s)
- Temperature, ``ta`` as ``(time,lev,lat,lon)`` (units: K)
- Sea level pressure, ``psl`` as ``(time,lat,lon)`` (units: Pa)
- Sea surface temperature, ``tos`` as ``(time,lat,lon)`` (units: Kelvin)

References
----------

.. _ref-Bellenger:

	Bellenger, H., Guilyardi, E., Leloup, J., Lengaigne, M., & Vialard, J. (2014). 
	ENSO representation in climate models: From CMIP3 to CMIP5. Climate Dynamics, 42, 
	1999-2018, https://doi.org/10.1007/s00382-013-1783-z
	
.. _ref-Planton:

	Planton, Y. Y., Guilyardi, E., Wittenberg, A. T., Lee, J., Gleckler, P. J., Bayr, T., 
	... & Voldoire, A. (2021). Evaluating climate models with the CLIVAR 2020 ENSO metrics 
	package. Bulletin of the American Meteorological Society, 102(2), E193-E217,
	https://doi.org/10.1175/BAMS-D-19-0337.1
	
.. _ref-Zhao:

	Zhao, M., Golaz, J. C., Held, I. M., Guo, H., Balaji, V., Benson, R., ... & Xiang, B. 
	(2018). The GFDL global atmosphere and land model AM4. 0/LM4. 0: 1. Simulation 
	characteristics with prescribed SSTs. Journal of Advances in Modeling Earth Systems, 
	10(3), 691-734, https://doi.org/10.1002/2017MS001209

.. _ref-Hersbach:

    Hersbach, H. and coauthors, 2020: The ERA5 global reanalysis. Q J R Meteorol Soc.,
    146, 1999-2049, https://doi.org/10.1002/qj.3803
    
.. _ref-Richter:

	Richter, J. H., Anstey, J. A., Butchart, N., Kawatani, Y., Meehl, G. A., Osprey, S., 
	& Simpson, I. R. (2020). Progress in simulating the quasi‐biennial oscillation in 
	CMIP models. Journal of Geophysical Research: Atmospheres, 125(8), e2019JD032362,
	https://doi.org/10.1029/2019JD032362
	
.. _ref-Garfinkel:

	Garfinkel, C. I., & Hartmann, D. L. (2011). The influence of the quasi-biennial 
	oscillation on the troposphere in winter in a hierarchy of models. Part I: Simplified 
	dry GCMs. Journal of the Atmospheric Sciences, 68(6), 1273-1289,
	https://doi.org/10.1175/2011JAS3665.1

.. _ref-Hansen:
	Hansen, F., Matthes, K., & Gray, L. J. (2013). Sensitivity of stratospheric dynamics 
	and chemistry to QBO nudging width in the chemistry‒climate model WACCM. Journal of 
	Geophysical Research: Atmospheres, 118(18), 10-464,
	https://doi.org/10.1002/jgrd.50812
	
.. _ref-Rao:
	Rao, J., Garfinkel, C. I., & White, I. P. (2020). Impact of the quasi-biennial 
	oscillation on the northern winter stratospheric polar vortex in CMIP5/6 models. 
	Journal of Climate, 33(11), 4787-4813, https://doi.org/10.1175/JCLI-D-19-0663.1

More about this POD
--------------------------

**Statistical testing**

A student's 2-tailed t-test is used to assess how likely it is that the Nina minus
Nino anomalies and easterly QBO minus westerly QBO anomalies arise by chance for the zonal
wind, eddy heat flux, and sea level pressure plots. A p-value <= 0.05 is used as the 
threshold for "statistical significance," which is denoted on the aforementioned figures
in the third row using stippling.