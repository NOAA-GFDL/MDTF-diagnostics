Diagnostic settings file format
===============================

The settings file is how your diagnostic tells the framework what it needs to run, in terms of software and model data. 

Each diagnostic must contain a text file named ``settings.jsonc`` in the `JSON <https://en.wikipedia.org/wiki/JSON#Data_types_and_syntax>`__ format, with the addition that any text to the right of ``//`` is treated as a comment and ignored (sometimes called the "JSONC" format). 

Brief summary of JSON
---------------------

We'll briefly summarize subset of JSON syntax used in this configuration file. The file's JSON expressions are built up out of *items*, which may be either 

1. a boolean, taking one of the values ``true`` or ``false`` (lower-case, with no quotes).
2. a number (integer or floating-point).
3. a case-sensitive string, which must be delimited by double quotes.

In addition, for the purposes of the configuration file we define 

.. _time_duration:

4. a "time duration": this is a string specifying a time span, used e.g. to describe how frequently data is sampled. It consists of an optional integer (if omitted, the integer is assumed to be 1) and a units string which is one of ``hr``, ``day``, ``mon``, ``yr`` or ``fx``. ``fx`` is used where appropriate to denote time-independent data. Common synonyms for these units are also recognized (e.g. ``monthly``, ``month``, ``months``, ``mo`` for ``mon``, ``static`` for ``fx``, etc.)

   **In addition**, the string ``"any"`` may be used to signify that any value is acceptable.

.. _cfunit:

5. a "CF unit": this is a string describing the units of a physical quantity, following the `syntax <https://www.unidata.ucar.edu/software/udunits/udunits-2.0.4/udunits2lib.html#Syntax>`__ of the `UDUNITS2 <https://www.unidata.ucar.edu/software/udunits/udunits-current/doc/udunits/udunits2.html>`__ library. ``1`` should be used for dimensionless quantities.

Items are combined in compound expressions of two types: 

.. _array:

6. *arrays*, which are one-dimensional ordered lists delimited with square brackets. Entries can be of any type, e.g. ``[true, 1, "two"]``.

.. _object:

7. *objects*, which are *un*-ordered lists of key:value pairs separated by colons and delimited with curly brackets. Keys must be strings and must all be unique within the object, while values may be any expression, e.g. ``{"red": 0, "green": false, "blue": "bagels"}``.

Compound expressions may be nested within each other to an arbitrary depth.

File organization
-----------------

.. code-block:: js

  {
    "settings" : {
      <...properties describing the diagnostic..>
    },
    "data" : {
      <...properties for all requested model data...>
    },
    "dimensions" : {
      "my_first_dimension": {
        <...properties describing this dimension...>
      },
      "my_second_dimension": {
        <...properties describing this dimension...>
      },
      ...
    },
    "varlist" : {
      "my_first_variable": {
        <...properties describing this variable...>
      },
      "my_second_variable": {
        <...properties describing this variable...>
      },
      ...
    }
  }


At the top level, the settings file is an :ref:`object<object>` containing four required entries, described in detail below.

- :ref:`settings<sec_settings>`: properties that label the diagnostic and describe its runtime requirements.
- :ref:`data<sec_data>`: properties that apply to all the data your diagnostic is requesting.
- :ref:`dimensions<sec_dimensions>`: properties that apply to the dimensions (in `netCDF <https://www.unidata.ucar.edu/software/netcdf/workshops/2010/datamodels/NcDims.html>`__ terminology) of the model data. Each distinct dimension (coordinate axis) of the data being requested should be listed as a separate entry here.
- :ref:`varlist<sec_varlist>`: properties that describe the individual variables your diagnostic operates on. Each variable should be listed as a separate entry here.


.. _sec_settings:

Settings section
----------------

This section is an :ref:`object<object>` containing properties that label the diagnostic and describe its runtime requirements.

Example
^^^^^^^

