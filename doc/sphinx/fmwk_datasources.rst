Data layer: Overview
====================

This section describes the :doc:`src.data_manager`, which implements general (base class) functionality for how the package finds and downloads model data requested by the PODs. It also describes some aspects of the :doc:`src.data_sources`, which contains the child class implementations of these methods that are selectable by the user through the ``--data-manager`` flag.

In the code (and this document), the terms "data manager" and "data source" are used interchangeably to refer to this functionality. In the future, this should be standardized on "data source," to avoid user confusion.

Overview
--------

Functionality
+++++++++++++

One of the major goals of the MDTF package is to allow PODs to analyze data from a wide range of sources and formats without rewriting. This is done by having PODs specify their :doc:`data requirements <ref_settings>`) in a model-agnostic way (see :doc:`fmwk_datamodel`, and providing separate :doc:`data source <ref_data_sources>`) "plug-ins" that implement the details of the data query and transfer for each source of model data supported by the package.

At a high level, the job of a data source plug-in is simple. The PODs' data request gets translated into the native format (variable naming convention, etc.) of the data source by the :class:`~src.core.VariableTranslator`). The plug-in does a search for each variable requested by each POD: if the search is successful and the data is available, the plug-in downloads the data for the POD; if not, we log an error and the POD can't run.

This simple picture gets complicated because we also implement the following functionality that provides more flexibility in the data search process. By shifting the following responsibilities from the user to the framework, we get a piece of software that's more usable in practice.

- PODs can be flexible in what data they accept by specifying *alternate variables*, to be used as a "fallback" or "plan B" if a variable isn't present in the model output. (Implementing and testing code that handles both cases is entirely the POD's responsibility.)
- Downloading is structured to *minimize data movement*: if multiple PODs request the same variable, only one copy of the remote files will be downloaded. If a time series is chunked across multiple files, only the files corresponding to the analysis period will be downloaded.
- The framework has a *data preprocessing* step which can do a limited set of transformations on data (in addition to changing its format), eg. automatically extracting a vertical level from 3D data.
- We allow for *optional settings* in the model data specification, which fall into several classes. Using CMIP6 as an example:

  - The values of some model data settings might be uniquely determined by others: eg, if the user wants to analyze data from the CESM2 model, setting ``source_id`` to CESM2 means ``institution_id`` must be NCAR. The user shouldn't need to supply both settings.
  - Some settings for the data source may be irrelevant for the user's purposes. E.g., (mean) surface air pressure at monthly frequency is provided in the ``Amon``, ``cfMon`` and ``Emon`` MIP tables, but not the other monthly tables. Since the user isn't running a MIP but only cares about obtaining that variable's data, they shouldn't need to look up which MIP table contains the variable they want.
  - Finally, in some use cases the user may be willing to have the framework infer settings on their behalf. E.g., if the user is doing initial exploratory data analysis, they probably want the ``revision_date`` to be the most recent version available for that model's data, without having to look up what that date is. Of course, the user may *not* want this (eg, for reproducing an earlier analysis), so this functionality can be controlled with the ``--strict`` command-line option or by explicitly setting the desired ``revision_date``.

In general, we break the logic up into a hierarchy of multiple classes to make future customization possible without code duplication. Recall that we expect to have many data source child classes, one for each format and location of model data supported by the package, so by moving common logic into parent classes and using inheritance we can enable new child data sources to be added with less new code.

.. _ref-datasources-mainloop:

"Query-fetch-preprocess" main loop
++++++++++++++++++++++++++++++++++

All current data sources operate in the following distinct **stages**, which are described by the :class:`~src.data_manager.DataSourceBase` class. This is a base class which only provides the skeleton for the stages below, leaving details to be implemented by child classes. The entry point for the entire process is the :meth:`~src.data_manager.DataSourceBase.request_data` method, which works "backwards" through the following stages:

0. (**Pre-Query**): in situations where a pre-existing data catalog is not available, construct one "on the fly" by crawling the directories where the data files are stored. This is done once, during the :meth:`~src.data_manager.AbstractDataSource.setup_query` hook that is executed before any queries.
1. **Query** the external source for the presence of variables requested by the PODs, done by :meth:`~src.data_manager.DataSourceBase.query_data`;
2. **Select** the specific files (or atomic units of data) to be transferred in order to minimize data movement, done by :meth:`~src.data_manager.DataSourceBase.select_data`;
3. **Fetch** the selected files from the provider's location via some file transfer protocol, downloading them to a local temp directory, done by :meth:`~src.data_manager.DataSourceBase.fetch_data`;
4. **Preprocess** the local copies of data, by converting them from their native format to the format expected by each POD, done by :meth:`~src.data_manager.DataSourceBase.preprocess_data`.

