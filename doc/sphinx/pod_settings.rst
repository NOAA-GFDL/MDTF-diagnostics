.. _ref-pod-settings:

POD settings file summary
=========================

This page gives a quick introduction to how to write the settings file for your POD. See the full
:doc:`documentation <./ref_settings>` on this file format for a complete list of all the options you can specify.

Overview
--------

The MDTF framework can be viewed as a "wrapper" for your code that handles data fetching and munging. Your code
communicates with this wrapper in two ways:

- The *settings file* is where your code talks to the framework: when you write your code, you document what model data
your code uses and what format it expects it in. When the framework is run, it will fulfill the requests you make here
(or tell the user what went wrong).
- When your code is run, the framework talks to it by setting :doc:`environment variables <ref_envvars>`
 containing paths to the data files and other information specific to the run.

In the settings file, you specify what model data your diagnostic uses in a vocabulary you're already familiar with:

- The `CF conventions <http://cfconventions.org/>`__ for standardized variable names and units.
- The netCDF4 (classic) data model, in particular the notions of
  `variables <https://www.unidata.ucar.edu/software/netcdf/workshops/2010/datamodels/NcVars.html>`__ and
  `dimensions <https://www.unidata.ucar.edu/software/netcdf/workshops/2010/datamodels/NcDims.html>`__ as they're used
  in a netCDF file.


Example
-------

.. code-block:: js

  // Any text to the right of a '//' is a comment
  {
    "settings" : {
      "long_name": "My example diagnostic",
      "driver": "example_diagnostic.py",
      "realm": "atmos",
      "runtime_requirements": {
        "python": ["numpy", "matplotlib", "netCDF4"]
      }
    },
    "data" : {
      "frequency": "day"
    },
    "dimensions": {
      "lat": {
        "standard_name": "latitude"
      },
      "lon": {
        "standard_name": "longitude"
      },
      "plev": {
        "standard_name": "air_pressure",
        "units": "hPa",
        "positive": "down"
      },
      "time": {
        "standard_name": "time",
        "units": "day"
      }
    },
    "varlist" : {
      "my_precip_data": {
        "standard_name": "precipitation_flux",
        "units": "kg m-2 s-1",
        "dimensions" : ["time", "lat", "lon"]
      },
      "my_3d_u_data": {
        "standard_name": "eastward_wind",
        "units": "m s-1",
        "dimensions" : ["time", "plev", "lat", "lon"]
      }
    }
  }


Settings section
----------------

This is where you describe your diagnostic and list the programs it needs to run.

``long_name``: 
  Display name of your diagnostic, used to describe your diagnostic on the top-level index.html page. Can contain spaces.

``driver``: 
  Filename of the driver script the framework should call to run your diagnostic.

``realm``: 
  One or more of the eight CMIP6 modeling realms (aerosol, atmos, atmosChem, land, landIce, ocean, ocnBgchem, seaIce)
  describing what data your diagnostic uses. This is give the user an easy way to, eg, run only ocean diagnostics on
  data from an ocean model. Realm can be specified in the `settings`` section, or specified separately for each variable
  in the `varlist` section.

``runtime_requirements``: 
  This is a list of key-value pairs describing the programs your diagnostic needs to run, and any third-party libraries
  used by those programs.

  - The *key* is program's name, eg. languages such as "`python <https://www.python.org/>`__" or
    "`ncl <https://www.ncl.ucar.edu/>`__" etc. but also any utilities such as "`ncks <http://nco.sourceforge.net/>`__",
    "`cdo <https://code.mpimet.mpg.de/projects/cdo>`__", etc.
  - The *value* for each program is a list of third-party libraries in that language that your diagnostic needs. You do
    *not* need to list built-in libraries: eg, in python, you should to list `numpy <https://numpy.org/>`__ but not
    `math <https://docs.python.org/3/library/math.html>`__. If no third-party libraries are needed,
    the value should be an empty list.

``pod_env_vars``:
  :ref:`object<object>`, optional. Names and values of shell environment variables used by your diagnostic,
  *in addition* to those supplied by the framework. The user can't change these at runtime, but this can be used to set
  site-specific installation settings for your diagnostic (eg, switching between low- and high-resolution observational
  data depending on what the user has chosen to download). Note that environment variable values must be provided as
  strings.

Data section
------------

This section contains settings that apply to all the data your diagnostic uses. Most of them are optional.

