Data layer: Fetch
=================

This section describes the **Select** and **Fetch** stages of the data request process, implemented in the :doc:`src.data_manager`.


.. _ref-datasources-select:

Selection stage
---------------

The purpose of the **Select** stage is to select the minimal amount of data to download which will satisfy the requirements of all the PODs. This logic comes into play when different PODs request the same variable, or when the query results for a single variable include multiple copies of the same data. The latter situation happens frequently in practice: in addition to the example above of the same variable being present in multiple MIP tables, model postprocessing workflows can output the same data in several formats.


Methods called
++++++++++++++


Handling failures at the Select stage
+++++++++++++++++++++++++++++++++++++

The logic for handling selection errors differs from the other stages, which operate on individual variables independently. 

.. _ref-datasources-fetch:

Fetch stage
-----------

Methods called
++++++++++++++



Handling failures at the Fetch stage
++++++++++++++++++++++++++++++++++++