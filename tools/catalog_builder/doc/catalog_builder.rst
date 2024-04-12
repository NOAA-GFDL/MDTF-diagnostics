.. _ref-catalog-builder:

catalog_builder.py
==================

USAGE
-----
Generate ESM-intake catalogs for datasets stored using the CMIP6, CESM, and GFDL
archive directory and retrieval structures (DRSs).

To run interactively:

.. code-block:: shell

    > cd MDTF-diagnostics/tools/catalog_builder
    > conda activate _MDTF_base
    > python3 catalog_builder.py --config [CONFIG FILE NAME].yml

Submit a SLURM batch job:

.. code-block:: shell

    > sbatch catalog_builder_slurm.csh -config [CONFIG FILE NAME].yml

Input
-----
Yaml file with configuration to build an ESM intake catalog

Output
------
A csv file with ESM-intake catalog entries for the target
root directory(ies) in the configuration file, and a json file
with the catalog column headers. Example catalog and header files
for CMIP6 dataset stored on the GFDL uda file system are located in
the examples/cmip subdirectory.

Required packages:
------------------
The required packages are included in the _MDTF_base conda
environment:

- click
- dask
- datetime
- ecgtools
- intake
- os
- pathlib
- shutil
- sys
- time
- traceback
- typing
- xarray
- yaml

Configuration file:
-------------------
The configuration file defines the following parameters to generate the ESM-intake catalog:

- convention (required): DRS convention to use: cmip (default), gfdl, or cesm
- data_root_dirs (required): a list of root directory paths with files to query
- dir_depth (required): the directory depth to traverse in the paths.
  A dir_depth=1 means that the files are in the root directory(ies),
  a dir_depth=2 means the files are in one or
  more subdirectories one level down from the root directory(ies) and so on
- output_dir (required): directory where catalog and header files will be written
- output_filename (required): base name of the catalog and header files
  (.csv and .json are appended by the program)
- num_threads (required): number of cpu threads to run with
- include_patterns (optional): list of patterns to include in search; supports wildcards
- exclude_patterns (optional): list of patterns to exclude from search; supports wildcards

Templates for the configuration file and a slurm batch submission script for GFDL PPAN are
located in the examples/templates subdirectory.