``frequency``:
  A string specifying a time span, used e.g. to describe how frequently data is sampled.
  It consists of an optional integer (if omitted, the integer is assumed to be 1) and a units string which is one of
  ``hr``, ``day``, ``mon``, ``yr`` or ``fx``. ``fx`` is used where appropriate to denote time-independent data.
  Common synonyms for these units are also recognized (e.g. ``monthly``, ``month``, ``months``, ``mo`` for ``mon``,
  ``static`` for ``fx``, etc.)

.. _sec_dimensions:

Dimensions section
------------------

This section is where you list the dimensions (coordinate axes) your variables are provided on. Each entry should be a
key-value pair, where the key is the name your diagnostic uses for that dimension internally, and the value is a list of
settings describing that dimension. In order to be unambiguous, all dimensions must specify at least:

Latitude and Longitude
^^^^^^^^^^^^^^^^^^^^^^

``standard_name``:
  **Required**, string. Must be ``"latitude"`` and ``"longitude"``, respectively.

``units``:
  Optional, a :ref:`CFunit<cfunit>`. Units the diagnostic expects the dimension to be in. Currently the framework only
  supports decimal ``degrees_north`` and ``degrees_east``, respectively.

``range``:
  :ref:`Array<array>` (list) of two numbers. Optional. If given, specifies the range of values the diagnostic expects
  this dimension to take. For example, ``"range": [-180, 180]`` for longitude will have the first entry of the longitude
  variable in each data file be near -180 degrees (not exactly -180, because dimension values are cell midpoints), and
  the last entry near +180 degrees.

``need_bounds``:
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ensure that bounds are supplied
  for this dimension, in addition to its midpoint values, following the
  `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#cell-boundaries>`__:
  the ``bounds`` attribute of this dimension will be set to the name of another netCDF variable containing the bounds
  information.

``axis``:
  String, optional. Assumed to be ``Y`` and ``X`` respectively if omitted, or if ``standard_name`` is
  ``"latitude"`` or ``"longitude"``. Included here to enable future support for non-lat-lon horizontal coordinates.

Time
^^^^

``standard_name``:
  **Required**. Must be ``"time"``.

``units``:
  String. Optional, defaults to "day". Units the diagnostic expects the dimension to be in. Currently the diagnostic
  only supports time axes of the form "<units> since <reference data>", and the value given here is interpreted in this
  sense (e.g. settings this to "day" would accommodate a dimension of the form "[decimal] days since 1850-01-01".)

``calendar``:
  String, Optional. One of the CF convention
  `calendars <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#calendar>`__ or
  the string ``"any"``. **Defaults to "any" if not given**. Calendar convention used by your diagnostic. Only affects
  the number of days per month.

``need_bounds``:
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ensure that bounds are supplied
  for this dimension, in addition to its midpoint values, following the
  `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#cell-boundaries>`__: the ``bounds`` attribute of this dimension will be set to the name of another netCDF variable containing the bounds information.

``axis``:
  String, optional. Assumed to be ``T`` if omitted or provided.

Z axis (height/depth, pressure, ...)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``standard_name``:
  **Required**, string.
  `Standard name <http://cfconventions.org/Data/cf-standard-names/72/build/cf-standard-name-table.html>`__ of the
  variable as defined by the `CF conventions <http://cfconventions.org/>`__, or a commonly used synonym as employed in
  the CMIP6 MIP tables.

``units``:
  Optional, a :ref:`CFunit<cfunit>`. Units the diagnostic expects the dimension to be in. **If not provided, the
  framework will assume CF convention**
  `canonical units <http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>`__.

``positive``:
  String, **required**. Must be ``"up"`` or ``"down"``, according to the
  `CF conventions <http://cfconventions.org/faq.html#vertical_coords_positive_attribute>`__.
  A pressure axis is always ``"down"`` (increasing values are closer to the center of the earth), but this is not set
  automatically.

``need_bounds``:
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ensure that bounds are supplied
  for this dimension, in addition to its midpoint values, following the
  `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#cell-boundaries>`__:
  the ``bounds`` attribute of this dimension will be set to the name of another netCDF variable containing the bounds
  information.

``axis``:
  String, optional. Assumed to be ``Z`` if omitted or provided.

Other dimensions (wavelength, ...)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``standard_name``:
  **Required**, string. `Standard name <http://cfconventions.org/Data/cf-standard-names/72/build/cf-standard-name-table.html>`__
  of the variable as defined by the `CF conventions <http://cfconventions.org/>`__, or a commonly used synonym as
  employed in the CMIP6 MIP tables.