.. code-block:: js

  "settings" : {
    "long_name" : "Effect of X on Y diagnostic",
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


Diagnostic description
^^^^^^^^^^^^^^^^^^^^^^

``long_name``: 
  String, **required**. Human-readable display name of your diagnostic. This is the text used to describe your diagnostic on the top-level index.html page. It should be in sentence case (capitalize first word and proper nouns only) and omit any punctuation at the end.

``driver``: 
  String, **required**. Filename of the top-level driver script the framework should call to run your diagnostic's analysis.

``realm``: 
  String or :ref:`array<array>` (list) of strings, **required**. One of the eight CMIP6 modeling realms (aerosol, atmos, atmosChem, land, landIce, ocean, ocnBgchem, seaIce) describing what data your diagnostic uses. If your diagnostic uses data from multiple realms, list them in an array (e.g. ``["atmos", "ocean"]``). This information doesn't affect how the framework fetches model data for your diagnostic: it's provided to give the user a shortcut to say, e.g., "run all the atmos diagnostics on this output."

Diagnostic runtime
^^^^^^^^^^^^^^^^^^

``runtime_requirements``: 
  :ref:`object<object>`, **required**. Programs your diagnostic needs to run (for example, scripting language interpreters) and any third-party libraries needed in those languages. Each executable should be listed in a separate key-value pair:

  - The *key* is the name of the required executable, e.g. languages such as "`python <https://www.python.org/>`__" or "`ncl <https://www.ncl.ucar.edu/>`__" etc. but also any utilities such as "`ncks <http://nco.sourceforge.net/>`__", "`cdo <https://code.mpimet.mpg.de/projects/cdo>`__", etc.
  - The *value* corresponding to each key is an :ref:`array<array>` (list) of strings, which are names of third-party libraries in that language that your diagnostic needs. You do *not* need to list standard libraries or scripts that are provided in a standard installation of your language: eg, in python, you need to list `numpy <https://numpy.org/>`__ but not `math <https://docs.python.org/3/library/math.html>`__. If no third-party libraries are needed, the value should be an empty list.

  In the future we plan to offer the capability to request specific `versions <https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/pkg-specs.html#package-match-specifications>`__. For now, please communicate your diagnostic's version requirements to the MDTF organizers.

``pod_env_vars``: 
  :ref:`object<object>`, optional. Names and values of shell environment variables used by your diagnostic, *in addition* to those supplied by the framework. The user can't change these at runtime, but this can be used to set site-specific installation settings for your diagnostic (eg, switching between low- and high-resolution observational data depending on what the user has chosen to download). Note that environment variable values must be provided as strings.


.. _sec_data:

Data section
------------

This section is an :ref:`object<object>` containing properties that apply to all the data your diagnostic is requesting.

Example
^^^^^^^

.. code-block:: js

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

  See the `netCDF FAQ <https://www.unidata.ucar.edu/software/netcdf/docs/faq.html#How-many-netCDF-formats-are-there-and-what-are-the-differences-among-them>`__ for information on the distinctions. Any recent version of a supported language for diagnostics with netCDF support will be able to read all of these. However, the extended features of the ``"netcdf4"`` data model are not commonly used in practice and currently only supported at a beta level in NCL, which is why we've chosen ``"any_netcdf_classic"`` as the default.


``rename_dimensions``:
  Boolean. Optional: assumed ``false`` if not specified. If set to ``true``, the framework will change the name of all :ref:`dimensions<sec_dimensions>` in the model data from the model's native value to the string specified in the ``name`` property for that dimension. If set to ``false``, **the diagnostic is responsible for reading dimension names from the environment variable**. See the environment variable :doc:`documentation <ref_envvars>` for details on how these names are provided.

``rename_variables``: 
  Boolean. Optional: assumed ``false`` if not specified. If set to ``true``, the framework will change the name of all :ref:`variables<sec_varlist>` in the model data from the model's native value to the string specified in the ``name`` property for that variable. If set to ``false``, **the diagnostic is responsible for reading dimension names from the environment variable**. See the environment variable :doc:`documentation <ref_envvars>` for details on how these names are provided.

.. _multi_file:

``multi_file_ok``: 
  Boolean. Optional: assumed ``false`` if not specified. If set to ``true``, the diagnostic is signalling that it's able to accept data for a single variable that may be spread out in multiple files, to be aggregated along the time dimension (e.g. through the use of `xarray <http://xarray.pydata.org/en/stable/generated/xarray.open_mfdataset.html>`__.) Aggregation along the time dimension is the only type of aggregation the diagnostic will need to consider. 

  If ``false``, the framework will ensure all data for a single variable is presented as a single netCDF file. This may lead to large file sizes if your diagnostic uses high-frequency data, in which case you should consider setting a limit via ``max_duration``.

``min_duration``, ``max_duration``: 
  :ref:`Time durations<time_duration>`. Optional: assumed ``"any"`` if not specified. Set minimum and maximum length of the analysis period for which the diagnostic should be run: this overrides any choices the user makes at runtime. Some example uses of this setting are:
  
  - If your diagnostic uses low-frequency (e.g. seasonal) data, you may want to set ``min_duration`` to ensure the sample size will be large enough for your results to be statistically meaningful. 
  - On the other hand, if your diagnostic uses high-frequency (e.g. hourly) data, you may want to set ``max_duration`` to prevent the framework from attempting to download a large volume of data for your diagnostic if the framework is called with a multi-decadal analysis period.

The following properties can optionally be set individually for each variable in the varlist :ref:`section<sec_varlist>`. If so, they will override the global settings given here.

.. _dims_ordered:

``dimensions_ordered``: 
  Boolean. Optional: assumed ``false`` if not specified. If set to ``true``, the framework will ensure that the dimensions of each variable's array are given in the same order as listed in ``dimensions``. **If set to false, your diagnostic is responsible for handling arbitrary dimension orders**: e.g. it should *not* assume that 3D data will be presented as (time, lat, lon).

.. _freq_target:

``frequency``, ``min_frequency``, ``max_frequency``: 
  :ref:`Time durations<time_duration>`. Time frequency at which the data is provided. Either ``frequency`` or the min/max pair, or both, is required:

  - If only ``frequency`` is provided, the framework will attempt to obtain data at that frequency. If that's not available from the data source, your diagnostic will not run. 
  - If the min/max pair is provided, the diagnostic must be capable of using data at any frequency within that range (inclusive). **The diagnostic is responsible for determining the frequency** from the data file itself if this option is used.
  - If all three properties are set, the framework will first attempt to find data at ``frequency``. If that's not available, it will try data within the min/max range, so your code must be able to handle this possibility.


.. _sec_dimensions:

Dimensions section
------------------

This section is an :ref:`object<object>` contains properties that apply to the dimensions of model data. "Dimensions" are meant in the sense of the netCDF `data model <https://www.unidata.ucar.edu/software/netcdf/workshops/2010/datamodels/NcDims.html>`__, and "coordinate dimensions" in the CF conventions: informally, they are "coordinate axes" holding the values of independent variables that the dependent variables are sampled at.

All :ref:`dimensions<item_var_dims>` and :ref:`scalar coordinates<item_var_coords>` referenced by variables in the varlist section must have an entry in this section. If two variables reference the same dimension, they will be sampled on the same set of *spatial* values. Different time values are specified with the ``frequency`` attribute on varlist entries. 

**Note** that the framework currently *only* supports the (simplest and most common) "independent axes" case of the `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#_independent_latitude_longitude_vertical_and_time_axes>`__. In particular, the framework only deals with data on lat-lon grids. 

Example
^^^^^^^

.. code-block:: js

  "dimensions": {
    "lat": {
        "standard_name": "latitude",
        "units": "degrees_N",
        "range": [-90, 90],
        "need_bounds": false
    },
    "lon": {
        "standard_name": "longitude",
        "units": "degrees_E",
        "range": [-180, 180],
        "need_bounds": false
    },
    "plev": {
        "standard_name": "air_pressure",
        "units": "hPa",
        "positive": "down",
        "need_bounds": false
    },
    "time": {
        "standard_name": "time",
        "units": "days",
        "calendar": "noleap",
        "need_bounds": false
    }
  }


Latitude and Longitude
^^^^^^^^^^^^^^^^^^^^^^

``standard_name``: 
  **Required**, string. Must be ``"latitude"`` and ``"longitude"``, respectively.

``units``: 
  Optional, a :ref:`CFunit<cfunit>`. Units the diagnostic expects the dimension to be in. Currently the framework only supports decimal ``degrees_north`` and ``degrees_east``, respectively.

``range``: 
  :ref:`Array<array>` (list) of two numbers. Optional. If given, specifies the range of values the diagnostic expects this dimension to take. For example, ``"range": [-180, 180]`` for longitude will have the first entry of the longitude variable in each data file be near -180 degrees (not exactly -180, because dimension values are cell midpoints), and the last entry near +180 degrees.

``need_bounds``: 
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ensure that bounds are supplied for this dimension, in addition to its midpoint values, following the `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#cell-boundaries>`__: the ``bounds`` attribute of this dimension will be set to the name of another netCDF variable containing the bounds information.

``axis``:
  String, optional. Assumed to be ``Y`` and ``X`` respectively if omitted, or if ``standard_name`` is ``"latitude"`` or ``"longitude"``. Included here to enable future support for non-lat-lon horizontal coordinates.

Time
^^^^

``standard_name``: 
  **Required**. Must be ``"time"``.

``units``: 
  String. Optional, defaults to "day". Units the diagnostic expects the dimension to be in. Currently the diagnostic only supports time axes of the form "<units> since <reference data>", and the value given here is interpreted in this sense (e.g. settings this to "day" would accommodate a dimension of the form "[decimal] days since 1850-01-01".)

``calendar``: 
  String, Optional. One of the CF convention `calendars <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#calendar>`__ or the string ``"any"``. **Defaults to "any" if not given**. Calendar convention used by your diagnostic. Only affects the number of days per month.

``need_bounds``: 
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ensure that bounds are supplied for this dimension, in addition to its midpoint values, following the `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#cell-boundaries>`__: the ``bounds`` attribute of this dimension will be set to the name of another netCDF variable containing the bounds information.

``axis``:
  String, optional. Assumed to be ``T`` if omitted or provided.

Z axis (height/depth, pressure, ...)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``standard_name``: 
  **Required**, string. `Standard name <http://cfconventions.org/Data/cf-standard-names/72/build/cf-standard-name-table.html>`__ of the variable as defined by the `CF conventions <http://cfconventions.org/>`__, or a commonly used synonym as employed in the CMIP6 MIP tables.

``units``: 
  Optional, a :ref:`CFunit<cfunit>`. Units the diagnostic expects the dimension to be in. **If not provided, the framework will assume CF convention** `canonical units <http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>`__.

``positive``: 
  String, **required**. Must be ``"up"`` or ``"down"``, according to the `CF conventions <http://cfconventions.org/faq.html#vertical_coords_positive_attribute>`__. A pressure axis is always ``"down"`` (increasing values are closer to the center of the earth), but this is not set automatically.

``need_bounds``: 
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ensure that bounds are supplied for this dimension, in addition to its midpoint values, following the `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#cell-boundaries>`__: the ``bounds`` attribute of this dimension will be set to the name of another netCDF variable containing the bounds information.

``axis``:
  String, optional. Assumed to be ``Z`` if omitted or provided.

Other dimensions (wavelength, ...)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``standard_name``: 
  **Required**, string. `Standard name <http://cfconventions.org/Data/cf-standard-names/72/build/cf-standard-name-table.html>`__ of the variable as defined by the `CF conventions <http://cfconventions.org/>`__, or a commonly used synonym as employed in the CMIP6 MIP tables.

``units``: 
  Optional, a :ref:`CFunit<cfunit>`. Units the diagnostic expects the dimension to be in. **If not provided, the framework will assume CF convention** `canonical units <http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>`__.

``need_bounds``: 
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ensure that bounds are supplied for this dimension, in addition to its midpoint values, following the `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#cell-boundaries>`__: the ``bounds`` attribute of this dimension will be set to the name of another netCDF variable containing the bounds information.

.. _sec_varlist:

Varlist section
---------------

This section is an :ref:`object<object>` contains properties that apply to the model variables your diagnostic needs for its analysis. "Dimensions" are meant in the sense of the netCDF `data model <https://www.unidata.ucar.edu/software/netcdf/workshops/2010/datamodels/NcVars.html>`__: informally, they are the "dependent variables" whose values are being computed as a function of the values stored in the dimensions.

**Note** that this includes "auxiliary coordinates" in the CF conventions terminology and similar ancillary information. If your diagnostic needs, eg, cell areas or volumes, orography data, etc., each piece of data should be listed as a separate entry here, *even if* their use is conventionally implied by the use of other variables.

Each entry corresponds to a distinct data file (or set of files, if ``multi_file_ok`` is ``true``) downloaded by the framework. If your framework needs the same physical quantity sampled with different properties (e.g. slices of a variable at multiple pressure levels), specify them as multiple entries.

Varlist entry example
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: js

  "u500": {
      "standard_name": "eastward_wind",
      "path_variable": "U500_FILE",
      "units": "m s-1",
      "dimensions" : ["time", "lat", "lon"],
      "dimensions_ordered": true,
      "scalar_coordinates": {"pressure": 500},
      "requirement": "optional",
      "alternates": ["another_variable_name", "a_third_variable_name"]
  }


Varlist entry properties
^^^^^^^^^^^^^^^^^^^^^^^^

The *key* in a varlist key-value pair is the name your diagnostic uses to refer to this variable (and must be unique). The value of the key-value pair is an :ref:`object<object>` containing properties specific to that variable:

``standard_name``: 
  String, **required**. `Standard name <http://cfconventions.org/Data/cf-standard-names/72/build/cf-standard-name-table.html>`__ of the variable as defined by the `CF conventions <http://cfconventions.org/>`__, or a commonly used synonym as employed in the CMIP6 MIP tables (e.g. "ua" instead of "eastward_wind"). 

``path_variable``: 
  String, **optional** but recommended. Name of the shell environment variable the framework will set with the location of this data. **This is the only currently supported method for communicating the location of model data to your diagnostic.** If omitted, set to ``<key>_FILE``, where ``<key>`` is the key to the varlist entry (case-sensitive). See the environment variable :doc:`documentation <ref_envvars>` for details. 

  - If ``multi_file_ok`` is ``false``, ``<path_variable>`` will be set to the absolute path to the netcdf file containing this variable's data.
  - If ``multi_file_ok`` is ``true``, ``<path_variable>`` will be a single path *or* a colon-separated list of paths to the files containing this data. Files will be listed in  order of the dates of their contents.
  - If the variable is listed as ``"optional"`` or ``"alternate"`` or has ``alternate`` variables listed, ``<path_variable>`` will be defined but set to the empty string if the framework couldn't obtain this data from the data source. **Your diagnostic should test for this possibility**. (If the variable is required but the framework couldn't obtain data, an error will be logged and your diagnostic will not run).

