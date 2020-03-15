Diagnostic settings file format
===============================

The settings file is how your diagnostic tells the framework what it needs to run, in terms of software and model data. 

Each diagnostic must contain a text file named ``settings.jsonc`` in the `JSON <https://en.wikipedia.org/wiki/JSON#Data_types_and_syntax>`_ format, with the addition that comments are 

Brief summary of JSON
---------------------

We'll briefly summarize subset of JSON syntax used in this configuration file. The file's JSON expressions are built up out of *items*, which may be either 

1. a boolean, taking one of the values ``true`` or ``false`` (lower-case, with no quotes).
2. a number (integer or floating-point).
3. a case-sensitive string, which must be delimited by double quotes.

In addition, for the purposes of the configuration file we define 

.. _unitful:

4. a "unit-ful quantity": this is a string containing a number followed by a unit, eg. ``"6hr"``. **In addition**, the string ``"any"`` may be used to signify that any value is acceptable.

Items are combined in compound expressions of two types: 

.. _array:

5. *arrays*, which are one-dimensional ordered lists delimited with square brackets. Entries can be of any type, eg ``[true, 1, "two"]``.

.. _object:

6. *objects*, which are *un*-ordered lists of key:value pairs separated by colons and delimited with curly brackets. Keys must be strings and must all be unique within the object, while values may be any expression, eg. ``{"red": 0, "green": false, "blue": "bagels"}``.

Compound expressions may be nested within each other to an arbitrary depth.

Settings section
----------------

This section is an :ref:`object<object>` containing properties that label the diagnostic and describe its runtime requirements.

Example
^^^^^^^

.. code-block:: jsonc

  "settings" : {
    "long_name" : "Effect of X and Y on Z diagnostic ",
    "driver" : "my_script.py",
    "realm" : ["atmos", "ocean"],
    "runtime_requirements": {
      "python": ["numpy", "matplotlib", "netCDF4", "cartopy"],
      "ncl": ["contributed", "gsn_code", "gsn_csm"]
    },
    "pod_env_vars" : {
      // RES: Spatial Resolution (degree) for Obs Data (0.25, 0.50, 1.00).
      "RES": "1.00"
    }
  }

::

Diagnostic description
^^^^^^^^^^^^^^^^^^^^^^

``long_name``: 
  String, **required**. Human-readable display name of your diagnostic. This is the text used to describe your diagnostic on the top-level index.html page. It should be in sentence case (capitalize first word and proper nouns only) and omit any punctuation at the end.

``driver``: 
  String, **required**. Filename of the top-level driver script the framework should call to run your diagnostic's analysis.

``realm``: 
  String or :ref:`array<array>` of strings, **required**. One of the eight CMIP6 modeling `realms <https://github.com/PCMDI/cmip6-cmor-tables/blob/3b802b4e94fc36c5c9d1c9234fcace7d81f769c3/Tables/CMIP6_CV.json#L2411>`_ describing what data your diagnostic uses. If your diagnostic uses data from multiple realms, list them in an array (eg. ``["atmos", "ocean"]``). This information doesn't affect how the framework fetches model data for your diagnostic: it's provided to give the user a shortcut to say, eg., "run all the atmos diagnosics on this output."

Diagnostic runtime
^^^^^^^^^^^^^^^^^^

``runtime_requirements``: 
  :ref:`object<object>`, **required**. Programs your diagnostic needs to run (for example, scripting language interpreters) and any third-party libraries needed in those languages. Each executable should be listed in a separate key: value pair:

  - The ``key`` is the name of the required executable, eg. languages such as "`python <https://www.python.org/>`_" or "`ncl <https://www.ncl.ucar.edu/>`_" etc. but also any utilities such as "`ncks <http://nco.sourceforge.net/>`_", "`cdo <https://code.mpimet.mpg.de/projects/cdo>`_", etc.
  - The ``value`` corresponding to each ``key`` is an :ref:`array<array>` of strings, which are names of third-party libraries in that language that your diagnostic needs. You do *not* need to list standard libraries or scripts that are provided in a standard installation of your language: eg, in python, you need to list `numpy <https://numpy.org/>`_ but not `math <https://docs.python.org/3/library/math.html>`_. If no third-party libraries are needed, the ``value`` should be an empty list.

  In the future we plan to offer the capability to request specific `versions <https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/pkg-specs.html#package-match-specifications>`_. For now, please communicate your diagnostic's version requirements to the MDTF organizers.

