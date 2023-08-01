"""Classes that define varlist coordinates and other attributes
"""
import dataclasses as dc
import itertools
import typing
from src import util
from src import data_model
from src import translation
import os
import logging

_log = logging.getLogger(__name__)


# --------------VarlistEntry---------------------

VarlistEntryRequirement = util.MDTFEnum(
    'VarlistEntryRequirement',
    'REQUIRED OPTIONAL ALTERNATE AUX_COORDINATE',
    module=__name__
)

VarlistEntryRequirement.__doc__ = """
:class:`util.MDTFEnum` used to track whether the DataSource is required to
provide data for the :class:`VarlistEntry`.
"""

VarlistEntryStage = util.MDTFIntEnum(
    'VarlistEntryStage',
    'NOTSET INITED QUERIED FETCHED PREPROCESSED',
    module=__name__
)
VarlistEntryStage.__doc__ = """
:class:`util.MDTFIntEnum` used to track the stages of processing of a
:class:`VarlistEntry` carried out by the DataSource.
"""


_coord_env_var_suffix = '_coord'
_coord_bounds_env_var_suffix = '_bnds'
_var_name_env_var_suffix = '_var'
_file_env_var_suffix = '_FILE'

PodDataFileFormat = util.MDTFEnum(
    'PodDataFileFormat',
    ("ANY_NETCDF ANY_NETCDF_CLASSIC "
     "ANY_NETCDF3 NETCDF3_CLASSIC NETCDF_64BIT_OFFSET NETCDF_64BIT_DATA "
     "ANY_NETCDF4 NETCDF4_CLASSIC NETCDF4"),
    module=__name__
)


@util.mdtf_dataclass
class _VarlistGlobalSettings:
    format: PodDataFileFormat = \
        dc.field(default=PodDataFileFormat.ANY_NETCDF_CLASSIC, metadata={'query': True})
    rename_variables: bool = False
    multi_file_ok: bool = False
    dimensions_ordered: bool = False

@util.mdtf_dataclass
class _VarlistTimeSettings:
    frequency: util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    min_frequency: util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    max_frequency: util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    min_duration: str = util.NOTSET
    max_duration: str = util.NOTSET


@util.mdtf_dataclass
class VarlistEntryBase(metaclass=util.MDTFABCMeta):
    """Base class for VarlistEntry

    Attributes:
        use_exact_name: see docs
        env_var: Name of env var which is set to the variable's name in the
            provided dataset.
        path_variable: Name of env var containing path(s) to local data.
        dest_path: Path(s) to local data.
        alternates: List of lists of VarlistEntries.
        translation: :class:`core.TranslatedVarlistEntry`, populated by DataSource.
        stage: enum to track processing stages of VarlistEntry classes
        data: dict mapping experiment_keys to DataKeys. Populated by DataSource.
    """

    def __init_subclass__(cls):
        required_class_variables = [
            'use_exact_name',
            'env_var',
            'requirement',
            'alternates',
            'translation',
            'data',
            'stage',
            '_deactivation_log_level'
        ]
        for var in required_class_variables:
            if not hasattr(cls, var):
                raise NotImplementedError(
                    f'Class {cls} lacks required `{var}` class attribute'
                )

    def __post_init__(self):
        pass

    @property
    def _children(self):
        pass

    @property
    def name_in_model(self):
        pass

    @classmethod
    def from_struct(cls):
        pass

    def iter_alternates(self):

        def _iter_alternates():
            pass

    @staticmethod
    def alternates_str(alt_list):
        pass

    def debug_str(self):
        pass

    def iter_data_keys(self):
        pass

    def deactivate_data_key(self):
        pass

    @property
    def local_data(self):
        pass

    def query_attrs(self):
        def iter_query_attrs():
            pass

    @property
    def env_vars(self):
        pass


