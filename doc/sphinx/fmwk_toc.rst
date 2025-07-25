Internal code documentation
===========================

.. warning::
   The information in this section only pertains to the development and 
   maintenance of the MDTF framework code. It's not needed for end users to run 
   the package, or for POD developers to develop new diagnostics.


.. Package design
.. --------------

Package code and API documentation
----------------------------------

These sections provide an overview of specific parts of the code that's more higher-level than the module docstrings.

.. toctree::
   :maxdepth: 1

   fmwk_cli
   fmwk_preprocess
   fmwk_utils

Module index
------------

Main framework modules
^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
   src.pod_setup
   src.data_sources
   src.environment_manager
   src.translation
   src.output_manager
   src.preprocessor

Supporting framework modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::

   src.cli
   src.cmip6
   src.data_model
   src.mdtf_info
   src.units
   src.varlist_util
   src.verify_links
   src.xr_parser

Utility modules
^^^^^^^^^^^^^^^

The ``src.util`` subpackage provides non-MDTF-specific utility functionality used many places in the modules above.
See the :doc:`fmwk_utils` documentation for an overview.

.. autosummary::

   src.util.basic
   src.util.dataclass
   src.util.datelabel
   src.util.exceptions
   src.util.filesystem
   src.util.logs
   src.util.path_utils
   src.util.processes