``pod_env_vars``: 
  :ref:`object<object>`, optional. Names and values of shell environment variables used by your diagnostic, *in addition* to those supplied by the framework. The user can't change these at runtime, but this can be used to set site-specific installation settings for your diagnostic (eg, switching between low- and high-resolution observational data depending on what the user has chosen to download). Note that environment variable values must be provided as strings.

Data section
------------

This section is an :ref:`object<object>` containing properties that apply to all data files.

Example
^^^^^^^

.. code-block:: json

  "data": {
    "format": "netcdf4_classic",
    "rename_dimensions": false,
    "rename_variables": false,
    "multi_file_ok": true,
    "frequency": "3hr",
    "min_frequency": "1hr",
    "max_frequency": "6hr",
    "min_duration": "5yr",
    "max_duration": "any"
  }

::

Example
^^^^^^^

``format``:
  String. Optional: assumed ``"any_netcdf_classic"`` if not specified. Specifies the format(s) of *model* data your diagnostic is able to read. As of this writing, the framework only supports retrieval of netCDF formats, so only the following values are allowed: 

  - ``"any_netcdf"`` includes all of:

    - ``"any_netcdf3"`` includes all of:

      - ``"netcdf3_classic"`` (CDF-1, files restricted to < 2 Gb)
      - ``"netcdf3_64bit_offset"`` (CDF-2)
      - ``"netcdf3_64bit_data"`` (CDF-5)

    - ``"any_netcdf4"`` includes all of:

      - ``"netcdf4_classic"``
      - ``"netcdf4"``

  - ``"any_netcdf_classic"`` includes all the above *except* ``"netcdf4"`` (classic data model only).

  See the `netCDF FAQ <https://www.unidata.ucar.edu/software/netcdf/docs/faq.html>`_ (under "Formats, Data Models, and Software Releases") for information on the distinctions. Any recent version of a supported language for diagnostics with netCDF support will be able to read all of these. However, the extended features of the ``"netcdf4"`` data model are not commonly used in practice and currently only supported at a beta level in NCL, which is why we've chosen ``"any_netcdf_classic"`` as the default.


``rename_dimensions``:
  Boolean. Optional: assumed ``false`` if not specified. If set to ``true``, the framework will change the name of all :ref:`dimensions<sec_dimensions>` in the model data from the model's native value to the string specified in the ``name`` property for that dimension. If set to ``false``, **the diagnostic is responsible for reading dimension names from the environment variable**.

``rename_variables``: 
  Boolean. Optional: assumed ``false`` if not specified. If set to ``true``, the framework will change the name of all :ref:`variables<sec_varlist>` in the model data from the model's native value to the string specified in the ``name`` property for that variable. If set to ``false``, **the diagnostic is responsible for reading dimension names from the environment variable**.

.. _multi_file:

``multi_file_ok``: 
  Boolean. Optional: assumed ``false`` if not specified. If set to ``true``, the diagnostic can handle datasets for a single variable spread across multiple files, eg `xarray <http://xarray.pydata.org/en/stable/generated/xarray.open_mfdataset.html>`_. 

``min_duration``, ``max_duration``: 
  :ref:`Unit-ful quantities<unitful>`. Optional: assumed ``"any"`` if not specified. Set minimum and maximum length of the analysis period for which the diagnostic should be run. For example, if your diagnostic uses seasonal data, On the other hand, if your diagnostic uses hourly data, 

The following properties can optionally be set individually for each variable in the varlist :ref:`section<sec_varlist>`. If so, they will override the global settings given here.

``dimensions_ordered``: 
  Boolean. Optional: assumed ``false`` if not specified. If set to ``true``, the framework will ensure that the dimensions of each variable's array are given in the same order as listed in ``dimensions``. **If set to false, your diagnostic is responsible for handling arbitrary dimension orders**: eg. it should *not* assume that 3D data will be presented as (time, lat, lon).