@util.mdtf_dataclass
class VarlistEntryMixin:
    status: util.ObjectStatus = dc.field(default=util.ObjectStatus.NOTSET, compare=False)

    def __post_init__(self, coords=None):
        # set up log (VarlistEntryLoggerMixin)
        self.init_log()
        data_model.DMVariable.__post_init__(self, coords)

        # (re)initialize mutable fields here so that if we copy VE (eg with .replace)
        # the fields on the copy won't point to the same object as the fields on
        # the original.
        self.translation = None
        self.data: util.ConsistentDict
        # activate required vars
        if self.status == util.ObjectStatus.NOTSET:
            if self.requirement == VarlistEntryRequirement.REQUIRED:
                self.status = util.ObjectStatus.ACTIVE
            else:
                self.status = util.ObjectStatus.INACTIVE

        # env_vars
        if not self.env_var:
            self.env_var = self.name + _var_name_env_var_suffix

        if not self.path_variable:
            self.path_variable = self.name.upper() + _file_env_var_suffix
        # self.alternates is either [] or a list of nonempty lists of VEs
        if self.alternates:
            if not isinstance(self.alternates[0], list):
                self.alternates = [self.alternates]
            self.alternates = [vs for vs in self.alternates if vs]

    @property
    def _children(self):
        """Iterable of child objects associated with this object."""
        return []  # leaves of object hierarchy

    @property
    def name_in_model(self):
        if self.translation and self.translation.name:
            return self.translation.name
        else:
            return "(not translated)"
            # raise ValueError(f"Translation not defined for {self.name}.")

    @classmethod
    def from_struct(cls, global_settings_d, dims_d, name, parent, **kwargs):
        """Instantiate from a struct in the varlist section of a POD's
        settings.jsonc.
        """
        new_kw = global_settings_d.copy()
        new_kw['coords'] = []

        if 'dimensions' not in kwargs:
            raise ValueError(f"No dimensions specified for varlist entry {name}.")
        # validate: check for duplicate coord names
        scalars = kwargs.get('scalar_coordinates', dict())
        seen = set()
        dupe_names = set(x for x
                         in itertools.chain(kwargs['dimensions'], scalars.keys())
                         if x in seen or seen.add(x))
        if dupe_names:
            raise ValueError((f"Repeated coordinate names {list(dupe_names)} in "
                              f"varlist entry for {name}."))

        # add dimensions
        for d_name in kwargs.pop('dimensions'):
            if d_name not in dims_d:
                raise ValueError((f"Unknown dimension name {d_name} in varlist "
                                  f"entry for {name}."))
            new_kw['coords'].append(dims_d[d_name])

        # add scalar coords
        if 'scalar_coordinates' in kwargs:
            for d_name, scalar_val in kwargs.pop('scalar_coordinates').items():
                if d_name not in dims_d:
                    raise ValueError((f"Unknown dimension name {d_name} in varlist "
                                      f"entry for {name}."))
                new_kw['coords'].append(dims_d[d_name].make_scalar(scalar_val))
        filter_kw = util.filter_dataclass(kwargs, cls, init=True)
        obj = cls(name=name, _parent=parent, **new_kw, **filter_kw)
        # specialize time coord
        time_kw = util.filter_dataclass(kwargs, _VarlistTimeSettings)
        if time_kw:
            obj.change_coord('T', None, **time_kw)
        return obj

    def iter_alternates(self):
        """Breadth-first traversal of "sets" of alternate VarlistEntries,
        alternates for those alternates, etc. ("Sets" is in quotes because
        they're implemented as lists here, since VarlistEntries aren't immutable.)

        This is a "deep" iterator,  yielding alternates of alternates,
        alternates of those, ... etc. until variables with no alternates are
        encountered or all variables have been yielded. In addition, it yields
        the "sets" of alternates and not the VarlistEntries themselves.
        """

        def _iter_alternates():
            stack = [[self]]
            already_encountered = []
            while stack:
                alt_v_set = stack.pop(0)
                if alt_v_set not in already_encountered:
                    yield alt_v_set
                already_encountered.append(alt_v_set)
                for ve in alt_v_set:
                    for alt_v_set_of_ve in ve.alternates:
                        if alt_v_set_of_ve not in already_encountered:
                            stack.append(alt_v_set_of_ve)

        # first value yielded by _iter_alternates is the var itself, so drop
        # that and then start by returning var's alternates
        iterator_ = iter(_iter_alternates())
        try:
            next(iterator_)
        except StopIteration:
            # should never get here, for above reason
            yield from []
        yield from iterator_

    @staticmethod
    def alternates_str(alt_list):
        return "[{}]".format(', '.join(v.full_name for v in alt_list))

    def debug_str(self):
        """String representation with more debugging information.
        """

        def _format(v):
            str_ = str(v)[1:-1]
            status_str = f"{v.status.name.lower()}"
            status_str += (f" ({type(v.last_exception).__name__})" if v.failed else '')
            if getattr(v, 'translation', None) is not None:
                trans_str = str(v.translation)
                trans_str = trans_str.replace("<", "'").replace(">", "'")
            else:
                trans_str = "(not translated)"
            return (f"<{str_}; {status_str}, {v.stage.name.lower()}, {v.requirement})\n"
                    f"\tName in data source: {trans_str}")

        s = _format(self)
        for i, altvs in enumerate(self.iter_alternates()):
            s += f"\n\tAlternate set #{i + 1}: {self.alternates_str(altvs)}"
        return s

    def iter_associated_files_keys(self, status=None, status_neq=None):
        """Yield :class:`~data_manager.DataKeyBase`\s
        from v's *associated_files* dict, filtering out those DataKeys
        that have beeneliminated via previous failures in fetching or preprocessing.
        """
        iter_ = self.associated_files.values()
        if status is not None:
            iter_ = filter((lambda x: x.status == status), iter_)
        elif status_neq is not None:
            iter_ = filter((lambda x: x.status != status_neq), iter_)
        yield from list(iter_)

    def iter_data_keys(self, status=None, status_neq=None):
        """Yield :class:`~data_manager.DataKeyBase`\s
        from v's *data* dict, filtering out those DataKeys that have been
        eliminated via previous failures in fetching or preprocessing.
        """
        iter_ = self.data.values()
        if status is not None:
            iter_ = filter((lambda x: x.status == status), iter_)
        elif status_neq is not None:
            iter_ = filter((lambda x: x.status != status_neq), iter_)
        yield from list(iter_)

    def deactivate_data_key(self, d_key, exc):
        """When a DataKey (*d_key*) has been deactivated during query or fetch,
        log a message and delete our record of it if we were using it, and
        deactivate ourselves if we don't have any viable DataKeys left.

        We can't just use the *status* attribute on the DataKey, because the
        VarlistEntry-DataKey relationship is many-to-many.
        """
        expt_keys_to_remove = []
        for dd_key in self.iter_data_keys(status=None):
            if dd_key == d_key:
                expt_keys_to_remove.append(dd_key.expt_key)
        if expt_keys_to_remove:
            self.log.debug("Eliminating %s for %s.", d_key, self.full_name)
        for expt_key in expt_keys_to_remove:
            del self.data[expt_key]

        if self.stage >= VarlistEntryStage.QUERIED and not self.data:
            # all DataKeys obtained for this var during query have
            # been eliminated, so need to deactivate var
            self.deactivate(util.ChildFailureEvent(self))

    @property
    def local_data(self):
        """Return sorted list of local file paths corresponding to the selected
        experiment.
        """
        if self.stage < VarlistEntryStage.FETCHED:
            raise util.DataRequestError((f"Requested local_data property on "
                                         f"{self.full_name} before fetch."))

        local_paths = set([])
        for d_key in self.iter_data_keys(status=util.ObjectStatus.ACTIVE):
            local_paths.update(d_key.local_data)
        local_paths = sorted(local_paths)
        if not local_paths:
            raise util.DataRequestError((f"local_data property on {self.full_name} "
                                         "empty after fetch."))
        return local_paths

    def query_attrs(self, key_synonyms=None):
        """Returns a dict of attributes relevant for DataSource.query_dataset()
        (ie, which describe the variable itself and aren't specific to the
        MDTF implementation.)
        """
        if key_synonyms is None:
            key_synonyms = dict()

        def iter_query_attrs(obj):
            """Recursive generator yielding name:value pairs for all dataclass
            fields marked with query attribute in their metadata.
            """
            for f in dc.fields(obj):
                val = getattr(obj, f.name, None)
                if dc.is_dataclass(val):
                    yield from iter_query_attrs(val)
                if f.metadata.get('query', False):
                    key = key_synonyms.get(f.name, f.name)
                    yield key, val

        d = util.ConsistentDict()
        d.update(dict(iter_query_attrs(self)))
        for dim in self.dims:
            d.update(dict(iter_query_attrs(dim)))
        return d


