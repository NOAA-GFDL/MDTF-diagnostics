Xarray metadata parser
======================

The job of the parser is to standardize the metadata and other attributes of model data files after they're opened by the preprocessor. The goal is for *all* needed standardization, data validation and other checks to be performed here, so that the logic in the preprocessor functions can safely make assumptions about the structure of the dataset they operate on, rather than having to code (and test) for every case they may encounter.

:meth:`~src.xr_parser.parse` is the "public" method for xr\_parser's functionality. It first performs the following dataset-wide operations:

- :meth:`~src.xr_parser.munge_ds_attrs`, which strips whitespace and does other proofreading on the raw xarray attributes.
- `xarray's <http://xarray.pydata.org/en/stable/index.html>`__ own `decode_cf() <http://xarray.pydata.org/en/stable/generated/xarray.decode_cf.html>`__ method, which primarily decodes the time coordinate to `cftime.datetime <https://unidata.github.io/cftime/api.html#cftime.datetime>`__ objects, which are properly calendar-aware.
- `cf\_xarray's <https://cf-xarray.readthedocs.io/en/latest/index.html>`__ `guess\_coord\_axis() <https://cf-xarray.readthedocs.io/en/latest/generated/xarray.DataArray.cf.guess_coord_axis.html#xarray.DataArray.cf.guess_coord_axis>`__ method, which uses heuristics to assign axis labels ('X', 'Y', 'Z', 'T') to dataset coordinates. 
- :meth:`~src.xr_parser.check_calendar`, which checks whether decode\_cf() parsed the date axis correctly, and if not, looks for calendar information in some non-standard locations.

TBD
---