``use_exact_name``:
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ignore the model's naming conventions and *only* look for a variable with a name matching the key of this entry, regardless of what model or data source the framework is using. The only use case for this setting is to give diagnostics the ability to request data that falls outside the CF conventions: in general, you should rely on the framework to translate CF standard names to the native field names of the model being analyzed. 

``units``: 
  Optional, a :ref:`CFunit<cfunit>`. Units the diagnostic expects the variable to be in. **If not provided, the framework will assume CF convention**  `canonical units <http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>`__.

.. _item_var_dims:

``dimensions``:
  **Required**. List of strings, which must be selected the keys of entries in the :ref:`dimensions<sec_dimensions>` section. Dimensions of the array containing the variable's data. **Note** that the framework will not reorder dimensions (transpose) unless ``dimensions_ordered`` is additionally set to ``true``.

``dimensions_ordered``: 
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ensure that the dimensions of this variable's array are given in the same order as listed in ``dimensions``. **If set to false, your diagnostic is responsible for handling arbitrary dimension orders**: e.g. it should *not* assume that 3D data will be presented as (time, lat, lon). If given here, overrides the values set globally in the ``data`` section (see :ref:`description<dims_ordered>` there).

.. _item_var_coords:

``scalar_coordinates``: 
  :ref:`object<object>`, optional. This implements what the CF conventions refer to as "`scalar coordinates <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__", with the use case here being the ability to request slices of higher-dimensional data. For example, the snippet at the beginning of this section shows how to request the u component of wind velocity on a 500 mb pressure level.

  - *keys* are the key (name) of an entry in the :ref:`dimensions<sec_dimensions>` section.
  - *values* are a single number (integer or floating-point) corresponding to the value of the slice to extract. **Units** of this number are taken to be the ``units`` property of the dimension named as the key.

  In order to request multiple slices (e.g. wind velocity on multiple pressure levels, with each level saved to a different file), create one varlist entry per slice.

