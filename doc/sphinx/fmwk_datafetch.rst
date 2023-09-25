Data layer: Fetch
=================

This section describes the **Select** and **Fetch** stages of the data request process, implemented in the :doc:`src.data_manager`. See :doc:`fmwk_datasources` for an overview of the process.


.. _ref-datasources-select:

Selection stage
---------------

The purpose of the **Select** stage is to select the minimal amount of data to download which will satisfy the requirements of all the PODs. This logic comes into play when different PODs request the same variable, or when the query results for a single variable include multiple copies of the same data. The latter situation happens frequently in practice: in addition to the example above of the same CMIP6 variable being present in multiple MIP tables, model postprocessing workflows can output the same data in several formats.




Methods called
++++++++++++++


Termination conditions
++++++++++++++++++++++

The logic for handling selection errors differs from the other stages, which operate on individual variables independently. 

.. _ref-datasources-fetch:

Fetch stage
-----------

The purpose of the **Fetch** stage is straightforward: after the **Select** stage has completed, we have an unambiguous list of remote model data we need to transfer. This stage does so, in general by calling third-party library functions.

Methods called
++++++++++++++




Termination conditions
++++++++++++++++++++++