@util.mdtf_dataclass
class VarlistEntry(VarlistEntryMixin, VarlistEntryBase, util.MDTFObjectBase, data_model.DMVariable,
                   _VarlistGlobalSettings, util.VarlistEntryLoggerMixin):
    """Class to describe data for a single variable requested by a POD.
    Corresponds to list entries in the "varlist" section of the POD's
    settings.jsonc file.

    Two VarlistEntries are equal (as determined by the ``__eq__`` method, which
    compares fields without ``compare=False``) if they specify the same data
    product, ie if the same output file from the preprocessor can be symlinked
    to two different locations.

    Attributes:
        use_exact_name: see docs
        env_var: Name of env var which is set to the variable's name in the
            provided dataset.
        path_variable: Name of env var containing path to local data.
        dest_path: Path to local data.
        alternates: List of lists of VarlistEntries.
        translation: :class:`core.TranslatedVarlistEntry`, populated by DataSource.
        data: dict mapping experiment_keys to DataKeys. Populated by DataSource.
    """
    # _id = util.MDTF_ID()           # fields inherited from core.MDTFObjectBase
    # name: str
    # _parent: object
    # log = util.MDTFObjectLogger
    # status: ObjectStatus
    # standard_name: str           # fields inherited from data_model.DMVariable
    # units: Units
    # dims: list
    # scalar_coords: list
    # modifier: str
    use_exact_name: bool = False
    env_var: str = dc.field(default="", compare=False)
    path_variable: str = dc.field(default="", compare=False)
    dest_path: str = ""
    requirement: VarlistEntryRequirement = dc.field(
        default=VarlistEntryRequirement.REQUIRED, compare=False
    )
    alternates: list = dc.field(default_factory=list, compare=False)
    translation: typing.Any = dc.field(default=None, compare=False)
    data: util.ConsistentDict = dc.field(default_factory=util.ConsistentDict,
                                         compare=False)
    stage: VarlistEntryStage = dc.field(
        default=VarlistEntryStage.NOTSET, compare=False
    )

    _deactivation_log_level = logging.INFO  # default log level for failure

    @property
    def env_vars(self):
        """Get env var definitions for:

            - The path to the preprocessed data file for this variable,
            - The name for this variable in that data file,
            - The names for all of this variable's coordinate axes in that file,
            - The names of the bounds variables for all of those coordinate
              dimensions, if provided by the data.

        """
        if self.status != util.ObjectStatus.SUCCEEDED:
            # Signal to POD's code that vars are not provided by setting
            # variable to the empty string.
            return {self.env_var: "", self.path_variable: ""}

        assert self.dest_path
        d = util.ConsistentDict()

        assoc_dict = (
            {self.name.upper() + "_ASSOC_FILES": self.associated_files}
            if isinstance(self.associated_files, str)
            else {}
        )

        d.update({
            self.env_var: self.name_in_model,
            self.path_variable: self.dest_path,
            **assoc_dict
        })
        for ax, dim in self.dim_axes.items():
            trans_dim = self.translation.dim_axes[ax]
            d[dim.name + _coord_env_var_suffix] = trans_dim.name
            if trans_dim.has_bounds:
                d[dim.name + _coord_bounds_env_var_suffix] = trans_dim.bounds
        return d


