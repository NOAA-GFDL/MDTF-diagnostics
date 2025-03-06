.. role:: console(code)
   :language: console
   :class: highlight

.. _ref-data:

Model data format
=================

This section describes how all input model data must be "formatted" for use by the framework. By "format" we mean not
only the binary file format, but also the organization of data within and across files and metadata conventions.

A core design goal of this project is the ability to run diagnostics seamlessly on data from a wide variety of sources,
including different formats. The MDTF-diagnostics package leverages ESM-intake catalogs and APIs to query and access the
model datasets. As such, we can expand the package requirements to query additional metadata like grid type, institution,
or cell methods. If you would like the package to support formats or metadata conventions that aren't
currently supported, please make a request in the appropriate GitHub
`discussion thread <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/174>`__.

Model data format requirements
------------------------------

File organization
+++++++++++++++++

- Model data must be supplied in the form of a set of netCDF or Zarr files with locations and metadata defined in an
  ESM-intake catalog.

- The framework developers have provided a simple tool for generating data catalogs using CMIP, GFDL, and CESM
  conventions. The user community may modify this generator to suit their needs

- Each file may contain one variable (i.e., an array with the values of a single dependent variable, along with all of
  the values of the coordinates at which the dependent variable was sampled), or multiple variables. Refer to the
  ESM-intake documentation for `instructions to create and access data catalogs with multiple assets
  <https://intake-esm.readthedocs.io/en/stable/how-to/use-catalogs-with-assets-containing-multiple-variables.html>`__.

- The data for one variable may be spread across multiple netCDF files, but this must take the form of contiguous chunks
  by date (e.g., one file for 2000-2009, another for 2010-2019, etc.). The spatial coordinates in each file in a series
  of chunks must be identical.

Coordinates
+++++++++++

- The framework currently only supports model data provided on a latitude-longitude grid. The framework developers
  will extend support for non-rectilinear grids once requirements are finalized and use cases are provided.
- The framework currently only supports vertical coordinates given in terms of pressure. The pressure coordinate may be
  in any units (*mb*, *Pa*, *atm*, ...). We plan to offer support for
  `parametric vertical coordinates <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#parametric-vertical-coordinate>`__
  in the near future
- The time coordinate of the data must follow the
  `CF conventions <http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#time-coordinate>`__;
  in particular, it must have a ``calendar`` attribute which matches one of the CF conventions' recognized calendars
  (case-insensitive).
- The framework doesn't impose any limitations on the minimum or maximum resolution of model data, beyond the storage
  and memory available on the machine where the PODs are run.

.. _ref-data-metadata:

Metadata
++++++++

The framework currently makes use of the following metadata (attributes for each variable in the netCDF header),
in addition to the ``calendar`` attribute on the time coordinate:

- ``units``: Required for all variables and coordinates. This should be a string of the form recognized by
  `UDUNITS2 <https://www.unidata.ucar.edu/software/udunits/>`__, specifically the python
  `cfunits <https://ncas-cms.github.io/cfunits/>`__ package (which improves CF convention support, e.g. by recognizing
  ``'psu'`` as "practical salinity units.")
  
  This attribute is required because we allow PODs to request model data with specific units, rather than requiring each
  POD to implement and debug redundant unit conversion logic. Instead, unit checking and conversion is done by the
  framework. This can't be done if it's not clear what units the input data are in.

- ``standard_name``: If present, should be set to a recognized CF convention
  `standard name <http://cfconventions.org/Data/cf-standard-names/77/build/cf-standard-name-table.html>`__.
   This is used to confirm that the framework has downloaded the physical quantity that the POD has requested,
   independently of what name the model has given to the variable. If the input files do not contain a `standard_name`,
   attribute, consult the appropriate `fieldlist <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/data>`__ for the standard_name, or open an issue requesting that the fieldlists
   be updated with entries for your variables if they are missing.

- ``realm``: The model realm(s) that each variable is part of.
  
  If the user or data source has specified a :ref:`naming convention<ref-data-conventions>`, missing values for this
  attribute will be filled in based on the variable names used in that convention.

Many utilities exist for editing metadata in netCDF headers. Popular examples are the
`ncatted <http://nco.sourceforge.net/nco.html#ncatted>`__ tool in the `NCO <http://nco.sourceforge.net/>`__
utilities and the `setattribute <https://code.mpimet.mpg.de/projects/cdo/embedded/cdo_refcard.pdf>`__ operator in
`CDO <https://code.mpimet.mpg.de/projects/cdo>`__, as well as the functionality provided by xarray itself.

xarray reference implementation
-------------------------------

The framework uses `xarray <http://xarray.pydata.org/en/stable/>`__ to preprocess and validate model data before the
PODs are run; specifically using the `netcdf4 <https://unidata.github.io/netcdf4-python/>`__ engine and with
`CF convention support <http://xarray.pydata.org/en/stable/weather-climate.html#non-standard-calendars-and-dates-outside-the-timestamp-valid-range>`__
provided via the  `cftime <https://unidata.github.io/cftime/>`__ library. We also use
`cf_xarray <https://cf-xarray.readthedocs.io/en/latest/>`__ to access data attributes in a more convention-independent
way.

If you're deciding how to post-process your model's data for use by the MDTF-diagnostics package, or are debugging
issues with your
model's data format, it may be simpler to load and examine your data with these packages interactively, rather than by
invoking the entire package. The following python snippet approximates how the framework loads datasets for
preprocessing. Use the `\_MDTF_base <https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/main/src/conda/env_base.yml>`__
conda environment to install the correct versions of each package.

.. code-block:: python

   import cftime, cf_xarray
   import xarray as xr

   ds = xr.open_mfdataset(
       [<path to first file>, <second file>, ...],
       parallel=True,
       engine='netcdf4',
       combine='by_coords',
       data_vars='minimal', coords='minimal',
       compat='equals', join='exact',
       decode_cf=True, 
       decode_coords=True, 
       decode_times=True, use_cftime=True
   )
   # match coordinates to X/Y/Z/T axes using cf_xarray:
   ds = ds.cf.guess_coord_axis()
   # print summary
   ds.info()

The framework has additional logic for cleaning up noncompliant metadata (e.g.,
stripping whitespace from netCDF headers), but if you can load a dataset with the above commands,
the framework should be able to deal with it as well.

If the framework runs into errors when run on a dataset that meets the criteria above, please file a bug report via
the GitHub `issue tracker <https://github.com/NOAA-GFDL/MDTF-diagnostics/issues>`__.
