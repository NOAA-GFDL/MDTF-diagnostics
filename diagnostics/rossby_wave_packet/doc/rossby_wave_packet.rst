.. _rossby_wave_packet:

Rossby Wave Packet Diagnostics
============================================

Last update: September 2026

This Rossby Wave Packet (RWP) POD diagnoses envelope amplitude, wrapped phase, phase speed, and horizontal group velocity from six-hourly model northward wind at 250 hPa. For each model case selected in an MDTF run, the POD uses the framework-prepared wind field and writes the diagnostic fields to NetCDF together with summary figures. It also supports direct analysis of a NetCDF file without using the MDTF framework.

Version and contact information
-------------------------------

* Version 1.2.0 (September 2026)
* Scientific PI: **Lei Wang, wanglei@purdue.edu**
* Developer and email: **Yuan-Bing Zhao, dr.yuanbingzhao@gmail.com**

Open-source copyright agreement
--------------------------------

The RWP POD is distributed under the LGPLv3 license used by the
MDTF-diagnostics framework. See ``LICENSE.txt`` at the top level of the
framework repository.

Functionality
-------------

The POD has one main driver, ``src/rossby_wave_packet.py``. During an MDTF run,
the driver reads
``case_env_file`` and associates each entry in ``CASE_LIST`` with the exact
processed model file recorded in ``CATALOG_FILE``. The file is opened through
Intake-ESM. Case-specific names such as ``va250_var``, ``time_coord``,
``lat_coord``, and ``lon_coord`` are passed to the calculation instead of
assuming CMIP variable names. This permits the same POD to process translated
CMIP, CESM, and GFDL model output.

The reusable ``run_rwp`` function in ``src/rossby_wave_packet_core.py``
performs the scientific calculation. It:

#. selects the configured dates, latitude band, and pressure level;
#. estimates and removes the annual cycle, removes the record mean, or leaves
   the background unchanged;
#. retains the configured zonal wavenumber band;
#. forms the analytic signal along longitude and obtains envelope amplitude
   and wrapped phase;
#. calculates phase speed from wrapped temporal and zonal phase differences;
#. smooths the envelope, identifies sufficiently large packets, tracks each
   packet at the adjacent times, and calculates zonal and meridional group
   velocity using the packet-segment method.

Required programming language and libraries
-------------------------------------------

* Python 3.12 or newer
* NumPy and SciPy
* xarray, netCDF4, cftime, and Dask
* matplotlib
* Intake-ESM
* PyYAML

All requirements are present in the standard MDTF ``python3_base``
environment; the POD does not add a separate Conda environment.

Required model output
---------------------

The request in ``settings.jsonc`` is:

.. list-table:: Model variable requested by the RWP POD
   :header-rows: 1
   :widths: 16 28 14 12 30

   * - POD name
     - CF standard name
     - Units
     - Frequency
     - Dimensions
   * - ``va250``
     - ``northward_wind``
     - ``m s-1``
     - six-hourly
     - time, latitude, longitude; scalar pressure = 250 hPa

The framework may extract 250 hPa from a model pressure-level field or use a
native single-level 250-hPa field, depending on the model convention. The POD
does not require a pressure dimension after framework preprocessing. In
standalone mode, pressure may be supplied in Pa or hPa and the driver selects
the nearest requested level.

The horizontal grid must be rectilinear, regularly spaced in longitude, and
global in longitude. Longitude may be represented as 0--360 or -180--180 and
may contain a duplicate cyclic endpoint. Latitude may be ascending or
descending. Curvilinear, cubed-sphere, and limited-area grids must be
regridded to a regular global latitude-longitude grid before this POD is run.

Time and calendar handling
--------------------------

Time must be monotonic, uniformly sampled, and decodable under CF conventions.
The harmonic annual-cycle calculation supports standard, Gregorian,
proleptic-Gregorian, Julian, 365-day/noleap, 366-day/all-leap, and 360-day
calendars. Leap-day alignment is handled explicitly for Gregorian and Julian
records. The timestep must divide a 24-hour day when harmonic preprocessing is
used.

Use at least one complete year of model output when estimating the default
harmonic annual cycle. Longer records generally give a more representative
seasonal climatology. A short record may be used when its seasonal cycle is
negligible by setting ``ROSSBY_WAVE_PACKET_ANOMALY_METHOD`` to ``none``; the POD then proceeds
to zonal filtering and computes amplitude and phase. If the supplied model
field is already an anomaly filtered to the intended zonal wavenumbers, set
``ROSSBY_WAVE_PACKET_PREFILTERED_INPUT`` to ``true`` to begin directly with amplitude and
phase.

