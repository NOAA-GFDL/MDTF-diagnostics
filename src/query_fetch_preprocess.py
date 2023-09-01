import abc
import dataclasses as dc
import pandas as pd
import intake
import typing
import logging
from src import util


_log = logging.getLogger(__name__)
def query_catalog(case_list: util.NameSpace, catalog_path: str):
    # build list of case names with wild card appended
    cases = [c + "*" for c in case_list.keys()]
    # open the csv file using information provided by the catalog definition file
    cat = intake.open_esm_datastore(catalog_path)
    for case_name, case_dict in case_list.items():
        sub_cat = cat.search(file_name=case_name,
                             activity_id=case_dict.convention)

    # todo: add method to get files in desired daterange
    return sub_cat


@util.mdtf_dataclass
class DataKeyBase(util.MDTFObjectBase, metaclass=util.MDTFABCMeta):
    # _id = util.MDTF_ID()           # fields inherited from core.MDTFObjectBase
    # name: str
    # _parent: object
    # log = util.MDTFObjectLogger
    # status: ObjectStatus
    name: str = dc.field(init=False)
    value: typing.Any = util.MANDATORY
    expt_key: typing.Any = None
    local_data: list = dc.field(default_factory=list, compare=False)

    def __post_init__(self):
        self.name = f"{self.__class__.__name__}_{self.value}"
        super(DataKeyBase, self).__post_init__()
        if self.status == util.ObjectStatus.NOTSET: \
            self.status == util.ObjectStatus.INACTIVE

    @property
    def _log_name(self):
        # assign a unique log name through UUID; DataKey loggers sit in a
        # subtree of the DataSource logger distinct from the POD loggers
        return f"{self._parent._log_name}.{self.__class__.__name__}.{self._id._uuid}"

    @property
    def _children(self):
        """Iterable of child objects associated with this object."""
        return []

    # level at which to log deactivation events
    _deactivation_log_level = logging.INFO

    def __str__(self):
        if util.is_iterable(self.value):
            val_str = ', '.join(str(x) for x in self.value)
        else:
            val_str = str(self.value)
        return f"DataKey({val_str})"

    @abc.abstractmethod
    def remote_data(self):
        """Returns paths, urls, etc. to be used as input to a
        :meth:`~DataSourceBase.fetch_data` method to specify how this dataset is
        fetched.
        """
        pass


class DataFrameDataKey(DataKeyBase):
    """:class:`DataKeyBase` for use with :class:`DataframeQueryDataSourceBase`
    and child classes. The *value*\s stored in the DataKey are row indices on the
    catalog DataFrame in the DataSource, and the *remote_data* method returns
    values from those rows from the column in the catalog containing the paths
    to remote data.

    .. note::
       Due to implementation, the catalog used by the DataSource must be static.
       This code could readily be adapted to a dynamic catalog if its schema
       provided a unique ID number for each row, to take the place of the row
       index used here.
    """
    def __post_init__(self):
        """*value* as passed to :class:`DataframeQueryDataSourceBase` will be the
        entire DataFrame corresponding to this group of catalog entries. Here
        we convert that to a tuple of row indices and store that instead.
        """
        self.value = tuple(self.value.index.tolist())
        super(DataFrameDataKey, self).__post_init__()

    def remote_data(self):
        """Returns paths, urls, etc. to be used as input to a *fetch_data* method
        to specify how this dataset is fetched.
        """
        # pd.DataFrame loc requires list, not just iterable
        idxs = list(self.value)
        return self._parent.df[self._parent.remote_data_col].loc[idxs]


