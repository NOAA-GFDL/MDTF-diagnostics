Data layer: Query
=================

This section describes the **Query** stage of the data request process, implemented in the :doc:`src.data_manager`. See :doc:`fmwk_datasources` for an overview of the process.

Overview
--------

Currently all data sources implement the **Query** stage by querying an `intake-esm <https://intake-esm.readthedocs.io/en/latest/>`__ catalog (in a nonstandard way), which is implemented by :class:`~src.data_manager.DataframeQueryDataSourceBase`. In addition, all current data sources also assemble this catalog on the fly, by crawling data files in a regular directory hierarchy and parsing metadata from the file naming convention in a **Pre-Query** stage. This is provided by :class:`~src.data_manager.OnTheFlyDirectoryHierarchyQueryMixin`, which inherits from :class:`~src.data_manager.OnTheFlyFilesystemQueryMixin`. The **Pre-Query** stage is done once, during the :meth:`~src.data_manager.AbstractDataSource.setup_query` hook that is executed before any queries.

Specific data sources, which correspond to different directory hierarchy naming conventions, inherit from these classes and provide logic describing the file naming convention.

.. _ref-datasources-prequery:

Pre-query stage
---------------

The purpose of the **Pre-Query** stage is to perform any setup tasks that only need to be done once in order to enable data queries. As described above, current data sources crawl a directory to construct a catalog on the fly, but other sources could use this stage to open a connection to a remote database, etc.

Catalog construction
++++++++++++++++++++

Data sources that inherit from the :class:`~src.data_manager.OnTheFlyFilesystemQueryMixin` class (currently, all of them) construct an intake catalog before any queries are executed. The catalog gets constructed by the :meth:`~src.data_manager.setup_query` method of OnTheFlyFilesystemQueryMixin, which is called once, before any queries take place, as part of the hooks offered by the :class:`~src.data_manager.AbstractDataSource` base class. setup_query calls :meth:`~src.data_manager.generate_catalog`, as implemented by OnTheFlyDirectoryHierarchyQueryMixin, to crawl the directory and assemble a Pandas DataFrame, which is converted to an `intake-esm <https://intake-esm.readthedocs.io/en/latest/>`__ catalog. 

 Child classes of OnTheFlyDirectoryHierarchyQueryMixin must supply two classes as attributes, ``_FileRegexClass`` and ``_DirectoryRegex``. ``_DirectoryRegex`` is a :class:`~src.util.dataclass.RegexPattern` -- a wrapper around a python regular expression -- which selects the subdirectories to be included in the catalog, based on whether they match the regex. 

 ``_FileRegexClass`` implements parsing paths in the directory hierarchy into usable metadata, and is expected to be a :func:`~src.util.dataclass.regex_dataclass`: the regex_dataclass decorator extends python :py:mod:`dataclasses` to the case where the fields of a dataclass are populated by named capture groups in a regular expression. 

For concreteness, we'll describe how the CMIP6 directory hierarchy (DRS) is implemented by :class:`~src.data_sources.CMIP6LocalFileDataSource`. In this case ``_DirectoryRegex`` is the :func:`~src.cmip6.drs_directory_regex`, matching directories in the CMIP6 DRS, and ``_FileRegexClass`` is :class:`~src.cmip6.CMIP6_DRSPath`, which parses CMIP6 filenames and paths. Individual fields of a regex_dataclass can also be regex_dataclasses (under inheritance), in which case they apply regexes and populate fields of all parent classes as well. This is used in CMIP6_DRSPath, which simply concatenates the fields from :class:`~src.cmip6.CMIP6_DRSDirectory` and :class:`~src.cmip6.CMIP6_DRSFilename`, and so on. This is part of a more general mechanism in which the strings matched by the regex groups are used to instantiate objects of the type in the corresponding field's type annotation, e.g. the CMIP6 ``version_date`` attribute is used to create a :class:`~src.util.datelabel.Date` object. 

The regex_dataclass mechanism is intended to streamline the common aspects of parsing metadata from a string. In addition to the conditions of the regex, arbitrary validation and checking logic can be implemented in the class's ``__post_init__`` method. At the expense of regex syntax, this provides parsing functionality not available in other tools.

Catalog column specifications
+++++++++++++++++++++++++++++