@util.mdtf_dataclass
class VarlistSettings(_VarlistGlobalSettings,
                      _VarlistTimeSettings):
    """Class to describe options affecting all variables requested by this POD.
    Corresponds to the "data" section of the POD's settings.jsonc file.
    """
    @property
    def global_settings(self):
        return util.filter_dataclass(self, _VarlistGlobalSettings)

    @property
    def time_settings(self):
        return util.filter_dataclass(self, _VarlistTimeSettings)


@util.mdtf_dataclass
class VarlistCoordinate(data_model.DMCoordinate):
    """Base class to describe a single dimension (in the netcdf data model sense)
       used by one or more variables. Corresponds to list entries in the
       "dimensions" section of the POD's settings.jsonc file.
       """
    # name: str              # fields from data_model.DMCoordinate
    # standard_name: str
    # units: units.Units
    # axis: str
    # bounds: AbstractDMCoordinateBounds
    # value: typing.Union[int, float] # for scalar coordinates only
    # need_bounds: bool      # fields from VarlistCoordinateMixin
    # name_in_model: str
    # bounds_in_model: str
    need_bounds: bool = False
    pass


@util.mdtf_dataclass
class VarlistXCoordinate(data_model.DMXCoordinate):
    range: tuple = None


@util.mdtf_dataclass
class VarlistYCoordinate(data_model.DMYCoordinate):
    range: tuple = None


@util.mdtf_dataclass
class VarlistVerticalCoordinate(data_model.DMVerticalCoordinate):
    pass


@util.mdtf_dataclass
class VarlistPlaceholderTimeCoordinate(data_model.DMGenericTimeCoordinate):
    frequency: typing.Any = ""
    min_frequency: typing.Any = ""
    max_frequency: typing.Any = ""
    min_duration: typing.Any = 'any'
    max_duration: typing.Any = 'any'

    standard_name = 'time'
    axis = 'T'


@util.mdtf_dataclass
class VarlistTimeCoordinate(_VarlistTimeSettings,
                            data_model.DMTimeCoordinate):
    pass


