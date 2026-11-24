Wavenumber Frequency Spectra Diagnostic Module From NCAR
========================================================
Last update: 11/12/2026

Produces wavenumber-frequency spectra for OLR, precipitation, 200 hPa zonal wind and
850 hPa zonal wind.

Contact info
------------

- Current Developer: Dani Coleman (​bundy@ucar.edu​), NCAR
- Contributors: Dennis Shea, Andrew Gettleman, Jack Chen, Rich Neale (NCAR)

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This package is distributed under the LGPLv3 license (see LICENSE.txt).

Functionality
-------------

Python code calls NCL wkSpaceTime_driver.ncl code for each of the variables in turn.
Observation figures (see "Observational data" below) are in
``mdtf/inputdata/obs_data/Wheeler_Kiladis``.
Place your input data at: ``mdtf/inputdata/model/$model_name/day``
index.html can be found at: ``mdtf/MDTF_$ver/wkdir/MDTF_$model_name``

Required Programing Language and libraries
------------------------------------------

All these scripts required NCAR Command Language Version 6.3.0 or higher

Required input data to the module
---------------------------------

Daily data (CESM names in parentheses):

1. Outgoing longwave radiation, rlut (FLUT), W m\ :sup:`-2`
2. Precipitation rate, pr (PRECT), m s\ :sup:`-1` (other units are converted by the framework)
3. Zonal wind at 200 hPa, u200 (U200), m s\ :sup:`-1`
4. Zonal wind at 850 hPa, u850 (U850), m s\ :sup:`-1`

500 hPa omega is no longer used.

Missing values in the input data
--------------------------------

The space-time spectra need a complete daily record. Before the spectra are computed
(``getVarSlice.ncl``), missing values are filled in two steps:

1. Linear interpolation in time at each grid point (NCL ``linmsg_n``). A run of missing days
   is filled with a straight line between the valid days on either side; missing days at the
   start or end of the record take the nearest valid value. This fills days that are missing
   everywhere, such as the 30 documented missing days of the NOAA daily OLR Climate Data Record
   (1980-1989), which the zonal-average fill below cannot fill.
2. Any point still missing (a point missing at every time) is set to that day's zonal average
   (precipitation: zero), as before.

The log reports how many values each step filled, for example
``getVarSlice: rlut: filled 324000 of 324000 missing values by linear interpolation in time``.

Observational data
------------------

The observation panels in ``obs_data`` were made by running this POD on observations treated as a
model case, for 2001-2024 with IMERG precipitation. All observations are daily means on
one 1 x 1 deg grid (cell centres 89.5S-89.5N, 0.5-359.5E), the native grid of the NOAA daily OLR
Climate Data Record.

