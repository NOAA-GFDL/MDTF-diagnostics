GFDL-specific information
=========================

This page contains information specific to the site installation at the `Geophysical Fluid Dynamics Laboratory <https://www.gfdl.noaa.gov/>`__ (GFDL), Princeton, NJ, USA.

Site installation
-----------------

The DET team maintains a site-wide installation of the framework and all supporting data at /home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics. This is kept up-to-date and is accessible from both workstations and PPAN; in particular it is **not** necessary for an end user to set up conda environments or download any supporting data, as described in the installation instructions.

Invoking the package from the site installation's wrapper script automatically prepends ``--site="NOAA_GFDL"`` to the user's command-line flags.

Please contact us if your use case can't be accommodated by this installation.

Additional ways to invoke the package
-------------------------------------

The site installation provides alternative ways to run the diagnostics within GFDL's existing workflow:

1. Called from an interactive shell on PPAN or workstations. This is the standard mode of running the package, described in the rest of the documentation.

2. As a batch job on PPAN, managed via slurm. This previously required its own wrapper script, but now can be done using the same entry point and CLI options as for interactive execution.

3. Within FRE XMLs. This is done by calling the `mdtf_gfdl.csh <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/sites/NOAA_GFDL/mdtf_gfdl.csh>`__ wrapper script from an ``<analysis>`` tag in the XML:

   .. code-block:: xml

      <analysis switch="on" cumulative="no" script="/home/oar.gfdl.mdtf/mdtf/MDTF-diagnostics/sites/NOAA_GFDL/mdtf_gfdl.csh"/>

   The MDTF package behaves as any other analysis script called by FRE from an experiment XML: FRE will populate the wrapper script with the correct paths, date range of the run, etc., so these options don't need to be passed in the XML tag. 

   The wrapper script calls the site installation of the package with the ``--data-manager="GFDL_PP"`` (see below) option. ``GFDL_PP`` defaults to assuming GFDL variable naming :ref:`conventions<ref-data-conventions>`; data which follows other conventions (e.g. fremetarized runs intended for publication as part of CMIP6) requires the ``--convention`` flag to be set explicitly. In general, the wrapper script passes through any additional options set in the tag's ``script`` attribute, in addition to setting the data attributes provided by FRE. Passing through package flags in the ``<analysis>`` tag can be used to, e.g., only run specific PODs for each ``<component>`` with the ``--pods`` option.

   Currently, FRE requires that each analysis script be associated with a single model ``<component>``. This poses difficulties for the MDTF package, which analyzes data from multiple modeling realms/``<component>``\s. We provide two ways to address this issue:

      A. If it's known ahead of time that a given model ``<component>`` will dominate the run time and finish last, one can call ``mdtf_gfdl.csh --run_once`` from an ``<analysis>`` tag in that component only. In this case, the framework will search all data present in the /pp/ output directory when it runs. The ``<component>`` being used doesn't need to generate any data analyzed by the diagnostics; in this case it's only used to schedule the diagnostics' execution.

      B. If one doesn't know which ``<component>`` will finish last, an alternate solution is to call ``mdtf_gfdl.csh`` from *each* ``<component>`` that generates data to be analyzed. This is assumed to be the default use case for the wrapper script (when ``--run_once`` is not set), where the package is called multiple times on a single model run to incrementally update the analysis as data from different components finishes postprocessing. Every time the package is called it will *only* run the diagnostics for which all the input data is available *and* which haven't run already (which haven't written their output to ``$OUTPUT_DIR``).

In case 3A or 3B, you can optionally pass the ``--component_only`` flag to the wrapper script if you wish to restrict the package to only use data from the ``<component>`` it's associated with in the XML. Otherwise, the default behavior is for the package to search all the data that's present in the /pp/ directory hierarchy when it runs.

The ``--run_once`` flag should be used whenever you don't need the incremental update capability of case 3B (or if the package is only being called from one ``<component>`` in an XML), since the default behavior in 3B necessarily disables logging warnings if individual PODs aren't able to run.


Additional data sources
-----------------------

In addition to the framework's :ref:`built-in data sources<ref-data-sources>`, several data sources are defined that are only accessible to GFDL users. 

All the data sources in this section use GFDL's in-house General Copy Program (GCP, not to be confused with Google Compute Platform) for all file transfers. If GCP is not present on ``$PATH`` when the package is started, the package will load the appropriate environment module.

Any data which is on GFDL's DMF tape-backed filesystem will be requested with ``dmget`` prior to copy. All files requested by all PODs are batched into a single call to ``dmget`` and to GCP. Framework execution blocks after the call to ``dmget`` is issued (the framework has no other tasks to do until the data is transferred locally), which can lead to long or unpredictable run times if data that has been migrated to tape is requested.

CMIP6 data on the Unified Data Archive
++++++++++++++++++++++++++++++++++++++

Selected via ``--data-manager="CMIP6_UDA"``.

Data source for analyzing CMIP6 data made available on on the Unified Data Archive (UDA)'s high-priority storage at /uda/CMIP6. Command-line options and method of operation are the same as documented in :ref:`ref-data-source-cmip6`.

CMIP6 data on the /archive filesystem
+++++++++++++++++++++++++++++++++++++

Selected via ``--data-manager="CMIP6_archive"``.

The same as above, but for analyzing the wider range of CMIP6 data on the DMF filesystem at /archive/pcmdi/repo/CMIP6. Command-line options and method of operation are the same as documented in :ref:`ref-data-source-cmip6`.

CMIP6 data on /data\_cmip6
++++++++++++++++++++++++++

Selected via ``--data-manager="CMIP6_data_cmip6"``.

The same as above, but for analyzing pre-publication data on /data\_cmip6/CMIP6 (only mounted on PPAN). Command-line options and method of operation are the same as documented in :ref:`ref-data-source-cmip6`.

Results of FREPP-processed runs
+++++++++++++++++++++++++++++++

Selected via ``--data-manager="GFDL_PP"``.

This data source searches for model data produced using GFDL's in-house postprocessing tool, FREPP. Note that this is a completely separate concern from invoking the package from the FRE pipeline (described above): data that has been processed and saved in this convention can be analyzed equally well in any of the package's modes of operation.

**Command-line options**

<*CASE_ROOT_DIR*> should be set to the root of the postprocessing directory hierarchy (i.e., should end in ``/pp``).

--component    If set, only run the package on data from the specified model component name. If this flag is *not* set, the data source will return data from different model ``<component>``\s requested by the same POD; see the description of the heuristics used for ``<component>`` selection below. This is necessary for, e.g., PODs that compare data from different modeling realms. The main use case for this flag is passing options from FRE to the package via the wrapper script.
--chunk_freq    If set, only run the package on data with the specified timeseries chunk length. If not set, default behavior is to use the smallest chunks available. The main use case for this flag is passing options from FRE to the package via the wrapper script.

When using this data source, ``-c``/``--convention`` should be set to the convention used to assign variable names. If not given, ``--convention`` defaults to ``GFDL``.

**Data selection heuristics**

This data source implements the following logic to guarantee that all data it provides to the PODs are consistent, i.e. that the variables selected have been generated from the same run of the same model. An error will be raised if no set of variables can be found that satisfy the user's input above and the following requirements:

* This data source only searches data saved as time series (``/ts/``), rather than time averages, since no POD is currently designed to use time-averaged data.
* If the same data has been saved in files of varying chronological length (``<chunk_freq>``), the shortest ``<chunk_freq>`` is used, in order to minimize the amount of data that is transferred but not used (because it falls outside of the user's analysis period).
* By default, any variable can come from model ``<component>``, with the same component used for all variables requested by a POD if possible. This setting is required to enable the execution of PODs that use data from different ``<component>``\s or realms. 

  - Specifying a model component with the ``--component`` flag does one of two things, depending on whether the package is being run once or incrementally. 
  - If the package is being run once, all data used must come from that component (e.g., multi-realm PODs will not run). In this case we assume the user wants to focus their attention on this component exclusively.
  - If the package is being run incrementally (called from FRE without the ``--run_once`` flag, see above, or called in general with the ``--frepp`` flag), all data for each POD must come from the same component, but different PODs may use data from different components. This is because we're operating according to scenario 3B (above) and are analyzing multiple components, but still want to focus on component-specific diagnostics.

* If the same data is provided by multiple model ``<component>``\s, a single ``<component>`` is selected via the following heuristics:

  - Preference is given to model components starting with "cmip" (case insensitive), in order to support analysis of data produced as part of CMIP6.
  - If multiple ``<component>``\s are still eligible, the one with the fewest words in the identifier (separated by underscores) is selected; in case of a tie, the ``<component>`` name with the shortest overall string length is used.
  - This is haphazard, but it's the best we can do given that ``<component>`` names may be arbitrary strings, with only partial standardization.

Quasi-automated source selection
++++++++++++++++++++++++++++++++

Selected via ``--data-manager="GFDL_auto"``.

Provided mostly for backwards compatibility, this dispatches operation to the ``CMIP6_UDA`` or ``GFDL_PP`` data sources based on whether <*CASE_ROOT_DIR*> is a valid postprocessing directory. Command-line options are the union of those for the ``CMIP6_UDA`` or ``GFDL_PP`` data sources.


Additional command-line options
-------------------------------

In addition to the framework's built-in `command-line options <../sphinx/ref_cli.html>`__, the following site-specific options are recognized.

For long command line flags, words may be separated with hyphens (GNU standard) or with underscores (python variable name convention). For example, ``--file-transfer-timeout`` and ``--file_transfer_timeout`` are both recognized by the package as synonyms for the same setting.

GFDL-specific flags
+++++++++++++++++++

The following new flags are added:

--GFDL-PPAN-TEMP <DIR>    If running on the GFDL PPAN cluster, set the ``$MDTF_TMPDIR`` environment variable to this location and create temp files here. This must be a location accessible via GCP, and the package does not currently verify this. Defaults to ``$TMPDIR``.
--GFDL-WS-TEMP <DIR>    If running on a GFDL workstation, set the ``$MDTF_TMPDIR`` environment variable to this location and create temp files here. The directory will be created if it doesn't exist. This must be accessible via GCP, and the package does not currently verify this. Defaults to /net2/``$USER``/tmp.
--frepp    Normally this is set by the `mdtf_gfdl.csh <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/sites/NOAA_GFDL/mdtf_gfdl.csh>`__ wrapper script (by default, unless the ``--run_once`` flag is set), and not directly by the user. This should only be set if you're using the package in scenario 3B. above, where the package will be called **multiple** times when each model component is finished running. When the package is invoked with this flag, it only runs PODs for which i) the data has finished post-processing (is present in the /pp/ directory) and ii) haven't been run by a previous invocation of the package. The bookkeeping for this is done by having each invocation write placeholder directories for each POD it's executing to ``$OUTPUT_DIR``. Setting this flag disables the package's warnings for PODs with missing data, since that may be a normal occurrence in this scenario.

GFDL-specific default values
++++++++++++++++++++++++++++

The following paths are set to more useful default values:

--OBS-DATA-REMOTE <DIR>    Site-specific installation of observational data used by individual PODs at /home/oar.gfdl.mdtf/mdtf/inputdata/obs\_data. If running on PPAN, this data will be GCP'ed to the current node. If running on a workstation, it will be symlinked.
--OBS-DATA-ROOT <OBS_DATA_ROOT>    Local directory for observational data. Defaults to ``$MDTF_TMPDIR``/inputdata/obs_data, where the environment variable ``$MDTF_TMPDIR`` is defined as described above.
--MODEL-DATA-ROOT <MODEL_DATA_ROOT>    Local directory used as a destination for downloaded model data. Defaults to ``$MDTF_TMPDIR``/inputdata/model, where the environment variable ``$MDTF_TMPDIR`` is defined as described above.
--WORKING-DIR <WORKING_DIR>    Working directory. Defaults to ``$MDTF_TMPDIR``/wkdir, where the environment variable ``$MDTF_TMPDIR`` is defined as described above.
-o, --OUTPUT-DIR <OUTPUT_DIR>     Destination for output files. Defaults to ``$MDTF_TMPDIR``/mdtf_out, which will be created if it doesn't exist.

