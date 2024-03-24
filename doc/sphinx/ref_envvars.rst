MDTF Environment variables
==========================

This page describes the environment variables that the framework will set for your diagnostic when it's run. 

Overview
--------

The MDTF framework can be viewed as a "wrapper" for your code that handles data fetching and munging.
Your code communicates with this wrapper in two ways:

- The :doc:`settings file <./pod_settings>` is where your code talks to the framework: when you write your code,
  you document what model data your code uses (not covered on this page, follow the link for details).
- The framework "talks" to a POD through a combination of shell environment variables passed directly to the subprocess
  via the `env` parameter, and by defining a `case_info.yml` file in the case workdir with case-specific environment
  variables.The framework communicates **all** runtime information this way: this is in order to 1) pass information
  in a language-independent way, and 2) to make writing diagnostics easier (i.e., the POD does not need to parse
  command-line settings).

**Note** that environment variables are always strings. Your POD will need to cast non-text data to the
appropriate type (e.g. the bounds of a case analysis time period, ``startdate``, ``enddate``, will need to be converted
to integers.)

Also note that names of environment variables are case-sensitive.

Paths
-----

``OBS_DATA``: 
  Path to the top-level directory containing any observational or reference data you've provided as the author of your
  diagnostic. Any data your diagnostic uses that doesn't come from the model being analyzed should go here
  (i.e., you supply it to the framework maintainers, they host it, and the user downloads it when they install the
  framework). The framework will ensure this is copied to a local filesystem when your diagnostic is run, but this
  directory should be treated as **read-only**.

``POD_HOME``: 
  Path to the top-level directory containing your diagnostic's source code. This will be of the form
  ``.../MDTF-diagnostics/diagnostics/<your POD's name>``. This can be used to call sub-scripts from your diagnostic's
  driver script. This directory should be treated as **read-only**.

``WORK_DIR``:
  Path to your diagnostic's *working directory*, which is where all output data should be written
  (as well as any temporary files).

  The framework creates the following subdirectories within this directory:

  - ``$WORK_DIR/obs/PS`` and ``$WORK_DIR/model/PS``: All output plots produced by your diagnostic should be written to
    one of these two directories. Only files in these locations will be converted to bitmaps for HTML output.
  - ``$WORK_DIR/obs/netCDF`` and ``$WORK_DIR/model/netCDF``: Any output data files your diagnostic wants to make
    available to the user should be saved to one of these two directories.

Model run information
---------------------

``CASENAME``: 
  User-provided label describing the run of model data being analyzed.

``startdate``, ``enddate``:
  Four-digit years describing the analysis period.


Locations of model data files
-----------------------------

These are set depending on the data your diagnostic requests in its :doc:`settings file <./pod_settings>`. Refer to the
examples below if you're unfamiliar with how that file is organized.

Each variable listed in the ``varlist`` section of the settings file must specify a ``path_variable`` property.
The value you enter there will be used as the name of an environment variable, and the framework will set the value
of that environment variable to the absolute path to the file containing data for that variable.

**From a diagnostic writer's point of view**, this means all you need to do here is replace paths to input data that
are hard-coded or passed from the command line with calls to read the value of the corresponding environment variable.

- If the framework was not able to obtain the variable from the data source (at the requested frequency, etc.,
  for the user-specified analysis period), this variable will be set equal to the **empty string**. Your diagnostic is
  responsible for testing for this possibility for all variables that are listed as ``optional`` or have alternates
  listed (if a required variable without alternates isn't found, your diagnostic won't be run.)
- If ``multi_file_ok`` is set to ``true`` in the settings file, this environment variable may be a list of paths to
  *multiple* files in chronological order, separated by colons. For example,
  ``/dir/precip_1980_1989.nc:/dir/precip_1990_1999.nc:/dir/precip_2000_2009.nc`` for an analysis period of 1980-2009.

Names of variables and dimensions
---------------------------------

These are set depending on the data your diagnostic requests in its :doc:`settings file <./pod_settings>`. Refer to
the examples below if you're unfamiliar with how that file is organized.

*For each dimension:*
  If <key> is the name of the key labeling the key:value entry for this dimension, the framework will set an environment
  variable named ``<key>_coord`` equal to the name that dimension has in the data files it's providing.
  
    - If ``rename_dimensions`` is set to ``true`` in the settings file, this will always be equal to <key>. If
    ``rename_dimensions`` is ``false``, this will be whatever the model or data source's native name for this dimension
    is, and your diagnostic should read the name from this variable. Your diagnostic should **only** use hard-coded
    names for dimensions if ``rename_dimensions`` is set to ``true`` in its :doc:`settings file <ref_settings>`.

  If the data source has provided (one-dimensional) bounds for this dimension, the name of the netCDF variable containing those bounds will be set in an environment variable named ``<key>_bnds``. If bounds are not provided, this will be set to the empty string. **Note** that multidimensional boundaries (e.g. for horizontal cells) should be listed as separate entries in the varlist section.

*For each variable:*
  If <key> be the name of the key labeling the key:value entry for this variable in the varlist section, the framework will set an environment variable named ``<key>_var`` equal to the name that variable has in the data files it's providing.
  
    - If ``rename_variables`` is set to ``true`` in the settings file, this will always be equal to <key>. If ``rename_variables`` is ``false``, this will be whatever the model or data source's native name for this variable is, and your diagnostic should read the name from this variable. Your diagnostic should **only** use hard-coded names for variables if ``rename_variables`` is set to ``true`` in its :doc:`settings file <ref_settings>`.


Simple example
--------------

We only give the relevant parts of the :doc:`settings file <ref_settings>` below.

.. code-block:: js

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


The framework will set the following environment variables:

#. ``lat_coord``: Name of the latitude dimension in the model's native format (because ``rename_dimensions`` is false).
#. ``lon_coord``: Name of the longitude dimension in the model's native format (because ``rename_dimensions`` is false).
#. ``time_coord``: Name of the time dimension in the model's native format (because ``rename_dimensions`` is false).
#. ``pr_var``: Name of the precipitation variable in the model's native format (because ``rename_variables`` is false).
#. ``PR_FILE``: Absolute path to the file containing ``pr`` data, e.g. ``/dir/precip.nc``.


More complex example
--------------------

Let's elaborate on the previous example, and assume that the diagnostic is being called on model that provides precipitation_flux but not convective_precipitation_flux.

.. code-block:: js

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


Comparing this with the previous example:

- ``lat_coord``, ``lon_coord`` and ``time_coord`` will be set to "lat", "lon" and "time", respectively, because ``rename_dimensions`` is true. The framework will have renamed these dimensions to have these names in all data files provided to the diagnostic.
- ``prc_var`` and ``pr_var`` will be set to the model's native names for these variables. Names for all variables are always set, regardless of which variables are available from the data source.
- In this example, ``PRC_FILE`` will be set to ``''``, the empty string, because it wasn't found. 
- ``PR_FILE`` will be set to ``/dir/precip_1980_1989.nc:/dir/precip_1990_1999.nc:/dir/precip_2000_2009.nc``, because ``multi_file_ok`` was set to ``true``.
