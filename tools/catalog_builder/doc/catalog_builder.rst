.. _ref-catalog-builder:

catalog_builder.py
=====================

USAGE
-----
Generate esm-intake catalogs for datasets stored using the CMIP6, CESM, and GFDL
directory and retrieval structures (DRSs). The MDTF-diagnostics preprocessor tool
and framework code parse the catalogs instead of querying directories each time they
are run, improving performance and simplifying development.

To use, run the following command:

`> `

Input
-----


Output
------

Required packages:
------------------
The required packages are included in the _MDTF_base conda
environment:
- dask
- os
- sys
- intake
- ecgtools
- pathlib
- shutil