Diagnostic parameters
---------------------

The defaults are declared as strings in the ``pod_env_vars`` section of
``settings.jsonc``. MDTF applies these POD-wide settings to all cases in one
run. Standalone users can set the corresponding command-line options; run
``python src/rossby_wave_packet.py --help`` for the complete interface.

.. list-table:: Principal calculation and plotting parameters
   :header-rows: 1
   :widths: 31 16 53

   * - Setting
     - Default
     - Purpose
   * - ``ROSSBY_WAVE_PACKET_ANOMALY_METHOD``
     - ``harmonic``
     - Background treatment: harmonic annual cycle, record mean, or none.
   * - ``ROSSBY_WAVE_PACKET_ANNUAL_HARMONICS``
     - 4
     - Highest annual harmonic retained in the estimated seasonal cycle.
   * - ``ROSSBY_WAVE_PACKET_WAVENUMBER_MIN``, ``ROSSBY_WAVE_PACKET_WAVENUMBER_MAX``
     - 4, 15
     - Integer zonal wavenumbers retained in the wave field.
   * - ``ROSSBY_WAVE_PACKET_AMPLITUDE_THRESHOLD``
     - 25 m s-1
     - Minimum envelope used by the phase-speed calculation.
   * - ``ROSSBY_WAVE_PACKET_GROUP_AMPLITUDE_THRESHOLD``
     - 20 m s-1
     - Envelope threshold used to identify packets for group velocity.
   * - ``ROSSBY_WAVE_PACKET_MINIMUM_ZONAL_EXTENT``
     - 20 degrees
     - Minimum zonal packet length.
   * - ``ROSSBY_WAVE_PACKET_MINIMUM_MERIDIONAL_EXTENT``
     - 10 degrees
     - Minimum meridional packet width.
   * - ``ROSSBY_WAVE_PACKET_SMOOTHING_SIGMA_DEGREES``
     - 4 degrees
     - Gaussian envelope smoothing scale in each horizontal direction.
   * - ``ROSSBY_WAVE_PACKET_GROUP_SPEED_LIMIT``
     - 100 m s-1
     - Absolute mask applied independently to group-velocity components.
   * - ``ROSSBY_WAVE_PACKET_LATITUDE_MIN``, ``ROSSBY_WAVE_PACKET_LATITUDE_MAX``
     - 25, 85
     - Analysis latitude bounds in degrees north; negative values select the
       Southern Hemisphere.
   * - ``ROSSBY_WAVE_PACKET_PLOT_TIME``
     - ``midpoint``
     - Phase-snapshot time, or a date/time resolved to the nearest record.

Method details
--------------

Envelope amplitude and phase
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After background removal, a Fourier transform along each latitude circle
retains zonal wavenumbers 4--15 by default. A Hilbert transform along the
cyclic longitude coordinate forms the analytic signal. Its magnitude is the
local envelope amplitude and its angle is the wrapped phase in the interval
-pi to pi.

Phase speed
^^^^^^^^^^^

Phase speed is the ratio of the wrapped temporal phase derivative to the local
zonal wavenumber. Centered time and longitude differences are used internally;
one-sided time differences are used at the first and last records. A point is
retained only when the envelope at the derivative stencil exceeds
``ROSSBY_WAVE_PACKET_AMPLITUDE_THRESHOLD``. An optional absolute speed limit can be enabled
with ``ROSSBY_WAVE_PACKET_PHASE_SPEED_LIMIT``.

Group velocity
^^^^^^^^^^^^^^

The group-velocity calculation follows the packet-segment procedure in the
retained research implementation. The envelope is Gaussian-smoothed with
cyclic longitude and nearest-value latitude boundaries. Zonal and meridional
segments must exceed the configured amplitude and spatial-extent thresholds.
Segments are tracked within a search window at the preceding and following
times, and local packet-envelope phase derivatives yield the two group-
velocity components. The first and last records are undefined because this
step requires centered time differences.

Output and interpretation
-------------------------

The POD writes the following fixed-name web figures to ``$WORK_DIR/model``:

* ``rossby_wave_packet_amplitude.png``: time-mean envelope amplitude for every model case;
* ``rossby_wave_packet_phase.png``: wrapped phase at the configured snapshot time;
* ``rossby_wave_packet_phase_speed.png``: phase speed at the configured snapshot time;
* ``rossby_wave_packet_group_velocity.png``: horizontal group-velocity magnitude and vectors
  at the configured snapshot time.

