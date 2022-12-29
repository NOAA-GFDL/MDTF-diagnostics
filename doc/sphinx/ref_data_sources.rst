.. _ref-data-sources:

Model data sources
==================

This section details how to select the input model data for the package to analyze.
The command-line option for this functionality is the ``--data-manager`` flag, which selects a "data source":
a code plug-in that implements all functionality needed to obtain model data needed by the PODs, based on user input:

* An interface to query the remote store of data for the variables requested by the PODs, whether in the form of a file naming convention or an organized data catalog/database;
* (Optional) heuristics for refining the query results in order to guarantee that all data selected came from the same model run;
* The data transfer protocol to use for transferring the selected data to a local filesystem, for processing by the framework and by the PODs.

Each data source may define its own specific command-line options, which are documented here. 

The choice of data source determines where and how the data needed by the diagnostics is obtained,
but doesn't specify anything about the data's contents. For that purpose we allow the user to specify a
"variable naming :ref:`convention<ref-data-conventions>`" with the ``--convention`` flag.
Also consult the :doc:`requirements<ref_data>` that input model data must satisfy in terms of file formats.

There are currently three data sources implemented in the package, described below.
If you're using site-specific functionality (via the ``--site`` flag), additional options may be available;
see the :doc:`site-specific documentation<site_toc>` for your site.
If you would like the package to support obtaining data from a source that hasn't currently been implemented,
please make a request in the appropriate GitHub
`discussion thread <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/175>`__.

.. _ref-data-source-localfile:

Sample model data source
++++++++++++++++++++++++

Selected via ``--data-manager="LocalFile"``. This is the default value for <*data-manager*>.

This data source lets the package run on the sample model data provided with the package and installed by the user
at <*MODEL_DATA_ROOT*>. Any additional data added by the user to this location
(either by copying files, or through symlinks) will also be recognized, provided that it takes the form of one netCDF
file per variable and that it follows the following file and subdirectory naming convention :

<*MODEL_DATA_ROOT*>/<*dataset_name*>/<*frequency*>/<*dataset_name*>.<*variable_name*>.<*frequency*>.nc,

where

* <*dataset_name*> is any string uniquely identifying the dataset,
* <*frequency*> is a string describing the frequency at which the data is sampled, e.g. ``6hr``, ``day``, ``mon``, etc. More specifically, it must take the form of an optional integer (if omitted, the value 1 is understood) followed by a unit string, one of ``hr``, ``day``, ``week``, ``mon`` or ``year``.
* <*variable_name*> is the name of the variable in one of the recognized :ref:`naming conventions<ref-data-conventions>`.

At runtime, the user selects which dataset to use with the following flag:

**Command-line options**

-e, --experiment, --sample-dataset <dataset_name>   | Name of the sample dataset to use. This should correspond to the name of one of the subdirectories in <*MODEL_DATA_ROOT*>. The user is responsible for manually copying or symlinking the files of interest to them; for instructions on downloading the sample model data we provide, see :ref:`ref-supporting-data`.
   |
   | Optional; if not given, this attribute is set equal to <*CASENAME*> (for backwards compatibility reasons).

When using this data source, ``-c``/``--convention`` should be set to the convention used to assign <*variable_name*>s: the data source does not enforce consistency in this setting. If not given, ``--convention`` defaults to ``CMIP`` (see below).

.. _ref-data-source-explictfile:

Explicit file data source
+++++++++++++++++++++++++

Selected via ``--data-manager="Explicit_file"``.

This data source lets the user explicitly assign model data files to each variable requested by a POD using standard shell glob syntax, without needing to move or symlink them to a directory hierarchy (as is needed for, e.g., the :ref:`ref-data-source-localfile`). Files must be on a locally mounted filesystem, and satisfy the requirements in :doc:`ref_data` (with the exception of metadata).

