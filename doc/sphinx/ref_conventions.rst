.. _ref-data-conventions:

Conventions for variable names and units
----------------------------------------

The use of data source plug-ins, as described in :doc:`ref_data_sources`, is how we let the package obtain data files by different methods, but doesn't address problems arising from differing content of these files. For example, the name for total precipitation used by NCAR models is ``PRECT`` and is given as a rate (meters per second), while the name for the same physical quantity in GFDL models is ``precip``, given in units of a flux (kg m\ :sup:`-2`\  s\ :sup:`-1`\ ).

Frequently a data source (in the sense described above) will only identify a variable through this "native" name, which makes it necessary to tell the package which "language to speak" when searching for different variables. Setting the ``--convention`` flag translates the data request for each POD into the variable naming convention used by the model that's being analyzed. 

This feature also provides a mechanism to deal with missing metadata, and to warn the user that the metadata for a specific file may be inaccurate: before any PODs are run, the framework examines each file and converts the name and units of each variable to the values that the POD has requested. 

Recognized conventions
++++++++++++++++++++++

Naming conventions are specified with the ``--convention`` flag. The currently implemented naming conventions are:

* ``CMIP``: Variable names and units as used in the `CMIP6 <https://www.wcrp-climate.org/wgcm-cmip/wgcm-cmip6>`__ `data request <https://doi.org/10.5194/gmd-2019-219>`__. There is a `web interface <http://clipc-services.ceda.ac.uk/dreq/index.html>`__ to the request. Data from any model that has been `published <https://esgf-node.llnl.gov/projects/cmip6/>`__ as part of CMIP6, or processed with the `CMOR3 <https://cmor.llnl.gov/>`__ tool, should follow this convention.

* ``NCAR``: Variable names and units used in the default output of models developed at the `National Center for Atmospheric Research <https://ncar.ucar.edu>`__ (NCAR), headquartered in Boulder, CO, USA. Recognized synonyms for this convention: ``CAM4``, ``CESM``, ``CESM2``.

* ``GFDL``: Variable names and units used in the default output of models developed at the `Geophysical Fluid Dynamics Laboratory <https://www.gfdl.noaa.gov/>`__ (GFDL), Princeton, NJ, USA. Recognized synonyms for this convention: ``AM4``, ``CM4``, ``ESM4``, ``SPEAR``.

* ``None``: This setting disables the variable translation functionality. Variable names and units are taken to be what's requested by each POD, and the user must take responsibility for any needed renaming or unit conversion.

If you would like the package to support a naming convention that hasn't currently been implemented, please make a request in the appropriate GitHub `discussion thread <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/174>`__.

Working with unimplemented conventions
++++++++++++++++++++++++++++++++++++++

The framework has a number of options for handling data that doesn't follow one of the recognized naming conventions described above. All of them involve more manual effort on the part of the user.

- The third-party `CMOR <https://cmor.llnl.gov/>`__ tool exists to convert model output into the ``CMIP`` convention.
- `NCO <http://nco.sourceforge.net/>`__, `CDO <https://code.mpimet.mpg.de/projects/cdo>`__ and other utilities provide command-line functionality for renaming variables, unit conversion, editing metadata, etc.
- As mentioned above, ``--convention=None`` turns off the variable translation functionality. The user is then responsible for ensuring that input model data has the variable names and units expected by each POD.
- The :ref:`explicit file data source<ref-data-source-explictfile>` allows the user to manually specify a set of files to use for a given variable, which will be renamed accordingly. It also provides the ability to overwrite existing metadata attributes.
- Finally, the ``--disable-preprocessor`` flag skips all unit conversion and checking associated with model metadata. The user is then responsible for ensuring that input model data has the variable names and units expected by each POD.

If using any of the above methods, please carefully consult the documentation for what data is needed by each POD. Note that we do not require POD developers to use any variable naming convention or set of units, so different PODs may request data in mutually inconsistent conventions (e.g., precipitation as a rate vs. as a flux).