``frequency``, ``min_frequency``, ``max_frequency``: 
  :ref:`Time durations<time_duration>`. Optional. Time frequency at which the variable's data is provided. If given here, overrides the values set globally in the ``data`` section (see :ref:`description<freq_target>` there).

``requirement``: 
  String. Optional: assumed ``"required"`` if not specified. One of three values:

  - ``"required"``: variable is necessary for the diagnostic's calculations. If the data source doesn't provide the variable (at the requested frequency, etc., for the user-specified analysis period) the framework will *not* run the diagnostic, but will instead log an error message explaining that the lack of this data was at fault.
  - ``"optional"``: variable will be supplied to the diagnostic if provided by the data source. If not available, the diagnostic will still run, and the ``path_variable`` for this variable will be set to the empty string. **The diagnostic is responsible for testing the environment variable** for the existence of all optional variables.
  - ``"alternate"``: variable is specified as an alternate source of data for some other variable (see next property). The framework will only query the data source for this variable if it's unable to obtain one of the *other* variables that list it as an alternate.

``alternates``: 
  :ref:`Array<array>` (list) of strings, which must be keys (names) of other variables. Optional: if provided, specifies an alternative method for obtaining needed data if this variable isn't provided by the data source. 
  
  - If the data source provides this variable (at the requested frequency, etc., for the user-specified analysis period), this property is ignored.
  - If this variable isn't available as requested, the framework will query the data source for all of the variables listed in this property. If *all* of the alternate variables are available, the diagnostic will be run; if any are missing it will be skipped. Note that, as currently implemented, only one set of alternates may be given (no "plan B", "plan C", etc.)