Each model case also receives a file named
``rossby_wave_packet_<case>.nc`` in
``$WORK_DIR/model/netCDF``. It contains filtered northward-wind anomalies,
amplitude, phase, phase speed, and both group-velocity components. The fixed
``rossby_wave_packet_output_manifest.csv`` associates case labels with filenames and records
the phase-snapshot time used in the web figure.

The instantaneous speed figures preserve these masks. A time mean formed by
skipping missing values would combine packet locations from different records
and could make the diagnostic appear valid over most of the domain. Masked
regions have not met the relevant envelope or packet-size thresholds, are
derivative endpoints, or exceed a configured speed limit. Thresholds should
be assessed against each model's upper-level variability and horizontal
resolution before intermodel differences are interpreted.

Running the POD
---------------

The MDTF framework invokes the driver after model-data preprocessing. Add
``rossby_wave_packet`` to ``pod_list`` and run the framework with a completed
runtime configuration:

.. code-block:: console

   python mdtf_framework.py -f <runtime-configuration.jsonc>

For a direct model-file run, invoke the same driver:

.. code-block:: console

   python src/rossby_wave_packet.py \
     --input <model-wind.nc> \
     --output-dir output \
     --start-date 1980-01-01 \
     --end-date 1980-12-31

Use ``--level none`` for a field already reduced to one pressure level. Print
the complete generated interface with:

.. code-block:: console

   python src/rossby_wave_packet.py --help

The driver exports a ``DRIVER_HELP`` dictionary and uses it to generate the
command help. Its keys and matching options are:

.. list-table:: Driver help dictionary
   :header-rows: 1
   :widths: 27 31 42

   * - Dictionary key
     - Command option
     - Purpose
   * - ``input``
     - ``--input``
     - Standalone model NetCDF input.
   * - ``catalog_file``, ``case_info``, ``case``
     - ``--catalog-file``, ``--case-info``, ``--case``
     - MDTF catalog and case selection.
   * - ``variable``, ``time_name``, ``latitude_name``, ``longitude_name``,
       ``level_name``
     - ``--variable`` and coordinate-name options
     - Explicit names when metadata are incomplete.
   * - ``level``, ``latitude_min``, ``latitude_max``, ``start_date``,
       ``end_date``
     - Data-selection options
     - Pressure, latitude, and time selection.
   * - ``prefiltered_input``, ``anomaly_method``, ``annual_harmonics``
     - Preprocessing options
     - Background removal or prefiltered-input mode.
   * - ``wavenumber_min``, ``wavenumber_max``
     - Wavenumber options
     - Retained zonal spectral band.
   * - ``amplitude_threshold``, ``phase_speed_limit``
     - Phase-speed options
     - Phase-speed masking controls.
   * - ``group_velocity``, ``group_amplitude_threshold``,
       ``minimum_zonal_extent``, ``minimum_meridional_extent``,
       ``smoothing_sigma_degrees``, ``group_speed_limit``
     - Group-velocity options
     - Packet detection, smoothing, and masking controls.
   * - ``output_dir``, ``output_prefix``, ``chunks_time``, ``plot``,
       ``plot_time``, ``dry_run``
     - Execution options
     - Output, chunking, plotting, and discovery-only controls.

Standalone operation
--------------------

The same driver can analyze a regular latitude-longitude NetCDF file without
the framework:

.. code-block:: console

   python src/rossby_wave_packet.py --input <model-wind.nc> --output-dir output

Variable and coordinate names are inferred from CF metadata and common model
aliases. Every name can be supplied explicitly for incomplete metadata. Use
``--level none`` for an input already reduced to one pressure level. The
public Python interface exposes the calculation as one function:

.. code-block:: python

   import xarray as xr
   from src.rossby_wave_packet_core import run_rwp

   source = xr.open_dataset("model_va.nc", chunks={"time": 32})
   result = run_rwp(source, level=250, latitude_min=25, latitude_max=85)

References
----------

Fragkoulidis, G., and V. Wirth, 2020: Local Rossby wave packet amplitude,
phase speed, and group velocity: Seasonal variability and their role in
temperature extremes. *Journal of Climate*, **33**, 8767--8787,
`doi:10.1175/JCLI-D-19-0377.1
<https://doi.org/10.1175/JCLI-D-19-0377.1>`__.