In addition, it also provides the option to rewrite arbitrary metadata attributes in these files, on a per-file basis. This may be useful in situations where the metadata used by the framework is missing or incorrect -- see :ref:`documentation<ref-data-metadata>` for what metadata is used by the framework. Note that many tools offer greater functionality for editing metadata, such as the `ncatted <http://nco.sourceforge.net/nco.html#ncatted>`__ tool in the `NCO <http://nco.sourceforge.net/>`__ utilities and the `setattribute <https://code.mpimet.mpg.de/projects/cdo/embedded/cdo_refcard.pdf>`__ operator in `CDO <https://code.mpimet.mpg.de/projects/cdo>`__.

Due to the number of required configuration options specific to this data source, the only mechanism provided to configure it is via an additional configuration file, passed with the following flag:

**Command-line options**

--config-file <config file path>     Path to a JSONC file configuring the above options. 

An example of the format for this file is:

.. code-block:: js

  {
    "EOF_500PhPa": {
      "zg_hybrid_sigma": "mon/QBOi.EXP1.AMIP.001.Z*.mon.nc",
      "ps": {
        "files": "mon/QBOi.EXP1.AMIP.001.PS.mon.nc",
        "var_name": "PS",
        "metadata": {
          "standard_name": "surface_air_pressure",
          "units": "Pa",
          "any_name": "any_value",
        }
      }
    },
    "example": {
      "tas": "**/NCAR-CAM5.atmos.19??-19??.tas.nc",
    }
  }

The file should be organized as a nested struct, with keys corresponding to names of PODs and then names of variables used by those PODs in their data request. The entry corresponding to variable names can either be a string or another struct. Strings are taken to be a shell glob specifying the set of files that contain the data for that variable. The struct may have up to three keys: ``files`` (the shell glob; required), ``var_name``, the name used for the variable in the data file, and ``metadata``, an arbitrary list of metadata attributes to assign to that variable.

Paths to the data for each variable are specified with standard shell glob syntax as implemented by python's :py:mod:`glob` module: ``?`` matches one character (excluding directory separators), ``*`` matches zero or more characters (excluding directory separators), and ``**`` matches any number of subdirectories. Globs given as relative paths are resolve relative to <*CASE_ROOT_DIR*>. Paths are not validated ahead of time; mis-specified globs or omitted entries (such as ``EOF_500PhPa``'s request for ``zg`` in the example above) are reported as a data query with zero results.

If the name of the variable used by the data files is not specified via the ``var_name`` attribute, it is assumed to be the name for that variable used by the POD in its data request. In either case, if a variable by that name is not found in the data file, the data source will use heuristics to determine the correct name, assuming one dependent variable per data file. (The behavior for all other data sources in this situation is to raise an error.)

Metadata attributes are set as strings, and are not validated before being set on the variable. Setting metadata attributes on a variable's coordinates (such as the ``calendar`` attribute) is not currently supported. Incorrect unit metadata may be fixed either with one of the third-party tools mentioned above, or by setting the ``scale_factor`` and ``add_offset`` `CF attributes <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#attribute-appendix>`__.

The user setting for ``-c``/``--convention`` is ignored by this data source: the ``None`` convention is always used, since the user has assigned files directly to the variable names used by each POD.

If changes to metadata are requested in the config file, the ``--overwrite-file-metadata`` flag is assumed and file metadata will always be overwritten if it differs from the framework's record.


.. _ref-data-source-cmip6:

CMIP6 local file data source
++++++++++++++++++++++++++++

Selected via ``--data-manager="CMIP6"``.

This data source searches for model data stored as netCDF files on a locally-mounted filesystem, in a structured directory hierarchy with directories and files named following the CMIP6 `data reference syntax <https://goo.gl/v1drZl>`__ (DRS). Each attribute in this syntax is only allowed to take one of a set of values, which are listed in the CMIP6 `controlled vocabulary <https://github.com/WCRP-CMIP/CMIP6_CVs>`__ data. The data search may be filtered by requiring these attributes to take a specific value (ranges of values are not supported), via the following flags:

**Command-line options**