- **OLR**: NOAA Climate Data Record (CDR) of Daily Outgoing Longwave Radiation, version 2
  (v02r00), 1979-present (Lee 2025; https://doi.org/10.25921/9pt5-by77), produced at the
  University of Maryland ESSIC (http://olr.umd.edu). It is derived from HIRS radiances on the
  NOAA and MetOp polar orbiters, calibrated against broadband (ERBE/CERES) OLR, with
  geostationary data for the diurnal cycle. NOAA documents 30 days with no data, all between
  1980 and 1989 (1980-03-02, 03-03, 06-04; 1981-03-24 to 04-08; 1982-09-22, 23; 1983-08-03;
  1984-01-11, 12, 12-03; 1985-09-22, 23; 1986-03-12; 1989-02-19, 20). In the distributed file 4
  of them (1980-03-02/03, 1989-02-19/20) contain values; these were set to missing, so all 30
  days are missing in the obs file and are filled by the POD as described above.
- **Precipitation**:

  - 2001-2024 (the panels in ``obs_data``): NASA GPM IMERG Final Run V07B daily (Huffman et al.
    2023; https://doi.org/10.5067/GPM/IMERGDF/DAY/07), 0.1 deg, averaged (area-weighted) onto the 1
    deg grid.
  - 1998-2019 (alternative figure set): TRMM Multi-satellite Precipitation Analysis 3B42 V7 daily
    (Huffman et al. 2007; https://doi.org/10.5067/TRMM/TMPA/DAY/7), 0.25 deg, 50S-50N, averaged onto
    the 1 deg grid. Each TRMM day runs from 01:30 UTC to 01:30 UTC the next day; the record ends
    2019-12-30.
  - 1979-1999 (alternative figure set, before the satellite records): ERA5 mean total precipitation
    rate.

- **Winds**: ERA5 reanalysis (Hersbach et al. 2020), hourly 0.25 deg pressure-level analyses,
  averaged over the 24 hours of each UTC day and regridded conservatively to 1 deg. ERA5.1
  (Simmons et al. 2020) is used for 2000-2006, as ECMWF recommends.

The file names in ``obs_data`` give the source of each panel (CDR, IMERG or ERA5):
``Fig<n>.<var>.<source>.png``, e.g. ``Fig3.Sym.rlut.CDR.png``, ``Fig3.Sym.pr.IMERG.png``,
``Fig1.Asym.u850.ERA5.png``. A ``README.txt`` there lists the sources. The ``obs_data`` directory is
distributed as ``Wheeler_Kiladis.20261119.tar`` in the MDTF `Digested observational data (Globus)
<https://app.globus.org/file-manager?origin_id=87726236-cbdd-4a91-a904-7cc1c47f8912>`__ collection.

The daily observation files, the scripts that made them, and the alternative figure sets for
TRMM (1998-2019) and ERA5 precipitation (1979-1999) are available from:

- Globus collection ``620e84f2-1f5b-46b7-addd-06e9ba44cfac``, path ``/MDTF_WK_MJO_obs/``
  (`Globus link <https://app.globus.org/file-manager?origin_id=620e84f2-1f5b-46b7-addd-06e9ba44cfac&origin_path=%2FMDTF_WK_MJO_obs%2F>`__);
  ``instructions.txt`` there describes the files and how to run them through MDTF.
- https://project.cgd.ucar.edu/projects/MDTF/MDTF_WK_MJO_obs/ (figures and scripts, no data).

The previous observation panels (NCEP/NCAR reanalysis, ERA and TRMM, 2018) used several grids
and periods.

Observation references
^^^^^^^^^^^^^^^^^^^^^^

- Hersbach, H., and co-authors, 2020: The ERA5 global reanalysis. *Q. J. R. Meteorol. Soc.*,
  **146**, 1999-2049, https://doi.org/10.1002/qj.3803.
- Huffman, G. J., and co-authors, 2007: The TRMM Multisatellite Precipitation Analysis (TMPA).
  *J. Hydrometeor.*, **8**, 38-55, https://doi.org/10.1175/JHM560.1.
- Huffman, G. J., E. F. Stocker, D. T. Bolvin, E. J. Nelkin, and J. Tan, 2023: GPM IMERG Final
  Precipitation L3 1 day 0.1 degree x 0.1 degree V07. NASA GES DISC,
  https://doi.org/10.5067/GPM/IMERGDF/DAY/07.
- Lee, H.-T., 2025: Climate Algorithm Theoretical Basis Document (C-ATBD): Outgoing Longwave
  Radiation (OLR) - Daily. NOAA CDR Program, CDRP-ATBD-0526 Rev 2. Dataset:
  https://doi.org/10.25921/9pt5-by77.
- Simmons, A., and co-authors, 2020: Global stratospheric temperature bias and other stratospheric
  aspects of ERA5 and ERA5.1. ECMWF Technical Memorandum 859, https://doi.org/10.21957/rcxqfmg0.

References
----------

   .. _1:

1. Wheeler, Matthew, and George N. Kiladis. “Convectively Coupled Equatorial Waves: Analysis of Clouds and Temperature in the Wavenumber–Frequency Domain.” ​*Journal of the Atmospheric Sciences​* **56**, no. 3 (February 1, 1999): 374–99. https://doi.org/10.1175/1520-0469(1999)056<0374:CCEWAO>2.0.CO;2​.
