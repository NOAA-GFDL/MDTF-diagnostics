Data layer overview
===================

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

Implementation
++++++++++++++

All current data sources operate in the following distinct **stages**, which are implemented by the :class:`~src.data_manager.DataSourceBase` class. This is a base class which only provides the skeleton for the stages below, leaving details to be implemented by child classes.

0. (**Pre-Query**): in situations where a pre-existing data catalog is not available, construct one "on the fly" by crawling the directories where the data files are stored. This is done once, during the :meth:`~src.data_manager.AbstractDataSource.setup_query` hook that is executed once, before any queries.
1. **Query** the external source for the presence of a variable requested by the POD, done by :meth:`~src.data_manager.DataSourceBase.query_data`;
2. **Select** the specific files (or atomic units of data) to be transferred in order to minimize data movement, done by :meth:`~src.data_manager.DataSourceBase.select_data`;
3. **Fetch** the selected files from the provider's location via some file transfer protocol, downloading them to a local temp directory, done by :meth:`~src.data_manager.DataSourceBase.fetch_data`;
4. **Preprocess** the local copies of data, by converting them from their native format to the format expected by each POD, done by :meth:`~src.data_manager.DataSourceBase.preprocess_data`.

The first stages are described here, while the **Preprocess** stage is described in the :doc:`next section <fmwk_preprocess>`.

Currently all data sources implement the **Query** stage by querying an `intake-esm <https://intake-esm.readthedocs.io/en/latest/>`__ catalog (in a nonstandard way), which is implemented by :class:`~src.data_manager.DataframeQueryDataSourceBase`. In addition, all current data sources also assemble this catalog on the fly, by crawling data files in a regular directory hierarchy and parsing metadata from the file naming convention in a **Pre-Query** stage. This is provided by :class:`~src.data_manager.OnTheFlyDirectoryHierarchyQueryMixin`, which inherits from :class:`~src.data_manager.OnTheFlyFilesystemQueryMixin`. Specific data sources, which correspond to different directory hierarchy naming conventions, inherit from these classes and provide logic describing the file naming convention.

In general, we break the logic up into a hierarchy of multiple classes to make future customization possible without code duplication. Recall that we expect to have many data source child classes, one for each format and location of model data supported by the package, so by moving common logic into parent classes and using inheritance we can enable new child data sources to be added with less new code.

Main loop of the data request process
+++++++++++++++++++++++++++++++++++++

The :class:`~src.data_manager.DataSourceBase` class implements the multi-stage process described above as a while loop to allow for greater flexibility. This is done not only for more robust error handling, but also to implement the alternate variables and preprocessing functionality described above. 

The entry point for the entire process is the :meth:`~src.data_manager.DataSourceBase.request_data` method, which works "backwards" through the stages above. 

Below 



Experiment keys and data keys
+++++++++++++++++++++++++++++





.. _ref-datasources-prequery:

Pre-query stage
---------------

Catalog construction
++++++++++++++++++++

Data sources that inherit from the :class:`~src.data_manager.OnTheFlyFilesystemQueryMixin` class (currently, all of them) construct an intake catalog before any queries are executed. The catalog gets constructed by the :meth:`~src.data_manager.setup_query` method of OnTheFlyFilesystemQueryMixin, which is called once, before any queries take place, as part of the hooks offered by the :class:`~src.data_manager.AbstractDataSource` base class. setup_query calls :meth:`~src.data_manager.generate_catalog]`, as implemented by OnTheFlyDirectoryHierarchyQueryMixin, to crawl the directory and assemble a Pandas DataFrame, which is converted to an intake-esm catalog. 

 Child classes of OnTheFlyDirectoryHierarchyQueryMixin must supply two classes as attributes, ``_FileRegexClass`` and ``_DirectoryRegex``. ``_DirectoryRegex`` is a :class:`~src.util.dataclass.RegexPattern` -- a wrapper around a python regular expression -- which selects the subdirectories to be included in the catalog, based on whether they match the regex. 

 ``_FileRegexClass`` implements parsing paths in the directory hierarchy into usable metadata, and is expected to be a :func:`~src.util.dataclass.regex_dataclass`: the regex_dataclass decorator extends python :py:mod:`dataclasses` to the case where the fields of a dataclass are populated by named capture groups in a regular expression. 

For concreteness, we'll describe how the CMIP6 directory hierarchy (DRS) is implemented by :class:`~src.data_sources.CMIP6LocalFileDataSource`. In this case ``_DirectoryRegex`` is the :func:`~src.cmip6.drs_directory_regex`, matching directories in the CMIP6 DRS, and ``_FileRegexClass`` is :class:`~src.cmip6.CMIP6_DRSPath`, which parses CMIP6 filenames and paths. Individual fields of a regex_dataclass can also be regex_dataclasses (under inheritance), in which case they apply regexes and populate fields of all parent classes as well. This is used in CMIP6_DRSPath, which simply concatenates the fields from :class:`~src.cmip6.CMIP6_DRSDirectory` and :class:`~src.cmip6.CMIP6_DRSFilename`, and so on. This is part of a more general mechanism in which the strings matched by the regex groups are used to instantiate objects of the type in the corresponding field's type annotation, e.g. the CMIP6 ``version_date`` attribute is used to create a :class:`~src.util.datelabel.Date` object. 