Each field of the ``_FileRegexClass`` dataclass defines a column of the DataFrame which is used as the catalog, and each parseable file encountered in the directory crawl is added to it as a row. Metadata about the columns for a specific data source is provided by a "column specification" object, which inherits from :class:`~src.data_manager.DataframeQueryColumnSpec` and is assigned to the ``col_spec`` attribute of the data source's class.

The ``expt_cols`` attribute of this class is a list of column names whose values must all be the same for two files to be considered to belong to the same experiment. This is needed, e.g., to collect timeseries data chunked by date across multiple files. This is used to define an "experiment key", which is used to test if two files belong to the same or different experiments. Currently this just concatenates string representations of all the entries in ``expt_cols``.

The ```pod_expt_cols`` and ```var_expt_cols`` attributes of the column spec come into play during the **Select** stage, and are discussed in :ref:`that section <ref-datasources-select>`. Finally, the column spec also identifies the names of the columns containing the path to the file on the remote filesystem (``remote_data_col``) and the column containing the :class:`~src.util.datelabel.DateRange` of data in each file.


.. _ref-datasources-query:

Query stage
-----------

The purpose of the **Query** stage is to locate remote data, if any is present, for each active variable for which this information is unknown.

Methods called
++++++++++++++

The overarching method for the **Query** stage is the :meth:`~src.data_manager.DataSourceBase.query_data` method of DataSourceBase, which does a query for all active PODs at once. This calls :meth:`~src.data_manager.DataframeQueryDataSourceBase.query_dataset` on the child class (DataframeQueryDataSourceBase), which queries a single variable requested by a POD. The catalog query itself is done in :meth:`~src.data_manager.DataframeQueryDataSourceBase._query_catalog`. Individual conditions of the query are assembled by :meth:`~src.data_manager.DataframeQueryDataSourceBase._query_clause`, except for the clause specifying that data cover the analysis period, which is done first for technical reasons involving the use of comparison operators in object-valued columns. 

By default, \_query_clause assumes the names of columns in the catalog are the same as the corresponding attributes on the :class:`~src.diagnostic.VarlistEntry` object defining the query. This can be changed by defining a class attribute named ``_query_attrs_synonyms``: a dict that will be used to map attributes on the variable to the correct column names. (Translating the *values* in those columns between the naming conventions of the POD's settings file and the naming convention used by the data source is done by :class:`~src.core.VariableTranslator`).

The query is executed by Pandas' `query <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html>`__ method, which returns a DataFrame containing a subset of the catalog's rows. There is no good reason for this, and this should be reimplemented in terms of Intake's `search <https://intake-esm.readthedocs.io/en/latest/api.html#intake_esm.core.esm_datastore.search>`__ method, which is closely equivalent.

The query results are then grouped by values of the "experiment key" (defined :ref:`above <ref-datasources-keys>`). If a group is not eliminated by :meth:`~src.data_manager.check_group_daterange` or custom logic in :meth:`~src.data_manager._query_group_hook`, it's considered a successful query. A "data key" (an object of the class given in the data source's ``_DataKeyClass`` attribute) corresponding to the result is generated and stored in the ``data`` attribute of the variable being queried. Specifically, the ``data`` attribute is a dict mapping experiment keys to data keys.

"Data keys" inherit from :class:`~src.data_manager.DataKeyBase` and are used to associate remote files (or URLs, etc.) with local paths to downloaded data during the Fetch stage. All data sources based on the DataframeQueryDataSourceBase use the :class:`~src.data_manager.DataFrameDataKey`, which identifies files based on their row index in the catalog; the path to the remote file (in ``remote_data_col``) is looked up separately.

Termination conditions
++++++++++++++++++++++

The **Query** stage operates in "batch mode," executing queries for all active variables (VarlistEntry objects with ``status`` = ACTIVE) which have not already been queried (``stage`` attribute < QUERIED enum value). A successful query is one that returns a nonempty result from the catalog, which causes its ``stage`` to be updated to QUERIED and the VarlistEntry to be removed from the batch. Unsuccessful queries result in the deactivation of the variable and the activation of its alternates, as described :ref:`above <ref-datasources-varlist>`. These alternates will be included in the batch when it's recalculated (unless they've already been queried as a result of being an alternate for another variable as well.)

The **Query** stage terminates when the batch of variables to query is empty (or when the batch-query process repeats more than a maximum number of times, to guard against infinite loops.) Recall, though, that because of the structure of the query-fetch-preprocess loop, the **Query** stage may execute multiple times with batches of different variables. 
