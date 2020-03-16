MDTF Environment variables
==========================

The framework communicates **all** runtime information to your diagnostic via shell `environment variables <https://en.wikipedia.org/wiki/Environment_variable>`_. We do this in order to 1) pass this information in a language-independent way, and 2) to make writing diagnostics easier (you don't need to parse command-line settings). 

**Note** that environment variables are always strings. Your script will need to cast non-text data to the appropriate type (eg. the bounds of the analysis time period, ``FIRSTYR``, ``LASTYR``, will need to be converted to integers.)

Also note that names of environment variables are case-sensitive.

Paths
-----

``OBS_DATA``: 
  Path to the top-level directory containing any observational or reference data you provide as the POD's author. The framework will ensure this is copied to a local filesystem when your diagnostic is run, but this directory should be treated as **read-only**.

``POD_HOME``: 
  Path to the top-level directory containing your diagnostic's source code (of the form ``.../MDTF-diagnostics/diagnostics/<your POD's name>``). This can be used to call sub-scripts from your diagnostic's driver script. This directory should be treated as **read-only**.

``WK_DIR``: 
  Path to your diagnostic's *working directory*, which is where any temporary files and output data should be created. 

  The framework creates the following subdirectories within this directory:

  - ``$WK_DIR/obs/PS`` and ``$WK_DIR/model/PS``: All output plots produced by your diagnostic should be written to one of these two directories. Only files in these locations will be converted to bitmaps for HTML output.
  - ``$WK_DIR/obs/netCDF`` and ``$WK_DIR/model/netCDF``: Any output data files your diagnostic wants to make available to the user should be saved to one of these two directories.


Model run information
---------------------

``CASENAME``: 
  User-provided label describing the run of model data being analyzed.

``FIRSTYR``, ``LASTYR``: 
  Four-digit years describing the analysis period.

Variables and Dimensions
------------------------

These are set depending on the data your diagnostic requests in its settings file.


For each dimension:
  Let <key> be the name of the key labeling the key:value entry for this dimension. Then

  - ``<key>_dim`` is set equal to the name of the dimension in the model data. 
  
    - If ``rename_dimensions`` is set to ``true`` in the settings file, this will always be equal to <key>. If If ``rename_dimensions`` is ``false``, this will be whatever the model or data source's native name for this dimension is, and your diagnostic should read the name from this variable. Your diagnostic should **only** use hard-coded names for dimensions if ``rename_dimensions`` is set to ``true`` in its :doc:`settings file <./dev_settings_format>`.

For each variable:
  Let <key> be the name of the key labeling the key:value entry for this variable in the varlist section, and let <path_variable> be the value of the ``path_variable`` property in the variable's entry. Then

  - ``<key>_var`` is set equal to the name of the variable in the model data. 
  
    - If ``rename_variables`` is set to ``true`` in the settings file, this will always be equal to <key>. If If ``rename_variables`` is ``false``, this will be whatever the model or data source's native name for this variable is, and your diagnostic should read the name from this variable. Your diagnostic should **only** use hard-coded names for dimensions if ``rename_dimensions`` is set to ``true`` in its :doc:`settings file <./dev_settings_format>`.

  - ``<path_variable>`` is set to the absolute path to the data file containing this variable.

    - If the framework was not able to obtain the variable from the data source (at the requested frequency, etc., for the user-specified analysis period), this variable will be set equal to the **empty string**. Your diagnostic is responsible for testing for this possibility for all variables that are listed as ``optional`` or have alternates listed.
    - If ``multi_file_ok`` is set to ``true`` in the settings file, this may be a list of paths to *multiple* files in chronological order, separated by colons. For example, ``/dir/precip_1980_1989.nc:/dir/precip_1990_1999.nc:/dir/precip_2000_2009.nc`` for the analysis period is 1980-2009.


Simple example
--------------

We only give the relevant parts of the :doc:`settings file <./dev_settings_format>` below.

.. code-block:: json

  "data": {
    "rename_dimensions": false,
    "rename_variables": false,
    "multi_file_ok": false,
    ...
  },
  "dimensions": {
    "lat": {
      "standard_name": "latitude",
      ...
    },
    "lon": {
      "standard_name": "longitude",
      ...
    },
    "time": {
      "standard_name": "time",
      ...
    }
  },
  "varlist": {
    "pr": {
      "standard_name": "precipitation_flux",
      "path_variable": "PR_FILE"
    }
  }

::

The framework will set the following environment variables:

#. ``lat_dim``: Name of the latitude dimension in the model's native format (because ``rename_dimensions`` is false).
#. ``lon_dim``: Name of the longitude dimension in the model's native format (because ``rename_dimensions`` is false).
#. ``time_dim``: Name of the time dimension in the model's native format (because ``rename_dimensions`` is false).
#. ``pr_var``: Name of the precipitation variable in the model's native format (because ``rename_variables`` is false).
#. ``PR_FILE``: Absolute path to the file containing ``pr`` data, eg. ``/dir/precip.nc``.


More complex example
--------------------

Let's elaborate on the previous example, and assume that the diagnostic is being called on model that provides precipitation_flux but not convective_precipitation_flux.

.. code-block:: json

  "data": {
    "rename_dimensions": true,
    "rename_variables": false,
    "multi_file_ok": true,
    ...
  },
  "dimensions": {
    "lat": {
      "standard_name": "latitude",
      ...
    },
    "lon": {
      "standard_name": "longitude",
      ...
    },
    "time": {
      "standard_name": "time",
      ...
    }
  },
  "varlist": {
    "prc": {
      "standard_name": "convective_precipitation_flux",
      "path_variable": "PRC_FILE",
      "alternates": ["pr"]
    },
    "pr": {
      "standard_name": "precipitation_flux",
      "path_variable": "PR_FILE"
    }
  }

::

Comparing this with the previous example:

- ``lat_dim``, ``lon_dim`` and ``time_dim`` will be set to "lat", "lon" and "time", respectively, because ``rename_dimensions`` is true. The framework will have renamed these dimensions to have these names in all data files provided to the diagnostic.
- ``prc_var`` and ``pr_var`` will be set to the model's native names for these variables. Names for all variables are always set, regardless of which variables are available from the data source.
- In this example, ``PRC_FILE`` will be set to ``''``, the empty string, because it wasn't found. 
- ``PR_FILE`` will be set to ``/dir/precip_1980_1989.nc:/dir/precip_1990_1999.nc:/dir/precip_2000_2009.nc``, because ``multi_file_ok`` was set to ``true``.
