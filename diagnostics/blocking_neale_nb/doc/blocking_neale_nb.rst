.. Format guides/tools:
   https://docutils.sourceforge.io/docs/user/rst/quickref.html
   https://sublime-and-sphinx-guide.readthedocs.io/en/latest/code_blocks.html
   Rendered MDTF diagnostics/*/doc/example.rst https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx_pods/example.html)

Rich Neale's Blocking Diagnostic Documentation (notebook version)
=================================================================

Evaluates blocking frequency as determined by the meridional gradient above
a threshold value of daily 500mb height following
:ref:`D'Andrea et al (1998) <ref-DAndrea>` (a 1D index, a function of
longitude), and a 2D variant where the same test is applied over a band of
latitudes following :ref:`Davini et al (2012) <ref-Davini>`.

This POD (``blocking_neale_nb``) is a Python / Jupyter notebook version of the
NCL POD ``blocking_neale``. The notebook ``blocking_main.ipynb`` can be run by
the MDTF framework, or stand-alone (interactively in Jupyter or from the
command line). A stand-alone run writes the same output as a framework run:
the POD web page, figures, executed notebook, logs, a top-level ``index.html``
and (optionally) the tar file.

Version & Contact info
----------------------
| Version 3.0 (Python notebook), MDTF v4
| PI: Rich Neale, NCAR, rneale@ucar.edu
| Contact: Dani Coleman, NCAR, bundy@ucar.edu

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The MDTF framework is distributed under the LGPLv3 license (see LICENSE.txt)


Functionality
-------------

Required programming language and libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Python 3 with numpy, pandas, xarray, scipy, matplotlib, cartopy, intake-esm
and nbconvert. These are all in the standard MDTF ``_MDTF_python3_base``
conda environment. NCL is not needed.

Required model output variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Daily geopotential height at 500 hPa (``zg``, or a 3D field with air pressure
levels, from which the framework extracts 500 hPa).

Comparison data
^^^^^^^^^^^^^^^

- Observations: ERA5 (1979-2005) and MERRA (1979-2011), daily Z500,
  read from ``/glade/work/rneale/data/<OBS>/Z500.day.mean.nc``.
- Model ensembles: CESM2 Large Ensemble daily Z500 from
  ``/glade/campaign/cgd/cesm/CESM2-LE``. CESM1-LE, E3SMv1, E3SMv2, EAMv2 and
  CAM6 are also recognized (``blocking_utils.find_ens_info``,
  ``lens_simulations.py``).

These paths are on NCAR's GLADE file system, so at present the comparison
data are only available there.


Settings/Environment Variables
------------------------------

POD settings (``settings.jsonc``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set in ``pod_env_vars`` in ``settings.jsonc``. The framework passes them to
the notebook as environment variables, so every value is a string and lists
are comma-separated.

==============================  ======================  ==============================================
Variable                        Default                 Meaning
==============================  ======================  ==============================================
``MDTF_BLOCKING_SEASON``        ``"DJF"``               Season for the seasonal line plot and maps:
                                                        DJF, MAM, JJA, SON or ANN
``MDTF_BLOCKING_HEMISPHERE``    ``"nhem"``              Hemisphere (only nhem is implemented)
``MDTF_BLOCKING_ENSEMBLES``     ``"ERA5,MERRA,CESM2"``  Observations and model ensembles to compare
                                                        against the MDTF case(s)
``MDTF_BLOCKING_ENS_MEMBERS``   ``"1,1,2"``             Number of members to use from each entry in
                                                        ``MDTF_BLOCKING_ENSEMBLES`` (same order)
``MDTF_BLOCKING_REF_FIRSTYR``   ``""``                  First year for the comparison data.
                                                        Blank: use the case years
``MDTF_BLOCKING_REF_LASTYR``    ``""``                  Last year for the comparison data.
                                                        Blank: use the case years
``MDTF_BLOCKING_RECOMPUTE``     ``"False"``             Recompute cached blocking frequencies:
                                                        "False", "True" (all) or dataset names,
                                                        e.g. "CESM2,ERA5"
``MDTF_BLOCKING_CACHE_DIR``     ``""``                  Where to keep blocking frequency files.
                                                        Blank: this run's ``model/netCDF``
==============================  ======================  ==============================================

The comparison data need to cover the reference years: with the defaults
(blank), the case years must fall within the obs periods above. For a long
comparison, for example, set ``MDTF_BLOCKING_REF_FIRSTYR = "1979"`` and
``MDTF_BLOCKING_REF_LASTYR = "1999"``.

Run settings (``input_*.yml``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The usual MDTF runtime configuration: ``case_list`` (case name, convention,
``startdate``, ``enddate``), ``DATA_CATALOG``, ``OBS_DATA_ROOT``,
``WORK_DIR``, ``OUTPUT_DIR``, ``conda_root``, ``conda_env_root``,
``make_variab_tar``, ``overwrite``, etc. For a stand-alone run the case data
are read from ``DATA_CATALOG`` with intake-esm, using the same query as the
framework: the catalog path must contain the case name, and the variable is
matched on frequency, realm and standard name.

Settings in the notebook
^^^^^^^^^^^^^^^^^^^^^^^^

Near the top of the notebook are two text cells, written in the formats of
the two files above:

- ``runtime_yml``: the run settings, in ``input_*.yml`` format
- ``pod_settings_jsonc``: the POD settings, identical to ``settings.jsonc``

Edit these to change an interactive run. The export cell writes them out as
``input_<case>.yml`` and ``settings.jsonc`` (to the POD output directory) and
prints the commands to repeat the same run in batch. Where the settings come
from depends on how the notebook is run:

================================  =============================================
Run mode                          Settings source
================================  =============================================
Interactive (Jupyter)             The two text cells in the notebook
Stand-alone, command line         ``--config`` and ``--settings`` files
                                  (``MDTF_RUNTIME_CONFIG``, ``MDTF_POD_SETTINGS``)
MDTF framework (``mdtf -f``)      Environment variables set by the framework;
                                  the case data are the framework's
                                  preprocessed file (``MODEL_DATA_PATH``)
================================  =============================================


How to run
----------

1. MDTF framework: add ``blocking_neale_nb`` to ``pod_list`` and run

   ``./mdtf -f input_<case>.yml``

2. Stand-alone, command line (from the top of the MDTF-diagnostics repo, in an
   MDTF python3 conda env):

   ``python -m src.standalone_html run diagnostics/blocking_neale_nb/blocking_main.ipynb --config input_<case>.yml [--settings settings.jsonc] [--kernel <name>]``

   This executes the notebook with ``jupyter nbconvert``, saves it as
   ``blocking_main_ipynb.html`` in the POD output directory, and makes the tar
   file if ``make_variab_tar`` is True. It does not need the framework's conda
   setup or preprocessing.

3. Interactive: open ``blocking_main.ipynb`` in Jupyter with an MDTF python3
   kernel, edit the settings cells and run all cells. Save the notebook
   (Ctrl-S) before the last cell runs, or save and then re-run the last cell.
   That cell writes ``blocking_main_ipynb.html`` from the saved notebook
   (``standalone_html.export_saved_notebook``; nbconvert reads the file on
   disk, not the running kernel), then the web page and the tar file. If the
   notebook has not been saved since the run started it skips the html and
   says so. The html does not show the last cell's own output.

Output
^^^^^^

All three methods write the framework layout under
``<WORK_DIR>/MDTF_output`` (``MDTF_output.v1``, ``.v2``, ... if
``overwrite`` is False):

- ``index.html``, ``mdtf_diag_banner.png``, ``config_save.json``, logs
- ``blocking_neale_nb/blocking_neale_nb.html`` (the POD page)
- ``blocking_neale_nb/model/*.png``, ``blocking_neale_nb/obs/*.png`` (figures)
- ``blocking_neale_nb/model/netCDF/block_*.nc`` (blocking frequencies)
- ``blocking_neale_nb/blocking_main_ipynb.html`` (executed notebook)
- ``<WORK_DIR>/MDTF_output.tar`` if ``make_variab_tar`` is True

Blocking frequency files
^^^^^^^^^^^^^^^^^^^^^^^^

Each blocking frequency result (1D, 2D and annual cycle, for each dataset) is
saved as a netCDF file named by index, dataset, number of members, years and
season, for example ``block_1D_CESM2_nens.5_1979-1999_ANN.nc``. A later run that
needs the same result reads the file instead of recomputing it:

- The files go in ``MDTF_BLOCKING_CACHE_DIR``. Blank means this run's
  ``model/netCDF``, so results are reused only within the same output
  directory. Set it to a shared directory to reuse the obs and model ensemble
  results (most of the run time) across runs and cases. The files used are
  always copied to ``model/netCDF`` as well, so the output is complete.
- Each file records the version of the calculation
  (``BLOCKING_CALC_VERSION`` in ``blocking_utils.py``). Files from another
  version are recomputed automatically; increase the version whenever a code
  change alters the results.
- ``MDTF_BLOCKING_RECOMPUTE`` forces a recalculation: ``"True"`` for
  everything, or a comma-separated list of datasets (e.g. a case whose data
  were rewritten under the same name).


Methodology
-----------

1D blocking index
^^^^^^^^^^^^^^^^^

Following :ref:`Tibaldi and Molteni (1990) <ref-Tibaldi-Molteni>` and
:ref:`D'Andrea et al (1998) <ref-DAndrea>`, at every longitude and day the
500mb height gradients are computed around the central latitude
phi0 = 60N, with phiN = 78.85N and phiS = 41.25N:

- GHGN = (Z500(phiN) - Z500(phi0)) / (phiN - phi0)
- GHGS = (Z500(phi0) - Z500(phiS)) / (phi0 - phiS)

The test is repeated with all three latitudes shifted by -3.75, 0 and +3.75
deg (the nearest grid latitudes are used). A longitude is blocked on a given
day if GHGS > 0 and GHGN < -5 m per deg latitude for any of the three shifts.
The latitudes used span 37.5N-82.6N, so Z500 is read over 20N-90N.

Blocking frequency is the fraction of days blocked: for the chosen season
(``MDTF_BLOCKING_SEASON``; ANN uses every day) in the line plot, and for each
day of the year in the annual cycle.

Blocking frequency maps (2D index)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The POD also shows polar stereographic maps of Northern Hemisphere blocking
frequency for the chosen season, one panel for each MDTF case,
observational product and model ensemble (ensemble mean).

These use a 2D blocking index following :ref:`Davini et al. (2012) <ref-Davini>`.
Instead of testing the 500mb height gradients only around a fixed central
latitude band (the 1D index above), the test is applied at every grid
latitude phi0 between 35N and 75N, using the heights 15 deg to the north and
south (nearest grid latitudes):

- GHGN = (Z500(phi0+15) - Z500(phi0)) / 15
- GHGS = (Z500(phi0) - Z500(phi0-15)) / 15

A grid point is blocked on a given day when GHGS > 0 and GHGN < -5 m per
deg latitude (the same thresholds as the 1D index). The blocking frequency
is the fraction of days in the season that each point is blocked, so the maps
locate blocking in latitude as well as longitude.

Ensembles
^^^^^^^^^

For a model ensemble the frequency is computed for each member. The line
plot shows the ensemble mean with the member range shaded, and the maps and
annual cycle show the ensemble mean.


Code Overview
-------------

- ``blocking_main.ipynb``: the driver notebook. Sections:

  1. Settings: the ``runtime_yml`` and ``pod_settings_jsonc`` text cells,
     ``standalone_html.load_run_settings`` (works out the run mode and the
     settings), and the export cell.
  2. Load model data: the framework's ``MODEL_DATA_PATH`` file in a framework
     run, otherwise ``standalone_html.open_catalog_var`` (intake-esm).
  3. Comparison data: ``blocking_utils.ens_setup`` builds the ``block_meta``
     table (one row per dataset: type obs/model/mdtf, number of members,
     years, run names, files); the MDTF case(s) are added as rows; then
     ``blocking_utils.dataset_get`` reads Z500 for each dataset.
  4. Blocking frequencies: ``blocking_utils.block_z500_freq`` with
     ``block_diag='1D'`` (seasonal, by longitude), ``'2D'`` (seasonal maps)
     and ``'1DAC'`` (annual cycle, by day of year and longitude).
     Results are cached (see Blocking frequency files above).
  5. Figures: ``blocking_figs.block_plot_1d``, ``block_plot_2d`` and
     ``block_plot_anncycle``.
  6. Output: ``standalone_html.make_standalone_output`` writes the web page
     and the rest of the framework output (skipped in a framework run, where
     the framework does this).

- ``blocking_utils.py``: data setup and reading (``ens_setup``,
  ``find_ens_info``, ``dataset_get``) and the blocking calculations
  (``block_z500_freq``, with the cache helpers).
- ``blocking_figs.py``: figures.
- ``lens_simulations.py``: run names of the model ensemble members (from
  Rich Neale's blocking scripts).
- ``blocking_neale_nb.html``: the POD web page template.
- ``src/standalone_html.py`` (MDTF framework source): settings handling,
  catalog reading, web page and output for stand-alone notebook runs, and the
  command-line runner. It reuses the framework's own output code and
  templates, and is written to be usable by other notebook PODs.


Figures
-------

- Average seasonal cycle (combined): blocking frequency (%) vs longitude for
  ``MDTF_BLOCKING_SEASON``. Observations are black lines, model ensembles are
  colored dashed lines with the member range shaded, and the MDTF case(s) are
  solid colored lines.

- Annual cycle: Hovmoller plots of blocking frequency (%) by longitude and
  time of year, in separate figures for the MDTF case, the observations and
  the model ensembles, as in the NCL POD. The daily climatology is smoothed
  with 20 passes of a 9-point smoother (the Python equivalent of NCL
  ``smth9`` with p = q = 0.5, wrapping in longitude). Contours every 5%;
  shaded light grey for 10-20% and dark grey above 20%.

- Blocking frequency maps (2D index): polar stereographic maps of the
  seasonal blocking frequency, one panel per dataset.

The figures below are from the NCL version of the POD.

.. figure:: figure_freq_season.png
   :align: left
   :width: 75 %

.. figure:: figure_anncycle.OBS.png
   :align: left
   :width: 75 %

.. figure:: figure_anncycle.CAM5.png
   :align: left
   :width: 75 %

References
----------


.. _ref-Tibaldi-Molteni:

   1. Tibaldi and Molteni (1990): On the operational predictability of
   blocking. *Tellus A: Dynamic Meteorology and Oceanography*, **42** (3),
   343-365, `doi:10.3402/tellusa.v42i3.11882 <https://doi.org/10.3402/tellusa.v42i3.11882>`__.

.. _ref-DAndrea:

   2. D'Andrea, F., Tibaldi, S., Blackburn, M. et al. (1998): Northern
   Hemisphere atmospheric blocking as simulated by 15 atmospheric general
   circulation models in the period 1979-1988. *Climate Dynamics*, **14**,
   385-407 `doi:10.1007/s003820050230 <https://doi.org/10.1007/s003820050230>`__.

.. _ref-Davini:

   3. Davini, P., Cagnazzo, C., Neale, R., and Tribbia, J. (2012): Coupling
   between Greenland blocking and the North Atlantic Oscillation pattern,
   *Geophys. Res. Lett.*, **39**, L14701, `doi:10.1029/2012GL052315
   <https://doi.org/10.1029/2012GL052315>`__.

