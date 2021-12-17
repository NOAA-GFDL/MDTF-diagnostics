Metadata schema
===============

Overview of functionality
-------------------------

One of the main goals of the project is to enable seamless use of analysis scripts (PODs) on multiple sources of model data. The MDTF package does this by acting as an intermediary between the POD and the source of model data: when PODs are added to the package, they must list the model data they require in their :doc:`settings file <ref_settings>` in a model-agnostic way. The package then translate these pre-existing requirements 

To make this possible, the package requires a *data model*, or more accurately metadata schema, to describe these data requirements.

TBD


Abstract data model
-------------------

Most of these definitions are made in the :doc:`src.data_model`. This code was heavily influenced by 

We did not use this package as a third-party dependency because 1) it predates `xarray <http://xarray.pydata.org/en/stable/>`__, which we use for data processing; 2) despite offering 

TBD


VarlistEntry objects
--------------------
TBD

Variable convention translation
-------------------------------
TBD