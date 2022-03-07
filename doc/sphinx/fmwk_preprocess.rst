Data layer: Preprocessing
=========================

This section describes the :doc:`src.preprocessor`, responsible for converting model data into the format requested by PODs, and the :doc:`src.xr_parser`, responsible for "cleaning" model metadata beforehand. These implement the **Preprocess** stage of the data request; see :doc:`fmwk_datasources` for an overview.

Overview
--------

Functionality
+++++++++++++

The preprocessor is responsible for the final stage of the "query-fetch-preprocess" loop described in the :doc:`previous section <fmwk_datasources>`. By the time it's called, the needed model data has been found and locally downloaded by the previous stages of the loop -- otherwise, an error is logged and execution skips downstream stages. The job of the preprocessor is then to convert the downloaded model data from the model's native format into the format expected by each POD: this is why we use the term "preprocessor," because it operates on model data before the PODs see it.

In full generality, this is a very difficult task: the "format" could refer to any aspect of the model data. Other groups have gone so far as to refer to it as the "holy grail" of portable model analyses, describing it as "`CMORization on the fly <https://docs.esmvaltool.org/en/latest/develop/dataset.html>`__" (recall that the `CMOR <https://cmor.llnl.gov/>`__ tool standardizes model output for CMIP publication; it must be customized for each model convention, and many cases exist where CMIP published data hasn't been perfectly standardized across centers.)

Rather than tackle the full problem at once, we've implemented the preprocessor in a modular way in order to add functionality incrementally, as it's needed by PODs and data sources supported by the package. We break the general "format conversion" problem down into a sequence of individual *transformations* that operate on a single aspect of the data, converting that aspect from what's present in the downloaded data to what's requested by the POD (as described in its settings file and :class:`~src.diagnostic.VarlistEntry` objects). When called, the preprocessor simply executes each transformation in order. 

The available transformations in the preprocessor also "feed back" into the **Query** stage of the "query-fetch-preprocess" loop. :ref:`Recall <ref-datasources-query>` that, in order to make the package useful for exploratory analysis, we've implemented the **Query** stage to be as flexible and permissive as possible. One consequence of this is that, if the preprocessor has a transformation that converts some aspect *A* of the data from state *a1* to *a2*, this means that all PODs can make use of model data having *A = a1* equally well as data with *A = a2*. This means the **Query** stage should look for data with both values of *A*; if a POD author has specified *A = a1* in their POD's settings file, the data query should be enlarged to include *A = a2*, and the responsibility for doing so should most naturally lie with the transformation that converts *a1* to *a2*. We implement this by letting each transformation edit the linked list of data queries.

Implementation
++++++++++++++

Each preprocessor is a class inheriting from :class:`~src.preprocessor.MDTFPreprocessorBase`; a specific child class is associated with each data source via the ``_PreprocessorClass`` attribute on :class:`~src.data_manager.DataSourceBase` (and all child classes). This lets us handle the case where a specific source of data might require special preprocessing, even though currently all data sources use the :class:`~src.preprocessor.DefaultPreprocessor` class. For example, the methods to open and write the dataset are currently implemented in :class:`~src.data_manager.DataSourceBase`; a data source that provided model data in zarr format instead of netCDF would require a new preprocessor class that overrode those methods.

To accomplish the goals above, the preprocessor is structured as a miniature data pipeline. The inputs to the pipeline are the xarray `Dataset <http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html>`__ containing the downloaded data, and the :class:`~src.diagnostic.VarlistEntry` object from the POD describing the requested format for that data. The preprocessor operates on the Dataset to bring it in line with the information in the VarlistEntry; if it encounters a problem (e.g. the metadata can't be parsed) that's treated as an error causing the "query-fetch-preprocess" loop to look for possible alternate data.

As noted above, the preprocessor has *two* roles: converting the downloaded model data to the format requested by the PODs, and enlarging the scope of the data query to include all formats it's capable of converting between. The latter is executed before the former:

- The datasource creates an instance of its designated ``_PreprocessorClass`` for each POD in :meth:`~src.data_manager.DataSourceBase.setup_pod`; this object is stored in the ``preprocessor`` attribute of the :class:`~src.diagnostic.Diagnostic` object. Even though the data conversion operates on individual variables, the "scope" of the preprocessor is POD-wide because it needs to edit the data request for the POD as a whole. 
- This is done by the preprocessor's :meth:`~src.preprocessor.MDTFPreprocessorBase.edit_request` method, called immediately after the preprocessor is initialized. 

  - Logic to enlarge the data query, as specified in the linked list of alternate VarlistEntries for the POD, is handled by the edit_request() method on each transformation, as specified by :class:`~src.preprocessor.PreprocessorFunctionBase`.

After this is done, the "query-fetch-preprocess" loop begins and the edited data queries are executed. The second role takes place at the end of the loop, after the data has been downloaded:

- For every successfully downloaded variable, the :meth:`~src.data_manager.DataSourceBase.preprocess_data` method of the data source calls the :meth:`~src.preprocessor.MDTFPreprocessorBase.process` method on the POD's preprocessor object that was previously created.

  - This begins by loading the download variable into an xarray Dataset (:meth:`~src.preprocessor.MDTFPreprocessorBase.load_ds`). The location of the downloaded files is taken from the ``local_data`` attribute of the VarlistEntry object corresponding to the variable.
  - The metadata of the Dataset is standardized by the :ref:`metadata parser <ref-preprocessor-parser>`, implemented by :class:`~src.xr_parser.DefaultDatasetParser`. As described below, this logic is arguably as important as the contents of the preprocessor itself, as it has the responsibility of "defending" against malformed and mis-specified model metadata.
  - The process() method on each transformation is called in a fixed order (:meth:`~src.preprocessor.MDTFPreprocessorBase.process_ds`). 
  - The transformed Dataset is written out to a netCDF file (:meth:`~src.preprocessor.MDTFPreprocessorBase.write_ds`). 

    - We need to do some extra munging of the output metadata, in :meth:`~src.preprocessor.MDTFPreprocessorBase.clean_output_attrs`. This handles technicalities due to xarray's methods not being fully CF-compliant, etc. 
    - For provenance, we also update the ``history`` netCDF attribute on the output data files to document all the transformations done by the preprocessor. This is done in :meth:`~src.preprocessor.MDTFPreprocessorBase.log_history_attr`, which makes use of the variable-specific logging.

These aspects are described in more detail below.

.. _ref-preprocessor-parser:

Xarray metadata parser
----------------------

Overview
++++++++

The job of the metadata parser is to standardize the metadata and other attributes of model data files immediately after they're opened. The goal is for all needed standardization, data validation and other checks to be performed here, so that the logic in the preprocessor transformations can safely make assumptions about the structure of the dataset they operate on, rather than requiring each transformations to code and test for every case it may encounter, which would involve lots of redundant logic.

Like the preprocessor, the parser is implemented as a class so that the functionality can be customized by data sources with different needs, although currently all data sources use the :class:`~src.xr_parser.DefaultDatasetParser`. The preprocessor class to use is specified as the ``_PreprocessorClass`` attribute on the data source.

Functionality in the parser resists organization, since it needs to be updated to handle every special case of metadata convention encountered in the wild. Broadly speaking, though, the methods are organized into the following stages: 

- **Normalize** metadata on the downloaded data: convert equivalent ways to specify a piece of metadata to a single canonical representation.
- **Reconcile** the metadata with what the POD expects. Recall that each VarlistEntry is converted to a :class:`~src.core.TranslatedVarlistEntry`, expressing the variable in the model's native convention. In this stage, we check that the variable we *expected* to download, as expressed in the TranslatedVarlistEntry, matches what was *actually* downloaded. If there are differences, we update either the data's metadata or the TranslatedVarlistEntry, or raise an error.
- **Check** metadata admissibility before exiting, raising errors if necessary. It's conceptually simpler to write these tests as a separate stage that covers everything than to integrate the tests piecemeal into the previous two stages.

Method names in the parser follow this convention. 


Methods called
++++++++++++++

The parser has one public method, :meth:`~src.xr_parser.parse`, which is the entry point for all functionality. It calls the following methods:

- :meth:`~src.xr_parser.normalize_pre_decode` strips leading/trailing whitespace and does other proofreading on the raw xarray attributes. It also makes a copy of the raw attributes, since they can be overwritten by the next two methods.
- `xarray's <http://xarray.pydata.org/en/stable/index.html>`__ own `decode_cf() <http://xarray.pydata.org/en/stable/generated/xarray.decode_cf.html>`__ method, which primarily decodes the time coordinate to `cftime.datetime <https://unidata.github.io/cftime/api.html#cftime.datetime>`__ objects, which are properly calendar-aware.
- `cf\_xarray's <https://cf-xarray.readthedocs.io/en/latest/index.html>`__ `guess_coord_axis() <https://cf-xarray.readthedocs.io/en/latest/generated/xarray.DataArray.cf.guess_coord_axis.html#xarray.DataArray.cf.guess_coord_axis>`__ method, which uses heuristics to assign axis labels ('X', 'Y', 'Z', 'T') to dataset coordinates. This is important, since we need a way to handle the data's coordinates that doesn't depend on the model's naming conventions and coordinate system.
- :meth:`~src.xr_parser.restore_attrs_backup` corrects any metadata that was overwritten.
- :meth:`~src.xr_parser.normalize_metadata` then does our own normalization:

  - For all variables (dependent variables and coordinates) in the dataset, we normalize the standard name (:meth:`~src.xr_parser.normalize_standard_name`) and units attributes (:meth:`~src.xr_parser.normalize_unit`).
  - :meth:`~src.xr_parser.normalize_dependent_var` verifies that a dependent variable exists in the dataset matching the name expected in the TranslatedVarlistEntry.

- :meth:`~src.xr_parser.check_calendar` checks whether decode\_cf() parsed the date axis correctly, and if not, looks for calendar information in some non-standard locations. This is needed before we do reconciliation tasks involving the time coordinate.
- :meth:`~src.xr_parser.reconcile_variable` then reconciles the data's metadata with the expected metadata from the TranslatedVarlistEntry. In general, missing metadata from either source is filled in with values from the other source, while explicit differences in metadata attributes raise an error.

  - :meth:`~src.xr_parser.reconcile_names` reconciles the variable's name and its standard name attribute.
  - :meth:`~src.xr_parser.reconcile_units` reconciles the units attribute. An error is raised if the units are inequivalent, but unequal units are OK.
  - :meth:`~src.xr_parser.reconcile_dimension_coords` does similar logic for the variable's dimension coordinates, also reconciling the coordinate's bounds variable if present.
  - :meth:`~src.xr_parser.reconcile_scalar_coords` does similar logic for the variable's scalar coordinates (levels of a 3D variable.)

- :meth:`~src.xr_parser.check_ds_attrs` does all remaining checks on the final state of the metadata: 

  - We verify the calendar is still set correctly.
  - For all variables, we ensure that valid standard name and units attributes were assigned.

At this point, the metadata on the dataset is ready for use by the preprocessor's transformations.


Xarray accessor
---------------

We use `xarray <http://xarray.pydata.org/en/stable/index.html>`__ to load and manipulate all model data, as it's by far the most fully-functioned and best-maintained python library for doing so. However, it's a general purpose library, and we'd like to customize the xarray Dataset and DataArray objects to have functionality specific to climate model metadata. 

The reason extending xarray is so important lies with implementing the CF standard data model: while xarray advertises `partial support <http://xarray.pydata.org/en/stable/user-guide/weather-climate.html>`__ for the CF conventions, in practice this is limited to CF-compliant, calendar-aware parsing of time coordinates. Instead of variable metadata being thrown into a dict, we would like to parse it into the same classes used for other objects in the data model, in particular the VarlistEntry. 

The problem of user extensions to xarray is a longstanding one (see e.g. this `thread <https://github.com/pydata/xarray/issues/1080>`__ or a more recent `follow-up <https://github.com/pydata/xarray/issues/3959>`__). The xarray classes are complex, and it's impractical to ask child classes to re-implement all their supported methods. For the time being, we use the supported method of custom "`accessors <http://xarray.pydata.org/en/stable/internals/extending-xarray.html>`__", which in effect allows Datasets and DataArrays to be extended via custom properties. This situation isn't fully satisfactory: for example, accessor properties are effectively `read-only <https://github.com/pydata/xarray/issues/3268>`__ and some array manipulations (which aren't performed by the framework) may cause attributes to be dropped completely.

The solution we adopt is to use the accessor mechanism, customizing a third-party solution to our needs as they evolve. We use `cf\_xarray's <https://cf-xarray.readthedocs.io/en/latest/index.html>`__ as a third-party dependency, which defines its own accessors (through an attribute named ``cf`` added to Datasets and DataArrays). We customize some of the methods it offers to return values that are more easily comparable with the corresponding methods on VarlistEntry objects. Because cf\_xarray implements some functionality as a module-level function rather than a method, we need to resort to monkey-patching to override its behavior. This is done in :func:`~src.xr_parser.patch_cf_xarray_accessor`. After this is done, the new accessor classes are :class:`~src.xr_parser.MDTFCFDatasetAccessor` and :class:`~src.xr_parser.MDTFCFDataArrayAccessor`. We register them under the same attribute name (``cf``) for simplicity, although this has potential to cause confusion for readers familiar with vanilla cf_xarray.


Preprocessor functions
----------------------

Overview
++++++++

As described above, preprocessor transformations aren't implemented as simple python functions, because they have two roles: to actually perform the conversion, and to expand the scope of the data query to include all data formats they can convert between. Because of this, transformations are implemented as classes with two methods for the two roles: :meth:`~src.preprocessor.PreprocessorFunctionBase.edit_request` and :meth:`~src.preprocessor.PreprocessorFunctionBase.process`. The abstract base class defining these is :class:`~src.preprocessor.PreprocessorFunctionBase`. (Replacing "Function" with "Transformation" in the class names would be less confusing.)

Editing the data request
++++++++++++++++++++++++

Recall that by "data request," we mean the linked list of VarlistEntry objects connected through the ``alternates`` attribute. The **Query** stage of the data source traverses this list in breadth-first order until a viable set of alternates is found: if the data specified by one VarlistEntry isn't available, we try its alternates (if it has any), and if one of those isn't found, we try its alternates, and so on. "Editing the data request" corresponds to inserting new VarlistEntry objects into this linked list corresponding to the alternatives we want to consider.

Some transformations don't need to implement edit_request(). For example, :class:`~src.preprocessor.ConvertUnitsFunction`: units are uniquely determined by the variable name and model's variable convention; no data source saves multiple copies of the same variable in different units.

An simple example of a transformation that implements edit_request() is :class:`~src.preprocessor.PrecipRateToFluxFunction`: different models and different PODs define precipitation as a rate or as a mass flux. It's easy to convert between the two, but because it falls outside the scope of the udunits2 library we handle it as a special case here. 

A POD that needs precipitation will request it as either a rate or a flux, but because we can convert between the two, we should also add the other quantity as an alternate variable to query. This is done by the :meth:`~src.preprocessor.PrecipRateToFluxFunction.edit_request` method: it takes a VarlistEntry *v* and, if it refers to precipitation rate or flux, returns an edited copy *new_v* referring to the other quantity (and returning None otherwise.) The decorator :func:`~src.preprocessor.edit_request_wrapper` then does the bookkeeping work of inserting *new_v* after *v* in the linked list of alternate variables for the POD -- because this is the expected scenario for editing the data request, we collect the logic in one place.

Provenance
++++++++++

Log messages with the ObjectLogTag.NC_HISTORY tag will be copied to the ``history`` attribute of the netCDF file written as the output of the preprocessor, in case the user wishes to use these files for a non-MDTF purpose. In general, preprocessor transformations should be verbose in logging, since this section of the code is key to diagnosing problems arising from malformed model data.

