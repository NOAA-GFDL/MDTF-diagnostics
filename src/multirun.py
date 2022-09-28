"""
Base classes implementing logic for querying, fetching and preprocessing
model data requested by the PODs for multirun mode
(i.e., a single POD is associated with multiple data sources)
"""

import dataclasses as dc
from abc import ABC
import logging
import pandas as pd
import textwrap
from src import util, data_manager, diagnostic, core
from src import query_fetch_preprocess as qfp


_log = logging.getLogger(__name__)


# METHOD RESOLUTION ORDER (MRO): What order will classes inherit in MultirunDataSourceBase
# (and other classes with multiple base classes)?
# Python3 uses C3 linearization algorithm (https://en.wikipedia.org/wiki/C3_linearization):
# L[C] = C + merge of linearization of parents of C and list of parents of C
# in the order they are inherited from left to right.
# super() returns proxy objects: objects with the ability to dispatch to methods of other objects via delegation.
# Technically, super is a class overriding the __getattribute__ method.
# Instances of super are proxy objects providing access to the methods in the MRO.
# General format is:
# super(cls, instance-or-subclass).method(*args, **kw)
# You can get the MRO of a class by running print(class.mro())
# --------------------------------------------------------------------------
# MRO: [<class '__main__.MultirunDataframeQueryDataSourceBase'>
# <class '__main__.MultirunDataSourceBase'>
# <class 'src.data_manager.DataframeQueryDataSourceBase'>
# <class 'src.data_manager.DataSourceBase'>
# <class 'src.core.MDTFObjectBase'>
# <class 'src.util.logs.CaseLoggerMixin'>
# <class 'src.util.logs._CaseAndPODHandlerMixin'>
# <class 'src.util.logs.MDTFObjectLoggerMixinBase'>
# <class 'src.data_manager.AbstractDataSource'>
# <class 'src.data_manager.AbstractQueryMixin'>
# <class 'src.data_manager.AbstractFetchMixin'>
# <class 'abc.ABC'>
# <class 'object'>]


# defining attributes using dc.field default_factory means that all instances have a default type
# This also ensures that the same attribute object is not reused each time it is called
# Therefore, you can modify individual values in one dc.field instance without propagating the
# changes to other object instances
# class MultirunVarlist(diagnostic.Varlist):
#   contents: dc.InitVar = util.MANDATORY # fields inherited from data_model.DMDataSet
#   vars: list = dc.field(init=False, default_factory=list)
#   coord_bounds: list = dc.field(init=False, default_factory=list)
#   aux_coords: list = dc.field(init=False, default_factory=list)
#   pass

class MultirunDataframeQueryDataSourceBase(data_manager.DataframeQueryDataSourceBase, ABC, metaclass=util.MDTFABCMeta):
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

    def __init__(self, parent, case_dict):
        # parent and case_dict are required by parent init method
        self.expt_keys = dict()  # Object _id -> expt_key tuple

    @property
    def all_columns(self):
        return tuple(self.df.columns)

    @property
    def remote_data_col(self):
        col_name = self.col_spec.remote_data_col
        if col_name is None:
            raise ValueError
        return col_name

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
            if v.stage < diagnostic.VarlistEntryStage.QUERIED:
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
        except Exception:  # util.DataExperimentEvent:
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
        except Exception:  # util.DataExperimentEvent:
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


class MultirunLocalFileDataSource(qfp.OnTheFlyDirectoryHierarchyQueryMixin, qfp.LocalFetchMixin,
                                  MultirunDataframeQueryDataSourceBase):
    """DataSource for dealing data in a regular directory hierarchy on a
    locally mounted filesystem. Assumes data for each variable may be split into
    several files according to date, with the dates present in their filenames.
    """
    def __init__(self, case_dict, parent):
        super(MultirunLocalFileDataSource, self).__init__(case_dict, parent)


class MultirunSingleLocalFileDataSource(MultirunLocalFileDataSource, ABC):
    """DataSource for dealing data in a regular directory hierarchy on a
    locally mounted filesystem. Assumes all data for each variable (in each
    multirun experiment) is contained in a single file. This
    """
    def query_dataset(self, var):
        """Verify that only a single file was found from each experiment.
        """
        super(MultirunSingleLocalFileDataSource, self).query_dataset(var)
        for d_key in var.data.values():
            if len(d_key.value) != 1:
                self._query_error_handler(
                    "Query found multiple files when one was expected:",
                    d_key, log=var.log
                )
