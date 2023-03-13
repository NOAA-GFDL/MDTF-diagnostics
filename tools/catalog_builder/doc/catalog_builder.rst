.. _ref-catalog-builder:

catalog_builder.py
=====================

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
with the catalog column headers

Required packages:
------------------
The required packages are included in the _MDTF_base conda
environment:

- click
- dask
- datetime
- ecgtools
- glob
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
