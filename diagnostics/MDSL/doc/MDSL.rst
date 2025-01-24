Mean Dynamic Sea Level (MDSL) Package
=====================================
Last Update: 01/24/2025

This POD computes model errors in mean dynamic sea level (MDSL) using an improved aproach called Generalized Tri-Cornered Hat (GTCH). The POD computes MDSL error for alongcoast, regional, and global domains.  

Contact info
------------

- PI: Christopher M. Little (clittle@aer.com), Atmospheric and Environmental Research Inc.
- Current Developer: 
- Contributors: Mengnan Zhao, Sara Vannah, & Nishchitha Etige

Open source copyright agreement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Link the source file of the open source agreement.

Model Data
----------

The package has been successfully teseted for GFDL's CM4 and ESM4 model data and below HighResMIP model output:

ECMWF-IFS-HR_e_hist-1950_vl_r1i1p1f1

In addition the functionality of the POD has been tested successfully for oyher HighResMIP models of CMIP6 outside the MDTF.

Observed/Reference DATA
-----------------------

We use two reference MDSL products from National Center for Space Studies (CNES) and Technical University Denmark (DTU). For the alongcoast MDSL we use tide-gauge data as a reference in addition to the above mentioned reference products. The reference datasets (MDSL and Tide Gaude) are available at ~diagnostics/MDSL/ref_data

Functionality
-------------

.. figure:: ./MDSL_Schematic.png
   :align: center
   :width: 75 %

**Figure 1**: A schematic showing the MDSL diagnostic's functionality.


Required Programing Language and libraries
------------------------------------------
The package was coded in python version 3.12.2

It requires the following packages:
numpy, xarray, matplotlib, pandas, xesmf, os, intake, sys, yaml, 
cartopy.crs, cartopy.features, momlevel, sparse, cf_xarray

The custom functions needed are stored in below files:

~diagnostics/MDSL/gfdl_grid_fx

~diagnostics/MDSL/other_grid_fx

~diagnostics/MDSL/plot_fx

~diagnostics/MDSL/nch

Required input data to the module
---------------------------------
Model output variable - *zos* : sea_surface_height_above_geoid

Model has to be called using a data catalog. We used the MDTF catalog_builder to build
data catalogs for the models that we tested for the package.

Diagnostic Outputs
------------------
The diagnostics provides regional and global MDSL outputs. 

.. figure:: ./gs_output.png
   :align: center
   :width: 75 %

.. figure:: ./global_output.png
   :align: center
   :width: 75 %



References
----------

   .. _1:

1.  

More About the Diagnostic
-------------------------

Explain the outputs of the Diagnostics with example figures.

.. figure:: example.png
   :align: center
   :width: 100 %