Due to length, each of the stages is described in subsequent sections. The **Pre-Query** and **Query** stages are described in :doc:`fmwk_dataquery`, the **Select** and **Fetch** stages are described in :doc:`fmwk_datafetch`, and the **Preprocess** stage is described in :doc:`fmwk_preprocess`.

Although the stages are described as a linear progression above, when we incorporate error handling the process becomes a do-while loop. We mentioned that the stages (other than the **Pre-Query** setup) are executed backwards: first **Preprocess** is called, but it discovers it doesn't have any locally downloaded files to preprocess, so it calls **Fetch**, which discovers it doesn't know which files to download, etc. The loop is organized in this "backwards" fashion to make error handling more straightforward, especially since variables (and their alternates, see next section) are processed in a batch. 

There are many situations in which processing of a variable may fail at a given stage: a query may return zero results, a file transfer may be interrupted, or the data may have mis-labeled metadata. The general pattern for handling such a failure is to look for alternate representations for that variable, and start processing them from the beginning of the loop. 

.. _ref-datasources-varlist:

VarlistEntries as input
+++++++++++++++++++++++

The job of the data source is to obtain model data requested by the PODs from an experiment selected by the user at runtime. The way PODs request data is through a declaration in their :doc:`settings file <ref_settings>`, which is used to define :class:`~src.diagnostic.VarlistEntry` objects. These objects, along with the user's experiment selection, are the input to the data source. We summarize relevant attributes of the VarlistEntry objects here.

Each VarlistEntry object has a ``stage`` attribute, taking values in the :class:`~src.diagnostic.VarlistEntryStage` enum, which tracks the last stage of the loop that the variable has successfully completed. In addition, its ``status`` attribute is also relevant: only variables that have ACTIVE status are progressed through the pipeline; when a failure occurs on a variable, it's deactivated (via :meth:`~src.core.MDTFObjectBase.deactivate`) and its alternates are activated.

As part of the :meth:`~src.data_manager.setup` process (:meth:`~src.data_manager.setup_var`), model-agnostic information in each VarlistEntry object is translated into the naming convention used by the model. This is stored in a :class:`~src.core.TranslatedVarlistEntry` object, in the ``translation`` attribute of the corresponding VarlistEntry. These form the main input to the **Preprocess** stage, as described below.

Finally, the ``alternates`` attribute is central to how errors are handled during the data request process. Each variable (VarlistEntry) can optionally specify one or more alternate, or "backup" variables, as a list of other VarlistEntry objects stored in this attribute. These variables can specify their own alternates, etc., so that a single "data request" corresponding to a single logical variable is implemented as a *linked list* of VarlistEntry objects. 

The data source traverses this list in breadth-first order until data corresponding to a viable set of alternates is fully processed (makes it through all the stages): if the data specified by one VarlistEntry isn't available, we try its alternates (if it has any), and if one of those isn't found, we try its alternates, and so on. 

.. _ref-datasources-keys:

Experiment keys and data keys
+++++++++++++++++++++++++++++

The final pieces of terminology we need to introduce are "*experiment keys*" and "*data keys*". These are most relevant in the **Select** stage.

From the point of view of the MDTF package, an *experiment* is any collection of datasets that are "compatible," in that having a POD analyze the datasets together will produce a result that's sensible to look at. It makes no sense to feed variables from different CO2 forcings into a POD (unless that's part of that POD's purpose), but it may make sense to use variables from different model runs if forcings and other conditions are identical.

As described above, a data source is a python class that provides an interface to obtain data from many different experiments (stored in the same way). The class uniquely distinguishes different experiments by defining values in a set of "experiment attributes". Likewise, the results of a single experiment will comprise multiple variables and physical files, which are described by "data attributes" -- think of columns in a data catalog. Because each unit of data is associated with one experiment, the set of experiment attributes is a subset of the set of data attributes.

"Data keys" and "experiment keys," then, are objects that store or refer to these attributes for purposes of implementing the query, and are in one-to-one correspondence with units of data and experiments. In particular, the results of the query for one variable are stored in a dict on its ``data`` attribute, mapping experiment keys to data keys found by the query.

We spell this out in detail because this is our mechanism for enabling flexible and intelligent queries, as described in the overview section. In particular, we *don't* require that the user explicitly provide values for all experiment attributes at runtime: the job of the **Select** stage is to select an experiment key consistent with all data keys that have been found by the preceding **Query** stage.