``units``:
  Optional, a :ref:`CFunit<cfunit>`. Units the diagnostic expects the dimension to be in. **If not provided, the framework will assume CF convention** `canonical units <http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>`__.

``need_bounds``:
  Boolean. Optional: assumed ``false`` if not specified. If ``true``, the framework will ensure that bounds are supplied
  for this dimension, in addition to its midpoint values, following the
  `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#cell-boundaries>`__:
  the ``bounds`` attribute of this dimension will be set to the name of another netCDF variable containing the bounds
  information.

.. _sec_varlist:

Varlist section
---------------

Varlist entry example
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: js

  "u500": {
      "standard_name": "eastward_wind",
      "units": "m s-1",
      "realm": "atmos",
      "dimensions" : ["time", "lat", "lon"],
      "scalar_coordinates": {"plev": 500},
      "requirement": "optional",
      "alternates": ["another_variable_name", "a_third_variable_name"]
  }

This section is where you list the variables your diagnostic uses. Each entry should be a key-value pair, where the key
is the name your diagnostic uses for that variable internally, and the value is a list of settings describing that
variable. Most settings here are optional, but the main ones are:

``standard_name``: 
  The CF `standard name <http://cfconventions.org/Data/cf-standard-names/72/build/cf-standard-name-table.html>`__
  for that variable.

``units``:
  The units the diagnostic expects the variable to be in (using the syntax of the
  `UDUnits library <https://www.unidata.ucar.edu/software/udunits/udunits-2.0.4/udunits2lib.html#Syntax>`__).

``dimensions``:
  List of names of dimensions specified in the "dimensions" section, to specify the coordinate dependence of each
  variable.

``realm`` (if not specified in the `settings` section):
  string or list of CMIP modeling realm(s) that the variable belongs to

``modifier``:
 String, optional; Descriptor to distinguish variables with identical standard names and different dimensionalities or
 realms. See `modifiers.jsonc <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/data/modifiers.jsonc>`__ for
 supported modfiers. Open an issue to request the addition of a new modifier to the modifiers.jsonc file, or submit a
 pull request that includes the new modifier in the modifiers.jsonc file and the necessary POD settings.jsonc file(s).

``requirement``:
  String. Optional; assumed ``"required"`` if not specified. One of three values:

  - ``"required"``: variable is necessary for the diagnostic's calculations. If the data source doesn't provide the
  variable (at the requested frequency, etc., for the user-specified analysis period) the framework will *not* run the
  diagnostic, but will instead log an error message explaining that the lack of this data was at fault.
  - ``"optional"``: variable will be supplied to the diagnostic if provided by the data source. If not available, the
  diagnostic will still run, and the ``path_variable`` for this variable will be set to the empty string.
  **The diagnostic is responsible for testing the environment variable** for the existence of all optional variables.
  - ``"alternate"``: variable is specified as an alternate source of data for some other variable (see next property).
  The framework will only query the data source for this variable if it's unable to obtain one of the *other* variables
  that list it as an alternate.

``alternates``:
  Array (list) of strings (e.g., ["A", "B"]), which must be keys (names) of other variables. Optional: if provided,
  specifies an alternative method for obtaining needed data if this variable isn't provided by the data source.

  - If the data source provides this variable (at the requested frequency, etc., for the user-specified
  analysis period), this property is ignored.
  - If this variable isn't available as requested, the framework will query the data source for all of the variables
  listed in this property. If *all* of the alternate variables are available, the diagnostic will be run; if any are
  missing it will be skipped. Note that, as currently implemented, only one set of alternates may be given
  (no "plan B", "plan C", etc.)

``scalar_coordinates``:
  optional key-value pair specifying a level to select from a 4-D field. This implements what the CF conventions refer
  to as
  "`scalar coordinates <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#scalar-coordinate-variables>`__",
  with the use case here being the ability to request slices of higher-dimensional data. For example, the snippet at
  the beginning of this section `{"plev": 500}` shows how to request the u component of wind velocity on a 500-mb
  pressure level.

  - *keys* are the key (name) of an entry in the :ref:`dimensions<sec_dimensions>` section.
  - *values* are a single number (integer or floating-point) corresponding to the value of the slice to extract.
  **Units** of this number are taken to be the ``units`` property of the dimension named as the key.

  In order to request multiple slices (e.g. wind velocity on multiple pressure levels, with each level saved to a
  different file), create one varlist entry per slice.
