Data source configuration reference
===================================

This section details how to select the input model data for the package to analyze. The main command-line option for this functionality is the ``--data-manager`` flag, which selects a ":ref:`data source<ref-data-sources>`": a code plug-in that implements the functionality of querying and fetching data from a remote host. The plug-in may define its own specific command-line options, which are documented here. 

If you're using site-specific functionality (via the ``--site`` flag), additional options for the ``--data-manager`` flag may be available. See the :doc:`site-specific documentation<site_toc>` for your site.

The choice of data source determines where and how the data needed by the diagnostics is obtained, but doesn't specify anything about the data's contents. For that purpose we allow the user to specify a "variable naming :ref:`convention<ref-data-conventions>`" with the ``--convention`` flag. 

.. _ref-data-sources:

Model data sources
------------------

By "data source," we mean a code plug-in for the package that provides all functionality needed to obtain model data needed by the PODs, based on user input:

* An interface to query the remote store of data for the variables requested by the PODs, whether in the form of an organized data catalog/database or in file naming conventions;
* (Optional) heuristics for refining the query results in order to guarantee that all data selected came from the same experiment;
* The data transfer protocol to use for transferring the selected data to a local filesystem, for processing by the framework and by the PODs.

There are currently two data sources implemented in the package, described below. If you would like the package to support obtaining data from a source that hasn't currently been implemented, please make a request in the appropriate GitHub `discussion thread <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/175>`__.

.. _ref-data-source-localfile:

Sample model data source
++++++++++++++++++++++++

Selected via ``--data-manager="LocalFile"``. This is the default value for <*data-manager*>.

This data source lets the package run on the sample model data provided with the package and installed by the user at <*OBS_DATA_ROOT*>. Any additional data added by the user to this location (either by copying files, or through symlinks) will also be recognized, provided that it takes the form of one netCDF file per variable and that it follows the following naming convention for subdirectories and file names:

<*OBS_DATA_ROOT*>/<*dataset_name*>/<*frequency*>/<*dataset_name*>.<*variable_name*>.<*frequency*>.nc,

where

* <*dataset_name*> is any string uniquely identifying the dataset,
* <*frequency*> is a string describing the frequency at which the data is sampled (``6hr``, ``day``, ``mon``, etc.), and
* <*variable_name*> is the name of the variable according to one of the recognized :ref:`naming conventions<ref-data-conventions>`.

At runtime, the user selects which dataset to use with the following flag:

**Command-line options**

* ``-e``, ``--experiment``, ``--sample-dataset`` <*dataset_name*>: Name of the sample dataset to use. This should correspond to the name of one of the subdirectories in the <*OBS_DATA_ROOT*>. The user is responsible for manually downloading the sample datasets of interest to them; for instructions, see :ref:`ref-supporting-data`.

  Optional; if not given, this attribute is set from <*CASENAME*> (for backwards compatibility reasons).

* ``-c``/``--convention`` should be set when using this data source. If not given, it defaults to ``CMIP`` (see below).

.. _ref-data-source-cmip6:

CMIP6 local file data source
++++++++++++++++++++++++++++

Selected via ``--data-manager="CMIP6"``.

This data source searches for model data stored as netCDF files on a locally-mounted filesystem, in a structured directory hierarchy with directories and files named following the CMIP6 `data reference syntax <https://goo.gl/v1drZl>`__ (DRS). Each attribute in this syntax is only allowed to take one of a set of values, which are listed in the CMIP6 `controlled vocabulary <https://github.com/WCRP-CMIP/CMIP6_CVs>`__ data. The data search may be filtered by requiring these attributes to take a specific value (ranges of values are not supported), via the following flags:

**Command-line options**

* ``--activity-id`` <*activity_id*>: Optional. If given, restricts the search to data published in connection with a specific Model Intercomparison Project (MIP). By default, all available MIPs (consistent with the other settings) are considered.
* ``--institution-id`` <*institution_id*>: Optional. If given, restricts the search to data published by a specific institution.
* ``-m``, ``--model``, ``--source-id`` <*source_id*>: Optional. If given, restricts the search to data produced by a specific "source," i.e. climate model.
* ``-e``, ``--experiment``, ``--experiment-id`` <*experiment_id*>: Optional. If given, restricts the search to data produced for the given experiment.
* ``--variant-label`` <*r\?i\?p\?f\?*>: Optional. If specified, restricts the search to data with the given combinations of realization index (``r``), initialization index (``i``), physics index (``i``) and forcing index (``f``). Note that the meaning of these indices may differ between institutions and MIPs. Filtering the search on each index individually is not currently implemented.
* ``--grid-label`` <*grid_label*>: Optional. If specified, restricts the search to data marked with the given grid label (of the form `gn`, `gr1`, `gr2`, ...). Note that the meaning of these labels may differ between institutions and MIPs. 
* ``--version-date`` <*YYYYMMDD*>: Optional. If specified, restricts the search to data published with a given revision date.
* The user setting for ``-c``/``--convention`` is ignored by this data source; ``CMIP`` conventions are always used.

