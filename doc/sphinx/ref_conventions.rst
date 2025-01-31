.. _ref-data-conventions:

Recognized conventions
++++++++++++++++++++++

Naming conventions are specified with the ``convention`` parameter. The currently implemented naming conventions are:

* ``CMIP``: Variable names and units as used in the `CMIP6 <https://www.wcrp-climate.org/wgcm-cmip/wgcm-cmip6>`__
`data request <https://doi.org/10.5194/gmd-2019-219>`__. There is a
`web interface <http://clipc-services.ceda.ac.uk/dreq/index.html>`__ to the request. Data from any model that ha
s been `published <https://esgf-node.llnl.gov/projects/cmip6/>`__ as part of CMIP6, or processed with the
`CMOR3 <https://cmor.llnl.gov/>`__ tool, should follow this convention.

* ``CESM``: Variable names and units used in the default output of models developed at the
`National Center for Atmospheric Research <https://ncar.ucar.edu>`__ (NCAR), headquartered in Boulder, CO, USA.
Recognized synonyms for this convention: ``CAM4``, ``CESM``, ``CESM2``.

* ``GFDL``: Variable names and units used in the default output of models developed at the
`Geophysical Fluid Dynamics Laboratory <https://www.gfdl.noaa.gov/>`__ (GFDL), Princeton, NJ, USA. Recognized synonyms
for this convention: ``AM4``, ``CM4``, ``ESM4``, ``SPEAR``.

If you would like the package to support a naming convention that hasn't currently been implemented, please make a
request in the appropriate GitHub `discussion thread <https://github.com/NOAA-GFDL/MDTF-diagnostics/discussions/174>`__.

Working with unimplemented conventions
++++++++++++++++++++++++++++++++++++++

The framework has a number of options for handling data that doesn't follow one of the recognized naming conventions
described above. All of them involve more manual effort on the part of the user.

- The third-party `CMOR <https://cmor.llnl.gov/>`__ tool exists to convert model output into the ``CMIP`` convention.
- `NCO <http://nco.sourceforge.net/>`__, `CDO <https://code.mpimet.mpg.de/projects/cdo>`__ and other utilities provide
  command-line functionality for renaming variables, unit conversion, editing metadata, etc.
- As mentioned in :ref:`the cli documentation<ref-cli>`, setting ``translate_data`` to `false` in the runtime
  configuration file turns off the variable translation functionality. The user is then
  responsible for ensuring that input model data has the variable names and units expected by each POD.
- Finally, setting ``run_pp`` to `false` will disable all unit conversion and checking associated with model metadata.
  The user is then responsible for ensuring that input model data has the variable names and units expected by each POD.

If using any of the above methods, please carefully consult the documentation for what data is needed by each POD. Note
that we do not require POD developers to use standard variable names or set of units, so different PODs may
request data in mutually inconsistent conventions (e.g., precipitation as a rate vs. as a flux).