.. _freq_target:

``frequency``, ``min_frequency``, ``max_frequency``: 
  :ref:`Unit-ful quantities<unitful>`. Time frequency at which the data is provided. Either ``frequency`` or the min/max pair, or both, is required:

  - If only ``frequency`` is provided, the framework will attempt to obtain data at that frequency. If that's not available from the data source, your diagnostic will not run. 
  - If the min/max pair is provided, the diagnostic must be capable of using data at any frequency within that range (inclusive). **The diagnostic is responsible for determining the frequency** if this option is used.
  - If all three properties are set, the framework will first attempt to find data at ``frequency``. If that's not available, it will try data within the min/max range, so your code must be able to handle this possibility.

.. _sec_dimensions:

Dimensions section
------------------

This section is an :ref:`object<object>` contains properties that apply to the dimensions of model data. 

Example
^^^^^^^

.. code-block:: json

  "dimensions": {
    "latitude": {
        "name": "lat",
        "units": "degrees_N",
        "range": [-90, 90],
        "need_bounds": false
    },
    "longitude": {
        "name": "lon",
        "units": "degrees_E",
        "range": [-180, 180],
        "need_bounds": false
    },
    "pressure": {
        "name": "plev",
        "units": "hPa",
        "positive": "up",
        "need_bounds": false
    },
    "time": {
        "name": "time",
        "units": "days",
        "calendar": "noleap",
        "need_bounds": false
    }
  }

::

Latitude and Longitude
^^^^^^^^^^^^^^^^^^^^^^

``name``: 
  **Required**, string. 

``units``: 
  **Required**. String, following syntax of the `UDUnits library <https://www.unidata.ucar.edu/software/udunits/udunits-2.0.4/udunits2lib.html#Syntax>`_. Units the diagnostic expects the dimension to be in.

``range``: 
  Optional. List of :

``need_bounds``: 
  Optional. Boolean:

Time
^^^^

``name``: 
  **Required**. 

``units``: 
  **Required**. String, following syntax of the `UDUnits library <https://www.unidata.ucar.edu/software/udunits/udunits-2.0.4/udunits2lib.html#Syntax>`_. Units the diagnostic expects the dimension to be in.

``calendar``: 
  String, Optional. One of the CF convention `calendars <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#calendar>`_ or the string ``"any"``. **Defaults to "any" if not given**.

- ``need_bounds``: Optional. Boolean:

Z axis (height/depth, pressure, ...)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``name``: 
  **Required**. 

``units``: 
  **Required**. String, following syntax of the `UDUnits library <https://www.unidata.ucar.edu/software/udunits/udunits-2.0.4/udunits2lib.html#Syntax>`_. Units the diagnostic expects the dimension to be in.

``positive``: 
  Optional.

``need_bounds``: 
  Optional. Boolean:

Other dimensions (wavelength, ...)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``name``: 
  **Required**. 

``units``: 
  **Required**. String, following syntax of the `UDUnits library <https://www.unidata.ucar.edu/software/udunits/udunits-2.0.4/udunits2lib.html#Syntax>`_. Units the diagnostic expects the dimension to be in.

.. _sec_varlist:

Varlist section
---------------

This section contains properties that describe the individual variables your diagnostic operates on. 

Varlist entry example
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

  "u500": {
      "standard_name": "eastward_wind",
      "path_variable": "U500_FILE",
      "units": "m s-1",
      "dimensions" : ["time", "latitude", "longitude"],
      "dimensions_ordered": true,
      "scalar_coordinates": {"pressure": 500},
      "requirement": "optional",
      "alternates": ["foo", "bar"]
  }

::

Varlist entry properties
^^^^^^^^^^^^^^^^^^^^^^^^

Keys are the names of variables used internally by the diagnostic (and must be unique).

The following properties are set on a per-variable basis by 