In practice, it is not necessary to explicitly specify each of these attributes in order to select a desired set of data, as described below:

**Data selection heuristics**

This data source implements the following logic to guarantee that all data it provides to the PODs are consistent, i.e. that the variables selected have been generated from the same run of the same model. An error will be raised if no set of variables can be found that satisfy the user's input above and the following requirements:

* The <*activity_id*>, <*institution_id*>, <*source_id*>, <*experiment_id*>, <*variant_label*> and <*version_date*> for all variables requested by all PODs must be identical.
  
  - If multiple realization, initialization, etc. indices in the <*variant_label*> satisfy this requirement, the lowest-numbered indices are chosen.
  - If multiple <*version_date*>s satisfy this requirement, the most recent one is chosen.
  - If multiple values of the other attributes satisfy this requirement, an error is raised. In practice, this means that in the majority of cases, the user only needs to specify the <*source_id*> (model) and <*experiment_id*> (experiment) to uniquely identify the data. 

* The <*grid_label*> must be the same for all variables requested by a POD, but can be different for different PODs. The same value will be chosen for all PODs if possible. 

  - If multiple choices of <*grid_label*> satisfy this requirement, we prefer regridded to natively-gridded (``gn``) data, and select the lowest-numbered regridding.

* Variables that don't have global coverage (e.g., are restricted to the Greenland or Antarctic regions) or are zonally or otherwise spatially averaged are excluded from the search, as no POD is currently designed to use these types of data.


.. _ref-data-conventions:

Conventions for variable names and units
----------------------------------------

The use of data source plug-ins, as described above, is how we let the package obtain data files by different methods, but doesn't address problems arising from differing content of these files. For example, the name for total precipitation used by NCAR models is ``PRECT`` and is given as a rate (meters per second), while the name for the same physical quantity in GFDL models is ``precip``, given in units of a flux (kg m\ :sup:`-2`\  s\ :sup:`-1`\ ).

Frequently a data source (in the sense described above) will only identify a variable through this "native" name, which makes it necessary to tell the package which "language to speak" when searching for different variables. Setting the ``--convention`` flag translates the data request for each POD into the naming convention used by the model that's being analyzed. 

Before any PODs are run, the framework examines each file and converts the name and units of each variable to the values that the POD expects. This feature also provides a mechanism to deal with missing metadata, and to warn the user that the metadata for a specific file may be inaccurate. 

Naming conventions are specified with the ``--convention`` flag. The currently implemented naming conventions are:

* ``CMIP``: Variable names and units as used in the `CMIP6 <https://www.wcrp-climate.org/wgcm-cmip/wgcm-cmip6>`__ `data request <https://doi.org/10.5194/gmd-2019-219>`__. There is a `web interface <http://clipc-services.ceda.ac.uk/dreq/index.html>`__ to the request. Data from any model that has been `published <https://esgf-node.llnl.gov/projects/cmip6/>`__ as part of CMIP6, or processed with the `CMOR3 <https://cmor.llnl.gov/>`__ tool, should follow this convention.

* ``NCAR``: Variable names and units used in the default output of models developed at the `National Center for Atmospheric Research <https://ncar.ucar.edu>`__ (NCAR), headquartered in Boulder, CO, USA. Recognized synonyms for this convention: ``CAM4``, ``CESM``, ``CESM2``.

* ``GFDL``: Variable names and units used in the default output of models developed at the `Geophysical Fluid Dynamics Laboratory <https://www.gfdl.noaa.gov/>`__ (GFDL), Princeton, NJ, USA. Recognized synonyms for this convention: ``AM4``, ``CM4``, ``ESM4``, ``SPEAR``.

If you would like the package to support a naming convention that hasn't currently been implemented, please make a request in the appropriate GitHub `discussion thread <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/174>`__.
