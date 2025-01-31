.. role:: console(code)
   :language: console
   :class: highlight
.. _ref-catalogs:

ESM-intake catalogs
===================

The MDTF-diagnostics package uses `intake-ESM <https://intake-esm.readthedocs.io/en/stable/>`__ catalogs and APIs to
access model datasets and verify POD data requirements. Intake-ESM is a software package that uses
`intake <https://intake.readthedocs.io/en/latest/>`__ to load
catalog *assets*--netCDF or Zarr files and associated metadata--into a Pandas Dataframe or an xarray dataset.
Users can query catalogs and access data subsets according to desired date ranges, variables, simulations, and
other criteria without having to walk the directory structure or open files to verify information beforehand, making
them convenient and, depending on the location of the reference dataset, faster than on-the-fly file search methods.

Intake-ESM catalogs are generated using information from standardized directory structures and/or
file metadata using custom tools and or the ecgtools package following the intake-ESM recommendations. The final
output from the catalog generator will be a csv file populated with files and metadata, and a json header file that
points to the location of the csv file and contains information about the column headers. Users pass the json
header file to the intake-ESM `open-esm_datastore` utility so that it can parse the information in the csv file
to perform catalog queries.

.. code-block:: python

   # define dictionary with catalog query info
   query_dict = {}

   query_dict['frequency'] = "day"
   query_dict["realm"] = "atmos"
   query_dict['standard_name'] = "air_temperature"
   # open the intake-ESM catalog
   cat = intake.open_esm_datastore("/path/to/data_catalog.json")
   # query the catalog for data subset matching query_dict info
   cat_subset = cat.search(**query_dict)

The MDTF-diagnostics package provides a basic :ref:`catalog builder tool <ref-catalog-builder>` built on top of
`ecgtools <https://github.com/ncar-xdev/ecgtools>`__ that has been tested with
CMIP6, CESM, and GFDL datasets. GFDL also maintains a lightweight
`CatalogBuilder <https://github.com/NOAA-GFDL/CatalogBuilder>`__ that has been tested with GFDL and CMIP6 datasets.
Users may try both tools and select the one works best for their dataset and system, or create their own builder script.
The framework team will eventually merge the capabilities in the MDTF-diagnostics into the GFDL builder as the ecgtools
package is no longer under active development.

Required catalog information
----------------------------

The following intake-ESM catalog columns must be populated for each file for MDTF-diagnostics functionality; other
columns are optional at this time but may be used to refine query results in future releases:

  * activity_id: (str) the dataset convention:
      * "CMIP"
      * "CESM"
      * "GFDL"
  * file_path: (str) full path to the file
  * frequency: (str) output frequency of data; use the following CMIP definitions:
      * sampled hourly = "1hr"
      * monthly-mean diurnal cycle resolving each day into 1-hour means = "1hrCM"
      * sampled hourly at specified time point within an hour = "1hrPt"
      * 3 hourly mean samples = "3hr"
      * sampled 3 hourly at specified time point within the time period = "3hrPt"
      * 6 hourly mean samples = "6hr"
      * sampled 6 hourly at specified time point within the time period = "6hrPt"
      * daily mean samples = "day"
      * decadal mean samples = "dec"
      * fixed (time invariant) field = "fx"
      * monthly mean samples = "mon"
      * monthly climatology computed from monthly mean samples = "monC"
      * sampled monthly at specified time point within the time period = "monPt"
      * sampled sub-hourly at specified time point within an hour = "subhrPt"
      * annual mean samples = "yr"
      * sampled yearly at specified time point within the time period = "yrPt"
  * realm | modeling_realm: (str) model realm for the variable; use the following CMIP definitions if possible:
      * Aerosol = "aerosol"
      * Atmosphere = "atmos"
      * Atmospheric Chemistry = "atmosChem"
      * Land Surface = "land"
      * Land Ice = "landIce"
      * Ocean = "ocean"
      * Ocean Biogeochemistry = "ocnBgchem"
      * Sea Ice = "seaIce"
  * standard_name: (str) if a standard_name is not defined for a variable in the target file, use the equivalent CMIP6
    standard_name defined in the appropriate
    `fieldlist table <https://github.com/NOAA-GFDL/MDTF-diagnostics/tree/main/data>`__ if one is available. If no
    standard_name is available, open an issue requesting an addition to the fieldlist tables(s) for your variable. The
    task force will create a standard_name if one does not exist so that the catalog builders and the framework can
    cross-reference the entries for catalog generation and data translation.
  * time_range: (str or int) time range spanned by file with start_time and end_time separated by a '-', e.g.,:
      * yyyy-mm-dd-yyyy-mm-dd
      * yyyymmdd:HHMMSS-yyyymmdd:HHMMSS
  * units: (str) variable units. Unitless variables should have units of '1'.
  * variable_id: (str) variable name id (e.g., temp, precip, PSL, TAUX)