The regex_dataclass mechanism is intended to streamline the common aspects of parsing metadata from a string. In addition to the conditions of the regex, arbitrary validation and checking logic can be implemented in the class's ``__post_init__`` method. At the expense of regex syntax, this provides parsing functionality not available in other tools.

Catalog column specifications
+++++++++++++++++++++++++++++

Each field of the ``_FileRegexClass`` dataclass defines a column of the DataFrame which is used as the catalog, and each parseable file encountered in the directory crawl is added to it as a row. Metadata about the columns for a specific data source is provided by a "column specification" object, which inherits from :class:`~src.data_manager.DataframeQueryColumnSpec` and is assigned to the ``col_spec`` attribute of the data source's class. The column spec for the CMIP6 example is [here](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/acc56b638856a2d71e6bf892a8c9e6fd9aca5879/src/data_sources.py#L500-L519).

The ``expt_cols`` attribute of this class is a list of column names whose values must all be the same for two files to be considered to belong to the same experiment. This is needed, e.g., to collect timeseries data chunked by date across multiple files. This is used to define an ["experiment key"](https://github.com/NOAA-GFDL/MDTF-diagnostics/blob/acc56b638856a2d71e6bf892a8c9e6fd9aca5879/src/data_manager.py#L698-L710), which is used to test if two files belong to the same or different experiments. Currently this just concatenates string representations of all the entries in ``expt_cols``.

The ```pod_expt_cols`` and ```var_expt_cols`` attributes of the column spec come into play during the **Select** stage, and are discussed in :ref:`that section <ref-datasources-select>`. Finally, the column spec also identifies the names of the columns containing the path to the file on the remote filesystem (``remote_data_col``) and the column containing the :class:`~src.util.datelabel.DateRange` of data in each file.


.. _ref-datasources-query:

Query stage
-----------

The purpose of the query stage is to locate remote data, if any is present, for each active variable for which this information is unknown. Specifically

Methods called
++++++++++++++

The overarching method for the **Query** stage is the :meth:`~src.data_manager.DataSourceBase.query_data` method of DataSourceBase, which does a query for all active PODs at once. This calls :meth:`~src.data_manager.DataframeQueryDataSourceBase.query_dataset` on the child class (DataframeQueryDataSourceBase), which queries a single variable requested by a POD. The catalog query itself is done in :meth:`~src.data_manager.DataframeQueryDataSourceBase._query_catalog`. Individual conditions of the query are assembled by :meth:`~src.data_manager.DataframeQueryDataSourceBase._query_clause`, except for the clause specifying that data cover the analysis period, which is done first for technical reasons involving the use of comparison operators in object-valued columns. 

By default, \_query_clause assumes the names of columns in the catalog are the same as the corresponding attributes on the :class:`~src.diagnostic.VarlistEntry` object defining the query. This can be changed by defining a class attribute named ``_query_attrs_synonyms``: a dict that will be used to map attributes on the variable to the correct column names. (Translating the *values* in those columns between the naming conventions of the POD's settings file and the naming convention used by the data source is done by :class:`~src.core.VariableTranslator`).

The query is executed by Pandas' `query <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html>`__ method, which returns a DataFrame containing a subset of the catalog's rows. There is no good reason for this, and this should be reimplemented in terms of Intake's `search <https://intake-esm.readthedocs.io/en/latest/api.html#intake_esm.core.esm_datastore.search>`__ method, which is closely equivalent.

The query results are then grouped by values of the "experiment key" (defined above). If a group is not eliminated by :meth:`~src.data_manager.check_group_daterange` or custom logic in :meth:`~src.data_manager._query_group_hook`, it's considered a successful query. A "data key" (an object of the class given in the data source's ``_DataKeyClass`` attribute) corresponding to the result is generated and stored in the ``data`` attribute of the variable being queried.

The **Query** stage is

"Data keys" inherit from :class:`~src.data_manager.DataKeyBase` and are used to associate remote files (or URLs, etc.) with local paths to downloaded data during the Fetch stage. All data sources based on the DataframeQueryDataSourceBase use the :class:`~src.data_manager.DataFrameDataKey`, which identifies files based on their row index in the catalog; the path to the remote file (in ``remote_data_col``) is looked up separately.

Handling failures at the Query stage
++++++++++++++++++++++++++++++++++++




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




