Data layer overview
-------------------

The simplest description is that the framework is doing a database query: based 
on the user's input, the framework sets up a search interface for the model data. 
(The model for this "search interface" is nothing more elaborate than the 
search functionality on most data catalogs, e.g. the `ESGF catalog 
<https://esgf-node.llnl.gov/search/cmip6/>`__ of CMIP6 data.)
The PODs describe what data they need in their settings files: if the search is
successful and the data is available, the framework downloads the data for the 
POD; if not, we log an error and the POD can't run.

This simple picture gets complicated because we also implement the following 
functionality that provides more flexibility in the data search process. By 
shifting the following responsibilities from the user to the framework, we get a
piece of software that's more usable in practice, at the expense of code 
complexity.

- PODs can be flexible in what data they accept by specifying **alternate 
  variables**, to be used as a "fallback" or "plan B" if a variable isn't present
  in the model output. (Implementing and testing code that handles both cases is
  entirely the POD's responsibility.)
- The framework has a **data preprocessing** step which can do a limited set of
  transformations on data (in addition to changing its format), eg. extracting a
  vertical level from 4D data. If a POD only requires data on a single level, the
  framework can 
- We allow for **optional settings** in the model data specification, which fall
  into several classes. Using CMIP6 as an example:
   - The values of some model data settings might be uniquely determined by 
     others: eg, if the user wants to analyze data from the CESM2 model, setting 
     ``source_id`` to CESM2 means ``institution_id`` must be NCAR. The user 
     shouldn't need to supply both settings.
   - Some settings for the data source may be irrelevant for the user's purposes.
     Eg, (mean) surface air pressure at monthly frequency is provided in the 
     ``Amon``, ``cfMon`` and ``Emon`` MIP tables, but not the other monthly 
     tables. Since the user isn't running a MIP but only cares about obtaining 
     that variable's data, they shouldn't need to look up which MIP table 
     contains the variable they want.
   - Finally, in some use cases the user may be willing to have the framework 
     infer settings on their behalf. Eg, if the user is doing initial exploratory 
     data analysis, they probably want the ``revision_date`` to be the most recent
     version available for that models' data, without having to look up what that 
     date is. Of course, the user may *not* want this (eg, for reproducing an 
     earlier analysis), so this functionality can be controlled with the ``XXX`` 
     command-line option.


Data layer walkthrough
======================

We find it easiest to explain the data layer's implementation in terms of a 
walkthrough, or "script," describing the actions taken by each of the components
during a run of the framework.

Components (classes)
^^^^^^^^^^^^^^^^^^^^

- DataManager: the part of the framework supervising the "local" data handling.


- DataSource: the part of the framework describing the "remote" data. Unlike the 
  DataManager, there will be many DataSource subclasses: one for each type of 
  data source the framework can use.

  - 

Walkthrough
^^^^^^^^^^^

The first step is to instantiate the classes above. The user will have requested
that some subset of available PODs should be run; after being initialized, the
DataManager initializes these POD objects from the data in their settings files.
The PODs, in turn, initialize VarlistEntry objects.