class Varlist(data_model.DMDataSet):
    """Class to perform bookkeeping for the model variables requested by a
        single POD for multiple cases/ensemble members
    """

    def find_var(self, v):
        """If a variable matching *v* is already present in the Varlist, return
        (a reference to) it (so that we don't try to add duplicates), otherwise
        return None.
        """
        for vv in self.iter_vars():
            if v == vv:
                return vv
        return None

    def setup_var(self, pod, v):
        """Update VarlistEntry fields with information that only becomes
        available after DataManager and Diagnostic have been configured (ie,
        only known at runtime, not from settings.jsonc.)

        Could arguably be moved into VarlistEntry's init, at the cost of
        dependency inversion.
        """
        translate = translation.VariableTranslator().get_convention(self.convention)
        if v.T is not None:
            v.change_coord(
                'T',
                new_class={
                    'self': VarlistTimeCoordinate,
                    'range': util.DateRange,
                    'frequency': util.DateFrequency
                },
                range=self.attrs.date_range,
                calendar=util.NOTSET,
                units=util.NOTSET
            )
        v.dest_path = self.variable_dest_path(pod, v)
        try:
            trans_v = translate.translate(v)
            v.translation = trans_v
            # copy preferred gfdl post-processing component during translation
            if hasattr(trans_v, "component"):
                v.component = trans_v.component
        except KeyError as exc:
            # can happen in normal operation (eg. precip flux vs. rate)
            chained_exc = util.PodConfigEvent((f"Deactivating {v.full_name} due to "
                                               f"variable name translation: {str(exc)}."))
            # store but don't deactivate, because preprocessor.edit_request()
            # may supply alternate variables
            v.log.store_exception(chained_exc)
        except Exception as exc:
            chained_exc = util.chain_exc(exc, f"translating name of {v.full_name}.",
                                         util.PodConfigError)
            # store but don't deactivate, because preprocessor.edit_request()
            # may supply alternate variables
            v.log.store_exception(chained_exc)

        v.stage = VarlistEntryStage.INITED

    def variable_dest_path(self, pod, var):
        """Returns the absolute path of the POD's preprocessed, local copy of
        the file containing the requested dataset. Files not following this
        convention won't be found by the POD.
        """
        if var.is_static:
            f_name = f"{self.name}.{var.name}.static.nc"
            return os.path.join(pod.POD_WK_DIR, f_name)
        else:
            freq = var.T.frequency.format_local()
            f_name = f"{self.name}.{var.name}.{freq}.nc"
            return os.path.join(pod.POD_WK_DIR, freq, f_name)

    @classmethod
    def from_struct(cls, parent):
        """Parse the "dimensions", "data" and "varlist" sections of the POD's
        settings.jsonc file when instantiating a new :class:`Diagnostic` object.

        Args:
            parent: instance of the parent class object (pod_setup.PodObject)

        Returns:
            :py:obj:`dict`, keys are names of the dimensions in POD's convention,
            values are :class:`PodDataDimension` objects.
        """

        def _pod_dimension_from_struct(name, dd, v_settings):
            class_dict = {
                'X': VarlistXCoordinate,
                'Y': VarlistYCoordinate,
                'Z': VarlistVerticalCoordinate,
                'T': VarlistPlaceholderTimeCoordinate,
                'OTHER': VarlistCoordinate
            }
            try:
                return data_model.coordinate_from_struct(
                    dd, class_dict=class_dict, name=name,
                    **v_settings.time_settings
                )
            except Exception:
                raise ValueError(f"Couldn't parse dimension entry for {name}: {dd}")

        def _iter_shallow_alternates(var):
            """Iterator over all VarlistEntries referenced as alternates. Doesn't
            traverse alternates of alternates, etc.
            """
            for alt_vs in var.alternates:
                yield from alt_vs

        vlist_settings = util.coerce_to_dataclass(
            parent.pod_data, VarlistSettings)
        globals_d = vlist_settings.global_settings

        dims_d = parent.pod_dims

        vlist_vars = {
            k: VarlistEntry.from_struct(globals_d, dims_d, name=k, parent=parent, **v)
            for k, v in parent.pod_vars.items()
        }
        for v in vlist_vars.values():
            # validate & replace names of alt vars with references to VE objects
            for altv_name in _iter_shallow_alternates(v):
                if altv_name not in vlist_vars:
                    raise ValueError((f"Unknown variable name {altv_name} listed "
                                      f"in alternates for varlist entry {v.name}."))
            linked_alts = []
            for alts in v.alternates:
                linked_alts.append([vlist_vars[v_name] for v_name in alts])
            v.alternates = linked_alts
        return cls(contents=list(vlist_vars.values()))
