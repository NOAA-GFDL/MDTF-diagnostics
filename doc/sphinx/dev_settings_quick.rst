.. _ref-dev-settings-quick:

POD settings file summary
=========================

This page gives a quick introduction to how to write the settings file for your POD. See the full :doc:`documentation <./ref_settings>` on this file format for a complete list of all the options you can specify.

Overview
--------

The MDTF framework can be viewed as a "wrapper" for your code that handles data fetching and munging. Your code communicates with this wrapper in two ways:

- The *settings file* is where your code talks to the framework: when you write your code, you document what model data your code uses and what format it expects it in. When the framework is run, it will fulfill the requests you make here (or tell the user what went wrong).
- When your code is run, the framework talks to it by setting :doc:`environment variables <ref_envvars>` containing paths to the data files and other information specific to the run. 

In the settings file, you specify what model data your diagnostic uses in a vocabulary you're already familiar with:

- The `CF conventions <http://cfconventions.org/>`__ for standardized variable names and units.
- The netCDF4 (classic) data model, in particular the notions of `variables <https://www.unidata.ucar.edu/software/netcdf/workshops/2010/datamodels/NcVars.html>`__ and `dimensions <https://www.unidata.ucar.edu/software/netcdf/workshops/2010/datamodels/NcDims.html>`__ as they're used in a netCDF file. 


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
        "path_variable": "PATH_TO_PR_FILE",
        "units": "kg m-2 s-1",
        "dimensions" : ["time", "lat", "lon"]
      },
      "my_3d_u_data": {
        "standard_name": "eastward_wind",
        "path_variable": "PATH_TO_UA_FILE",
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
  One or more of the eight CMIP6 modeling realms (aerosol, atmos, atmosChem, land, landIce, ocean, ocnBgchem, seaIce) describing what data your diagnostic uses. This is give the user an easy way to, eg, run only ocean diagnostics on data from an ocean model.

``runtime_requirements``: 
  This is a list of key-value pairs describing the programs your diagnostic needs to run, and any third-party libraries used by those programs.

  - The *key* is program's name, eg. languages such as "`python <https://www.python.org/>`__" or "`ncl <https://www.ncl.ucar.edu/>`__" etc. but also any utilities such as "`ncks <http://nco.sourceforge.net/>`__", "`cdo <https://code.mpimet.mpg.de/projects/cdo>`__", etc.
  - The *value* for each program is a list of third-party libraries in that language that your diagnostic needs. You do *not* need to list built-in libraries: eg, in python, you should to list `numpy <https://numpy.org/>`__ but not `math <https://docs.python.org/3/library/math.html>`__. If no third-party libraries are needed, the value should be an empty list.

Data section
------------

This section contains settings that apply to all the data your diagnostic uses. Most of them are optional.

``frequency``:
  The time frequency the model data should be provided at, eg. "1hr", "6hr", "day", "mon", ...


Dimensions section
------------------

This section is where you list the dimensions (coordinate axes) your variables are provided on. Each entry should be a key-value pair, where the key is the name your diagnostic uses for that dimension internally, and the value is a list of settings describing that dimension. In order to be unambiguous, all dimensions must specify at least:

``standard_name``: 
  The CF `standard name <http://cfconventions.org/Data/cf-standard-names/72/build/cf-standard-name-table.html>`__ for that coordinate.

``units``:
  The units the diagnostic expects that coordinate to be in (using the syntax of the `UDUnits library <https://www.unidata.ucar.edu/software/udunits/udunits-2.0.4/udunits2lib.html#Syntax>`__). This is optional: if not given, the framework will assume you want CF convention `canonical units <http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>`__.

In addition, any vertical (Z axis) dimension must specify:

``positive``: 
  Either ``"up"`` or ``"down"``, according to the `CF conventions <http://cfconventions.org/faq.html#vertical_coords_positive_attribute>`__. A pressure axis is always ``"down"`` (increasing values are closer to the center of the earth).

Varlist section
---------------

This section is where you list the variables your diagnostic uses. Each entry should be a key-value pair, where the key is the name your diagnostic uses for that variable internally, and the value is a list of settings describing that variable. Most settings here are optional, but the main ones are:

``standard_name``: 
  The CF `standard name <http://cfconventions.org/Data/cf-standard-names/72/build/cf-standard-name-table.html>`__ for that variable.

``path_variable``: 
  Name of the shell environment variable the framework will use to pass the location of the file containing this variable to your diagnostic when it's run. See the environment variable :doc:`documentation <ref_envvars>` for details. 

``units``:
  The units the diagnostic expects the variable to be in (using the syntax of the `UDUnits library <https://www.unidata.ucar.edu/software/udunits/udunits-2.0.4/udunits2lib.html#Syntax>`__). This is optional: if not given, the framework will assume you want CF convention `canonical units <http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html>`__.

``dimensions``:
  List of names of dimensions specified in the "dimensions" section, to specify the coordinate dependence of each variable.