class DataFrameQueryColumnGroup:
    """Class wrapping a set of catalog (DataFrame) column names used by
    :class:`DataframeQueryDataSourceBase` in selecting experiment attributes of
    a given scope (case-wide, pod-wide or var-wide).

    One component of :class:`DataframeQueryColumnSpec`.
    """
    def __init__(self, key_cols=None, derived_cols=None):
        if key_cols is None:
            self.key_cols = tuple()
        else:
            self.key_cols = tuple(util.to_iter(key_cols, coll_type=set))
        if derived_cols is None:
            self.cols = self.key_cols
        else:
            self.cols = tuple(set(
                self.key_cols + util.to_iter(derived_cols, coll_type=tuple)
            ))

    # hard-coded column name for DataSource-specific experiment identifier
    _expt_key_col = 'expt_key'

    def expt_key(self, df, idx=None):
        """Returns string-valued key for use in grouping the rows of *df* by
        experiment.

        .. note::
           We can't just do a .groupby on column names, because pandas attempts
           to coerce DateFrequency to a timedelta64, which overflows for static
           DateFrequency. There doesn't seem to be a way to disable this type
           coercion.
        """
        if idx is not None:   # index used in groupby
            df = df.loc[idx]
        return '|'.join(str(df[col]) for col in self.key_cols)

    def expt_key_func(self, df):
        """Function that constructs the appropriate experiment_key column
        when apply()'ed to the query results DataFrame.
        """
        return pd.Series(
            {self._expt_key_col: self.expt_key(df, idx=None)},
            dtype='object'
        )

@util.mdtf_dataclass
class DataframeQueryColumnSpec(metaclass=util.MDTFABCMeta):
    """
    - *expt_cols*: Catalog columns whose values must be the same for all
      variables being fetched. This is the most common sense in which we
      "specify an experiment."
    - *pod_expt_cols*: Catalog columns whose values must be the same for each
      POD, but may differ between PODs. An example could be spatial grid
      resolution. Defaults to the empty set.
    - *var_expt_cols*: Catalog columns whose values must "be the same for each
      variable", i.e. are irrelevant differences for our purposes but must be
      constrained to a unique value in order to uniquely specify an experiment.
      An example is the CMIP6 MIP table: the same variable can appear in
      multiple MIP tables, but the choice of table isn't relvant for PODs.
      Defaults to the empty set.

    In addition, there are specially designated column names:

    - *remote_data_col*: Name of the column in the catalog containing the
      location of the data for that row (e.g., path to a netCDF file).
    - *daterange_col*: Name of the column in the catalog containing
      :class:`util.DateRange` objects specifying the date range covered by
      the data for that row. If set to None, we assume this information isn't
      available from the catalog and date range selection logic is skipped.
    """
    expt_cols: DataFrameQueryColumnGroup = util.MANDATORY
    pod_expt_cols: DataFrameQueryColumnGroup = \
        dc.field(default_factory=DataFrameQueryColumnGroup)
    var_expt_cols: DataFrameQueryColumnGroup = \
        dc.field(default_factory=DataFrameQueryColumnGroup)
    remote_data_col: str = None
    # TODO: generate DateRange from start/end date columns
    daterange_col: str = None

    def __post__init__(self):
        pass

    @property
    def has_date_info(self):
        return self.daterange_col is not None

    @property
    def all_expt_cols(self):
        """Columns of the DataFrame specifying the experiment. We assume that
        specifying a valid value for each of the columns in this set uniquely
        identifies an experiment.
        """
        return tuple(set(
            self.expt_cols.cols + self.pod_expt_cols.cols \
            + self.var_expt_cols.cols
        ))

    def expt_key(self, df, idx=None):
        """Returns tuple of string-valued keys for grouping files by experiment:
        (<values of expt_key_cols>, <values of pod_expt_key_cols>,
        <values of var_expt_key_cols>).
        """
        return tuple(x.expt_key(df, idx=idx) for x in \
            (self.expt_cols, self.pod_expt_cols, self.var_expt_cols))