--activity-id <activity_id>    Optional. If given, restricts the search to data published in connection with a specific Model Intercomparison Project (MIP). By default, all available MIPs (consistent with the other settings) are considered.
--institution-id <institution_id>    Optional. If given, restricts the search to data published by a specific institution.
-m, --model, --source-id <source_id>    Optional. If given, restricts the search to data produced by a specific source, i.e. climate model.
-e, --experiment, --experiment-id <experiment_id>    Optional. If given, restricts the search to data produced for the given experiment.
--variant-label <r?i?p?f?>    Optional. If specified, restricts the search to data with the given combinations of realization index (``r``), initialization index (``i``), physics index (``i``) and forcing index (``f``). Note that the meaning of these indices may differ between institutions and MIPs. Filtering the search on each index individually is not currently implemented.
--grid-label <grid_label>    Optional. If specified, restricts the search to data marked with the given grid label (of the form `gn`, `gr1`, `gr2`, ...). Note that the meaning of these labels may differ between institutions and MIPs. 
--version-date <YYYYMMDD>    Optional. If specified, restricts the search to data published with a given revision date.

<*CASE_ROOT_DIR*> is taken to be the root of the directory hierarchy in the data reference syntax. Arbitrary strings may be used in subdirectories of that hierarchy, and for the above flag values: this data source doesn't enforce the CMIP6 controlled vocabulary. This can be useful for, e.g., analyzing data that's not intended to be published as part of CMIP6 but was processed with CMIP tools out of convenience.

The user setting for ``-c``/``--convention`` is ignored by this data source; ``CMIP`` conventions are always used.

It is not necessary to explicitly specify each of the above flags in order to select a desired set of data, due to the use of heuristics described below:

**Data selection heuristics**

This data source implements the following logic to guarantee that all data it provides to the PODs are consistent, i.e. that the variables selected have been generated from the same run of the same model. An error will be raised if no set of variables can be found that satisfy the user's settings (described above) and the following requirements:

* The <*activity_id*>, <*institution_id*>, <*source_id*>, <*experiment_id*>, <*variant_label*> and <*version_date*> for all variables requested by all PODs must be identical.
  
  - If multiple realization, initialization, etc. indices in the <*variant_label*> satisfy this requirement, the lowest-numbered indices are chosen.
  - If multiple <*version_date*>\s satisfy this requirement, the most recent one is chosen.
  - If multiple values of the other attributes satisfy this requirement, an error is raised. 
  
  In practice, this means that in the majority of cases, the user only needs to specify the <*source_id*> (model) and <*experiment_id*> (experiment) to uniquely identify the dataset they want to analyze. 

* The <*grid_label*> must be the same for all variables requested by a POD, but can be different for different PODs. The same value will be chosen for all PODs if possible. 

  - If multiple choices of <*grid_label*> satisfy this requirement, we prefer regridded to natively-gridded (*gn*) data, and select the lowest-numbered regridding.

* Variables that don't have global coverage (e.g., are restricted to the Greenland or Antarctic regions) or are zonally or otherwise spatially averaged are excluded from the search, as no POD is currently designed to use these types of data.

.. _ref-data-source-nopp:

No preprocessor
++++++++++++++++++++++++++++
.. Important:: The ``No_pp`` data source is a development feature intended to simplify POD debugging. Finalized PODs must function with preprocessor enabled in the framework.

Selected via ``--data-manager="No_pp"``.

This datasource bypasses the preprocessor entirely.  Model input data must adhere to the `Local_File` naming convention
``<CASENAME>.<frequency>.<variable name>.nc`` and be located in the directory
``[Input directory root]/[CASENAME]/[output frequency]``. If ``data_type=single_run``, files in the input data directories
are symbolically linked to the working directory. If ``data_type=multi_run``, the data file paths point directly to the
input data location because symbolic linking breaks the framework. Thus, for the ``multi_run`` configuration, the `index.html`
file generated in the POD output directory will not work. However, the `[POD_NAME].html` file in the POD output directory
will properly display the output.

Data must have the variable names, units, convention, and dimensionality specified in the POD settings file.
Users can use the :ref:`rename_input_files.py<ref-rename-input-files>` tool to create copies of files in the Local_file format

The ``No_pp`` data source differs from passing the ``--disable-preprocessor`` option, which still renames variables
to match the desired convention, crops the date range to match the ``FIRSTYR``  and ``LASTYR specified
in the runtime configuration file, and writes copies of the modified files to the working directory.