``standard_name``: 
  String, **required**. `Standard name <http://cfconventions.org/Data/cf-standard-names/72/build/cf-standard-name-table.html>`_ of the variable as defined by the `CF conventions <http://cfconventions.org/>`_, or a commonly used synonym as employed in the CMIP6 MIP tables (eg. "ua" instead of "eastward_wind"). 

``path_variable``: 
  String, **required**. Name of the shell environment variable the framework will set with the location of this data. Specifically, the framework sets *two* environment variables:

  - If ``multi_file_ok`` is ``false``, both ``<path_variable>`` and ``<path_variable>_FILES`` will be set to the absolute path to the single data file containing the variable.
  - If ``multi_file_ok`` is ``true``, 

    - ``<path_variable>`` will be the absolute path to a *directory* containing all the variable's files.
    - ``<path_variable>_FILES`` will contain a space-delimited list of file *names* within that directory, in the order in which they need to be joined to put the data in chronological sequence.

``use_exact_name``:
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ignore the model's naming conventions and only find data with a variable name that 
  The main use case for this setting is to give diagnostics the ability to request data that falls outside the CF conventions. 

``units``: 
  Optional. String, following syntax of the `UDUnits library <https://www.unidata.ucar.edu/software/udunits/udunits-2.0.4/udunits2lib.html#Syntax>`_. Units the diagnostic expects the variable to be in. **If not provided, the framework will assume CF convention**  `canonical units <http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>`_.

``dimensions``:
  **Required**. List of strings, which must be selected from either the keys or ``name`` properties of entries in the :ref:`dimensions<sec_dimensions>` section. Dimensions of the array containing the variable's data. **Note** that the framework will not reorder dimensions unless ``dimensions_ordered`` is additionally set to ``true``.

``dimensions_ordered``: 
  Optional, boolean. If ``true``, the framework will ensure that the dimensions of this variable's array are given in the same order as listed in ``dimensions``. **If set to false, your diagnostic is responsible for handling arbitrary dimension orders**: eg. it should *not* assume that 3D data will be presented as (time, lat, lon).

``scalar_coordinates``: 
  :ref:`object<object>`, optional. This implements what the CF conventions refer to as "`scalar coordinates <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`_", with the use case here being the ability to request slices of higher-dimensional data. 

  - *keys* are the key or ``name`` property of an entry in the :ref:`dimensions<sec_dimensions>` section.
  - *values* are a single number (integer or floating-point) corresponding to the value of the slice to extract. **Units** of this number are taken to be the ``units`` property of the dimension named as the key.

  In order to request multiple slices (eg. wind velocity on multiple pressure levels), create one varlist entry per slice.

``frequency``, ``min_frequency``, ``max_frequency``: 
  :ref:`Unit-ful quantities<unitful>`. Optional. Time frequency at which the variable's data is provided. If given, overrides the values set globally in the ``data`` section (see :ref:`description<freq_target>` there).

``requirement``: 
  String. Optional: assumed ``"required"`` if not specified. One of three values:

  - ``"required"``: variable is necessary for the diagnostic's calculations. If the data source doesn't provide the variable (at the requested frequency, etc., for the user-specified analysis period) the framework will *not* run the diagnostic, but will instead log an error message explaining that the lack of this data was at fault.
  - ``"optional"``: variable will be supplied to the diagnostic if provided by the data source. If not available, the diagnostic will still run, and the ``path_variable`` for this variable will be set to the empty string. **The diagnostic is responsible for testing the environment variable** for the existence of all optional variables.
  - ``"alternate"``: variable is specified as an alternate source of data for some other variable (see next property). The framework will only query the data source for this variable if it's unable to obtain one of the *other* variables that list it as an alternate.

``alternates``: 
  Optional. List of strings which are the keys labeling other variables in the varlist. If provided, specifies an alternative method for obtaining needed data if this variable isn't provided by the data source. 
  
  - If the data source provides this variable (at the requested frequency, etc., for the user-specified analysis period), this property is ignored.
  - If this variable isn't available as requested, the framework will query the data source for all of the variables listed in this property. If *all* of the alternate variables are available, the diagnsotic will be run; if any are missing it will be skipped. Note that, as currently implemented, only one set of alternates may be given (no "plan B", "plan C", etc.)