class DataframeQueryDataSourceBase(abc.ABC, metaclass=util.MDTFABCMeta):
    """DataSource which queries a data catalog made available as a pandas
    DataFrame, and includes logic for selecting experiment based on column values.
    This class overrides the data_manager:~DataSourceBase class, passing a parent
    parameter with the POD attributes, along with the original parameter
    for each case (experiment), where required

    .. note::
       This implementation assumes the catalog is static and locally loaded into
       memory. (Tom thought that) the only source of this limitation is the fact that it
       uses values of the DataFrame's Index as its DataKeys, instead of storing
       the complete row contents, so this limitation could be lifted if needed.

       TODO: integrate better with general Intake API.
    """
    _DataKeyClass = DataFrameDataKey
    col_spec = util.abstract_attribute()  # instance of DataframeQueryColumnSpec
    log: dc.InitVar = _log

    def __init__(self, parent, case_dict):
        # parent and case_dict are required by parent init method
        self.expt_keys = dict()  # Object _id -> expt_key tuple

    @property
    @abc.abstractmethod
    def df(self):
        """Synonym for the DataFrame containing the catalog."""
        pass

    @property
    def remote_data_col(self):
        col_name = self.col_spec.remote_data_col
        if col_name is None:
            raise ValueError
        return col_name

    @property
    def all_columns(self):
        return tuple(self.df.columns)

    def _query_clause(self, col_name, query_attr_name, query_attr_val):
        """Translate a single field value into a logical clause in the dataframe
        catalog query. All queryable field values are assumed to be attribute
        values on a local variable named _dict_var_name.
        """
        _attrs = 'd'  # local var name used in _query_catalog

        if query_attr_name in ('min_frequency', 'max_frequency'):
            col_name = 'frequency'  # need to avoid hardcoding this

        if col_name not in self.all_columns:
            return ""
        if query_attr_val is util.NOTSET \
                or (isinstance(query_attr_val, str) and not query_attr_val):
            return ""
        elif query_attr_val is None:
            # In pandas filtering, ==, != fail on None; should convert Nones to np.nans
            return f"(`{col_name}`.isnull())"

        if isinstance(query_attr_val, util.DateRange):
            # skip, since filtering on DateRange is done separately in
            # _query_catalog, since pandas doesn't allow use of 'in' for
            # non-list membership
            return ""
        elif query_attr_name == 'min_frequency':
            return f"(`{col_name}` >= @{_attrs}.{query_attr_name})"
        elif query_attr_name == 'max_frequency':
            return f"(`{col_name}` <= @{_attrs}.{query_attr_name})"
        else:
            return f"(`{col_name}` == @{_attrs}.{query_attr_name})"

    def _query_catalog(self, var):
        """Construct and execute the query to determine whether data matching
        var is present in the catalog.

        Split off logic done here to perform the query against the catalog
        (returning a dataframe with results) from the processing of those
        results, in order to simplify overriding by child classes.
        """
        # construct query string for non-DateRange attributes
        query_d = util.WormDict()
        query_d.update(dc.asdict(self.attrs))
        field_synonyms = getattr(self, '_query_attrs_synonyms', dict())
        query_d.update(var.query_attrs(field_synonyms))
        clauses = [self._query_clause(k, k, v) for k,v in query_d.items()]
        query_str = '&'.join(c for c in clauses if c)

        # filtering on DateRange is done here, separately, due to limitations on
        # pd.query()/pd.eval() -- arbitrary method calls not supported, at least
        # not efficiently. TODO: better implementation with <=/>= separate
        # start/end date columns.
        catalog_df = self.df
        for col_name, v in query_d.items():
            if isinstance(v, util.DateRange):
                if col_name not in catalog_df:
                    # e.g., for sample model data where date_range not in catalog
                    continue
                # select files whose date range overlaps analysis date range
                # (in case we're dealing with chunked/multi-file data)
                row_sel = catalog_df.apply(
                    (lambda r: r[col_name].overlaps(v)),
                    axis=1
                )
                catalog_df = catalog_df[row_sel]

        return catalog_df.query(
            query_str,
            local_dict={'d': util.NameSpace.fromDict(query_d)}
        )

    def check_group_daterange(self, group_df, expt_key=None, log=_log):
        """Sort the files found for each experiment by date, verify that
        the date ranges contained in the files are contiguous in time and that
        the date range of the files spans the query date range.
        """
        date_col = self.col_spec.daterange_col # abbreviate
        if not self.col_spec.has_date_info or date_col not in group_df:
            return group_df

        d_key = self.data_key(group_df, expt_key=expt_key)
        try:
            sorted_df = group_df.sort_values(by=date_col)
            # method throws ValueError if ranges aren't contiguous
            files_date_range = util.DateRange.from_contiguous_span(
                *(sorted_df[date_col].to_list())
            )
            # throws AssertionError if we don't span the query range
            assert files_date_range.contains(self.attrs.date_range)
            return sorted_df
        except ValueError:
            self._query_error_handler(
                "Non-contiguous or malformed date range in files:", d_key, log=log
            )
        except AssertionError:
            log.debug(("Eliminating expt_key since date range of files (%s) doesn't "
                       "span query range (%s)."), files_date_range, self.attrs.date_range)
        except Exception as exc:
            self._query_error_handler(f"Caught exception {repr(exc)}:", d_key,
                                      log=log)
        # hit an exception; return empty DataFrame to signify failure
        return pd.DataFrame(columns=group_df.columns)

    def _query_group_hook(self, group_df):
        """Additional filtering to do on query results for a single experiment,
        for use by child classes.
        """
        return group_df

    def query_dataset(self, var):
        """Find all rows of the catalog matching relevant attributes of the
        DataSource and of the variable (:class:`~diagnostic.VarlistEntry`).
        Group these by experiments, and for each experiment make the corresponding
        :class:`DataFrameDataKey` and store it in var's *data* attribute.
        Specifically, the *data* attribute is a dict mapping experiments
        (labeled by experiment_keys) to data found for that variable
        by this query (labeled by the DataKeys).
        """
        query_df = self._query_catalog(var)
        # assign set of sets of catalog row indices to var's data attr
        # filter out empty entries = queries that failed.
        expt_groups = query_df.groupby(
            by=(lambda idx: self.col_spec.expt_key(query_df, idx))
        )
        var.data = util.ConsistentDict()
        for expt_key, group in expt_groups:
            group = self.check_group_daterange(group, expt_key=expt_key, log=var.log)
            if group.empty:
                var.log.debug('Expt_key %s eliminated by _check_group_daterange',
                              expt_key)
                continue
            group = self._query_group_hook(group)
            if group.empty:
                var.log.debug('Expt_key %s eliminated by _query_group_hook', expt_key)
                continue
            d_key = self.data_key(group, expt_key=expt_key)
            var.log.debug('Query found <expt_key=%s, %s> for %s',
                          expt_key, d_key, var.full_name)
            var.data[expt_key] = d_key

            if not isinstance(var.associated_files, dict):
                var.associated_files = {}

            # Query for associated files - if the object contains a
            # `query_associated_fields` method, we call it here. This is currently
            # implemented for the gfdl `GFDL_GCP_FileDataSourceBase`, but any
            # class that inherits ` DataframeQueryDataSourceBase` can define this
            # method to populate the `VarlistEntry.associated_files` attribute.
            # Otherwise, this attribute is set to an empty dictionary here.
            if not hasattr(self, "query_associated_files") or not var.associated_files:
                continue
            try:
                var.associated_files[expt_key] = self.query_associated_files(d_key)
            except Exception as exc:
                var.log.debug(f"Unable to query associated files: {exc}")

    def _query_error_handler(self, msg, d_key, log=_log):
        """Log debugging message or raise an exception, depending on if we're
        in strict mode.
        """
        err_str = msg + '\n' + textwrap.indent(str(d_key.remote_data()), 4*' ')
        if self.strict:
            raise util.DataQueryEvent(err_str, d_key)
        else:
            log.warning(err_str)

    # --------------------------------------------------------------

    def _expt_df(self, obj, var_iterator, col_group, parent_id=None, obj_name=None):
        """Return a DataFrame of partial experiment attributes (as determined by
        *cols*) that are shared by the query results of all variables covered by
        var_iterator.
        """
        key_col = col_group._expt_key_col # name of the column for the expt_key
        cols = list(col_group.cols)  # DataFrame requires list
        if not cols:
            # short-circuit construction for trivial case (no columns in expt_key)
            return pd.DataFrame({key_col: [""]}, dtype='object')

        expt_df = None
        if parent_id is None:
            parent_key = tuple()
        else:
            parent_key = self.expt_keys[parent_id]
        if obj_name is None:
            obj_name = obj.name

        for v in var_iterator:
            if v.stage < varlistentry_util.VarlistEntryStage.QUERIED:
                continue
            rows = set([])
            for d_key in v.iter_data_keys():
                # filter vars on the basis of previously selected expt attributes
                if d_key.expt_key[:len(parent_key)] == parent_key:
                    rows.update(util.to_iter(d_key.value))
            v_expt_df = self.df[cols].loc[list(rows)].drop_duplicates().copy()
            v_expt_df[key_col] = v_expt_df.apply(col_group.expt_key_func, axis=1)
            if v_expt_df.empty:
                # should never get here
                raise util.DataExperimentEvent(("No choices of expt attrs "
                                                f"for {v.full_name} in {obj_name}."), v)
            v.log.debug('%s expt attr choices for %s from %s',
                        len(v_expt_df), obj_name, v.full_name)

            # take intersection with possible values of expt attrs from other vars
            if expt_df is None:
                expt_df = v_expt_df.copy()
            else:
                expt_df = pd.merge(
                    expt_df, v_expt_df,
                    how='inner', on=key_col, sort=False, validate='1:1'
                )
            if expt_df.empty:
                raise util.DataExperimentEvent(("Eliminated all choices of experiment "
                                                f"attributes for {obj_name} when adding {v.full_name}."), v)

        if expt_df.empty:
            # shouldn't get here
            raise util.DataExperimentEvent(f"No active variables for {obj_name}.", None)
        obj.log.debug('%s expt attr choices for %s', len(expt_df), obj_name)
        return expt_df

    def get_expt_key(self, scope, obj, parent, parent_id=None):
        """Set experiment attributes with case, pod or variable *scope*. Given
        *obj*, construct a DataFrame of experiment attributes that are found in
        the queried data for all variables in *obj*. The parent parameter provides pod-level
        information that is extracted by the iter_vars and iter_vars_only methods


        If more than one choice of experiment is possible, call
        DataSource-specific heuristics in resolve_func to choose between them.
        """
        # set columns and tiebreaker function based on the scope of the
        # selection process we're at (case-wide, pod-wide or var-wide):
        if scope == 'case':
            col_group = self.col_spec.expt_cols
            resolve_func = self.resolve_expt
            obj_name = obj.name
            var_iterator = obj.iter_vars_only(parent, active=True)
        elif scope == 'pod':
            col_group = self.col_spec.pod_expt_cols
            resolve_func = self.resolve_pod_expt
            if isinstance(obj, diagnostic.MultirunDiagnostic):
                obj_name = obj.name
                var_iterator = obj.iter_children(status=core.ObjectStatus.ACTIVE)
            else:
                obj_name = 'all PODs'
                var_iterator = self.iter_vars_only(parent, active=True)
        elif scope == 'var':
            col_group = self.col_spec.var_expt_cols
            resolve_func = self.resolve_var_expt
            if isinstance(obj, diagnostic.VarlistEntry):
                obj_name = obj.name
                var_iterator = [obj]
            else:
                obj_name = "all POD's variables"
                var_iterator = self.iter_children(status=core.ObjectStatus.ACTIVE)
        else:
            raise TypeError()
        key_col = col_group._expt_key_col  # name of the column for the expt_key

        # get DataFrame of allowable (consistent) choices
        expt_df = self._expt_df(obj, var_iterator, col_group, parent_id, obj_name)

        if len(expt_df) > 1:
            if self.strict:
                raise util.DataExperimentEvent((f"Experiment attributes for {obj_name} "
                                                f"not uniquely specified by user input in strict mode."))
            else:
                expt_df = resolve_func(expt_df, obj)
        if expt_df.empty:
            raise util.DataExperimentEvent(("Eliminated all consistent "
                                            f"choices of experiment attributes for {obj_name}."))
        elif len(expt_df) > 1:
            raise util.DataExperimentEvent((f"Experiment attributes for "
                                            f"{obj_name} not uniquely specified by user input: "
                                            f"{expt_df[key_col].to_list()}"))

        # successful exit case: we've narrowed down the attrs to a single choice
        expt_key = (expt_df[key_col].iloc[0], )
        if parent_id is not None:
            expt_key = self.expt_keys[parent_id] + expt_key
        return expt_key

    def set_expt_key(self, obj, expt_key):
        # Take last entry because each level of scope in get_expt_key adds
        # an entry to the overall expt_key tuple
        key_str = str(expt_key[-1])
        if key_str:
            obj.log.debug("Setting multirun experiment_key for '%s' to '%s'",
                          obj.name, key_str)
        self.expt_keys[obj._id] = expt_key

    def set_experiment(self, parent):
        """Ensure that all data we're about to fetch comes from the same experiment.
        If data from multiple experiments was returned by the query that just
        finished, either employ data source-specific heuristics to select one
        or return an error.
        """
        # set attributes that must be the same for all variables
        if self.failed:
            raise util.DataExperimentEvent((f"Aborting multirun experiment selection "
                                            f"for '{self.name}' due to failure."))
        key = self.get_expt_key('case', self,  parent)
        self.set_expt_key(self, key)

        # set attributes that must be the same for all variables in each POD
        try:
            # attempt to choose same values for all PODs
            key = self.get_expt_key('pod', self, parent, self._id)
            p = parent
            self.set_expt_key(p, key)
        except Exception as exc:  # util.DataExperimentEvent:
            # couldn't do that, so allow different choices for each POD
            for p in parent.iter_children(status=core.ObjectStatus.ACTIVE):
                try:
                    key = self.get_expt_key('pod', p, parent, self._id)
                    self.set_expt_key(p, key)
                except Exception as exc:
                    exc = util.DataExperimentEvent("set_experiment() on POD-level "
                                                   f"experiment attributes for '{p.name}' failed ({repr(exc)}).")
                    p.deactivate(exc)
                    continue

        # Resolve irrelevant attrs. Try to choose as many values to be the same
        # as possible, to minimize the number of files we need to fetch
        try:
            # attempt to choose same values for each POD:
            for pv in self.iter_vars(parent, active=True):  # varlist is a self (Multirun data source) attribute
                key = self.get_expt_key('var', pv.pod, parent, pv.pod._id)
                self.set_expt_key(pv.var, key)
        except Exception as exc:  # util.DataExperimentEvent:
            # couldn't do that, so allow different choices for each variable
            for pv in self.iter_vars(parent, active=True):
                try:
                    key = self.get_expt_key('var', pv.var, parent, pv.pod._id)
                    self.set_expt_key(pv.var, key)
                except Exception as exc:
                    exc = util.DataExperimentEvent("multirun set_experiment() on variable-level "
                                                   f"experiment attributes for '{pv.var.name}' failed ({repr(exc)})."),
                    pv.var.deactivate(exc)
                    continue

        # finally designate selected experiment by setting its DataKeys to ACTIVE
        for v in self.iter_vars_only(parent, active=True):
            expt_key = self.expt_keys[v._id]
            assert expt_key in v.data
            d_key = v.data[expt_key]
            assert d_key.expt_key == expt_key
            d_key.log.debug("%s selected as part of experiment_key '%s'.",
                            d_key, expt_key)
            d_key.status = core.ObjectStatus.ACTIVE

            # set associated variables to active as well
            if isinstance(v.associated_files, dict):
                if expt_key in v.associated_files.keys():
                    v.associated_files[expt_key].status = core.ObjectStatus.ACTIVE

    def resolve_expt(self, expt_df, obj):
        """Tiebreaker logic to resolve redundancies in experiments, to be
        specified by child classes.
        """
        if self.col_spec.expt_cols.key_cols:
            raise NotImplementedError
        return expt_df

    def resolve_pod_expt(self, expt_df, obj):
        """Tiebreaker logic to resolve redundancies in experiments, to be
        specified by child classes.
        """
        if self.col_spec.pod_expt_cols.key_cols:
            raise NotImplementedError
        return expt_df

    def resolve_var_expt(self, expt_df, obj):
        """Tiebreaker logic to resolve redundancies in experiments, to be
        specified by child classes.
        """
        if self.col_spec.var_expt_cols.key_cols:
            raise NotImplementedError
        return expt_df
