Module Index
============

.. warning::
   The information in this section only pertains to the development and 
   maintenance of the MDTF framework code. It's not needed for end users to run 
   the package, or for POD developers to develop new diagnostics.

Main framework modules
----------------------

.. autosummary::

   src.core
   src.data_manager
   src.data_sources
   src.diagnostic
   src.environment_manager
   src.preprocessor
   src.output_manager

Supporting framework modules
----------------------------

.. autosummary::

   src.cli
   src.cmip6
   src.data_model
   src.mdtf_info
   src.units
   src.verify_links
   src.xr_parser

Utility modules
---------------

The ``src.util`` subpackage provides non-MDTF-specific utility functionality used many places in the modules above. See the :doc:`fmwk_utils` documentation for an overview.

.. autosummary::

   src.util.basic
   src.util.dataclass
   src.util.datelabel
   src.util.exceptions
   src.util.filesystem
   src.util.logs
   src.util.processes

Unused modules
--------------

The following modules implement features moved to, or intended for, future releases. They can be removed from the current production branch with no effect.

.. autosummary::

   src.conflict_resolution
   src.install