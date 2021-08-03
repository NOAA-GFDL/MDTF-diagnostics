import os
import dataclasses as dc
import io
import itertools
import typing
from src import util, core, data_model

import logging
_log = logging.getLogger(__name__)

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
class _VarlistGlobalSettings(object):
    format: PodDataFileFormat = \
        dc.field(default=PodDataFileFormat.ANY_NETCDF_CLASSIC, metadata={'query': True})
    rename_variables: bool = False
    multi_file_ok: bool = False
    dimensions_ordered: bool = False

@util.mdtf_dataclass
class _VarlistTimeSettings(object):
    frequency:     util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    min_frequency: util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    max_frequency: util.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    min_duration: str = util.NOTSET
    max_duration: str = util.NOTSET

@util.mdtf_dataclass
class VarlistSettings(_VarlistGlobalSettings, _VarlistTimeSettings):
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
class VarlistCoordinateMixin(object):
    """Base class to describe a single dimension (in the netcdf data model sense)
    used by one or more variables. Corresponds to list entries in the
    "dimensions" section of the POD's settings.jsonc file.
    """
    need_bounds: bool = False

@util.mdtf_dataclass
class VarlistCoordinate(data_model.DMCoordinate, VarlistCoordinateMixin):
    # name: str              # fields from data_model.DMCoordinate
    # standard_name: str
    # units: units.Units
    # axis: str
    # bounds: AbstractDMCoordinateBounds
    # value: typing.Union[int, float] # for scalar coordinates only
    # need_bounds: bool      # fields from VarlistCoordinateMixin
    # name_in_model: str
    # bounds_in_model: str
    pass

@util.mdtf_dataclass
class VarlistLongitudeCoordinate(data_model.DMLongitudeCoordinate, \
    VarlistCoordinateMixin):
    range: tuple = None

@util.mdtf_dataclass
class VarlistLatitudeCoordinate(data_model.DMLatitudeCoordinate, \
    VarlistCoordinateMixin):
    range: tuple = None

@util.mdtf_dataclass
class VarlistVerticalCoordinate(data_model.DMVerticalCoordinate, \
    VarlistCoordinateMixin):
    pass

@util.mdtf_dataclass
class VarlistPlaceholderTimeCoordinate(data_model.DMGenericTimeCoordinate, \
    VarlistCoordinateMixin):
    frequency: typing.Any = ""
    min_frequency: typing.Any = ""
    max_frequency: typing.Any = ""
    min_duration: typing.Any = 'any'
    max_duration: typing.Any = 'any'

    standard_name = 'time'
    axis = 'T'

@util.mdtf_dataclass
class VarlistTimeCoordinate(_VarlistTimeSettings, data_model.DMTimeCoordinate,
    VarlistCoordinateMixin):
    pass

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

@util.mdtf_dataclass
class VarlistEntry(core.MDTFObjectBase, data_model.DMVariable,
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

    _deactivation_log_level = logging.INFO # default log level for failure

    def __post_init__(self, coords=None):
        # inherited from two dataclasses, so need to call post_init on each directly
        core.MDTFObjectBase.__post_init__(self)
        # set up log (VarlistEntryLoggerMixin)
        self.init_log()
        data_model.DMVariable.__post_init__(self, coords)

        # (re)initialize mutable fields here so that if we copy VE (eg with .replace)
        # the fields on the copy won't point to the same object as the fields on
        # the original.
        self.translation = None
        self.data: util.ConsistentDict()
        # activate required vars
        if self.status == core.ObjectStatus.NOTSET:
            if self.requirement == VarlistEntryRequirement.REQUIRED:
                self.status = core.ObjectStatus.ACTIVE
            else:
                self.status = core.ObjectStatus.INACTIVE

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
        return [] # leaves of object hierarchy

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
        dupe_names = set(x for x \
            in itertools.chain(kwargs['dimensions'], scalars.keys()) \
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
            s += f"\n\tAlternate set #{i+1}: {self.alternates_str(altvs)}"
        return s

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
        for d_key in self.iter_data_keys(status=core.ObjectStatus.ACTIVE):
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
                    yield (key, val)

        d = util.ConsistentDict()
        d.update(dict(iter_query_attrs(self)))
        for dim in self.dims:
            d.update(dict(iter_query_attrs(dim)))
        return d

    @property
    def env_vars(self):
        """Get env var definitions for:

            - The path to the preprocessed data file for this variable,
            - The name for this variable in that data file,
            - The names for all of this variable's coordinate axes in that file,
            - The names of the bounds variables for all of those coordinate
                dimensions, if provided by the data.

        """
        if self.status != core.ObjectStatus.SUCCEEDED:
            # Signal to POD's code that vars are not provided by setting
            # variable to the empty string.
            return {self.env_var: "", self.path_variable: ""}

        assert self.dest_path
        d = util.ConsistentDict()
        d.update({
            self.env_var: self.name_in_model,
            self.path_variable: self.dest_path
        })
        for ax, dim in self.dim_axes.items():
            trans_dim = self.translation.dim_axes[ax]
            d[dim.name + _coord_env_var_suffix] = trans_dim.name
            if trans_dim.has_bounds:
                d[dim.name + _coord_bounds_env_var_suffix] = trans_dim.bounds
        return d

class Varlist(data_model.DMDataSet):
    """Class to perform bookkeeping for the model variables requested by a
    single POD.
    """
    @classmethod
    def from_struct(cls, d, parent):
        """Parse the "dimensions", "data" and "varlist" sections of the POD's
        settings.jsonc file when instantiating a new Diagnostic() object.

        Args:
            d (:py:obj:`dict`): Contents of the POD's settings.jsonc file.

        Returns:
            :py:obj:`dict`, keys are names of the dimensions in POD's convention,
            values are :class:`PodDataDimension` objects.
        """
        def _pod_dimension_from_struct(name, dd, v_settings):
            class_dict = {
                'X': VarlistLongitudeCoordinate,
                'Y': VarlistLatitudeCoordinate,
                'Z': VarlistVerticalCoordinate,
                'T': VarlistPlaceholderTimeCoordinate,
                'OTHER': VarlistCoordinate
            }
            try:
                return data_model.coordinate_from_struct(
                    dd, class_dict=class_dict, name=name,
                    **(v_settings.time_settings)
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
            d.get('data', dict()), VarlistSettings)
        globals_d = vlist_settings.global_settings

        assert 'dimensions' in d
        dims_d = {k: _pod_dimension_from_struct(k, v, vlist_settings) \
            for k,v in d['dimensions'].items()}

        assert 'varlist' in d
        vlist_vars = {
            k: VarlistEntry.from_struct(globals_d, dims_d, name=k, parent=parent, **v) \
            for k,v in d['varlist'].items()
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
        return cls(contents = list(vlist_vars.values()))

    def find_var(self, v):
        """If a variable matching v is already present in the Varlist, return
        (a reference to) it (so that we don't try to add duplicates), otherwise
        return None.
        """
        for vv in self.iter_vars():
            if v == vv:
                return vv
        return None

# ------------------------------------------------------------

@util.mdtf_dataclass
class Diagnostic(core.MDTFObjectBase, util.PODLoggerMixin):
    """Class holding configuration for a diagnostic script. Object attributes
    are read from entries in the settings section of the POD's settings.jsonc
    file upon initialization.

    See `settings file documentation
    <https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/ref_settings.html>`__
    for documentation on attributes.
    """
    # _id = util.MDTF_ID()           # fields inherited from core.MDTFObjectBase
    # name: str
    # _parent: object
    # log = util.MDTFObjectLogger
    # status: ObjectStatus
    long_name: str = ""
    description: str = ""
    convention: str = "CF"
    realm: str = ""

    driver: str = ""
    program: str = ""
    runtime_requirements: dict = dc.field(default_factory=dict)
    pod_env_vars: util.ConsistentDict = dc.field(default_factory=util.ConsistentDict)
    log_file: io.IOBase = dc.field(default=None, init=False)
    nc_largefile: bool = False

    varlist: Varlist = None
    preprocessor: typing.Any = dc.field(default=None, compare=False)

    POD_CODE_DIR = ""
    POD_OBS_DATA = ""
    POD_WK_DIR = ""
    POD_OUT_DIR = ""

    _deactivation_log_level = logging.ERROR # default log level for failure
    # recognized interpreters for supported script types; can ovverride with
    # explict 'program' attribute in settings
    _interpreters = {'.py': 'python', '.ncl': 'ncl', '.R': 'Rscript'}

    def __post_init__(self):
        core.MDTFObjectBase.__post_init__(self)
        # set up log (PODLoggerMixin)
        self.init_log()

        for k,v in self.runtime_requirements.items():
            self.runtime_requirements[k] = util.to_iter(v)

    @property
    def _log_name(self):
        # POD loggers sit in a subtree of the DataSource logger distinct from
        # the DataKey loggers; the two subtrees are distinguished by class name
        _log_name = f"{self.name}_{self._id}".replace('.', '_')
        return f"{self._parent._log_name}.{self.__class__.__name__}.{_log_name}"

    @classmethod
    def from_struct(cls, pod_name, d, parent, **kwargs):
        """Instantiate a Diagnostic object from the JSON format used in its
        settings.jsonc file.
        """
        try:
            kwargs.update(d.get('settings', dict()))
            pod = cls(name=pod_name, _parent=parent, **kwargs)
        except Exception as exc:
            raise util.PodConfigError("Caught exception while parsing settings",
                pod_name) from exc
        try:
            pod.varlist = Varlist.from_struct(d, parent=pod)
        except Exception as exc:
            raise util.PodConfigError("Caught exception while parsing varlist",
                pod_name) from exc
        return pod

    @classmethod
    def from_config(cls, pod_name, parent):
        """Usual method of instantiating Diagnostic objects, from the contents
        of its settings.jsonc file as stored in the
        :class:`~core.ConfigManager`.
        """
        config = core.ConfigManager()
        return cls.from_struct(pod_name, config.pod_data[pod_name], parent)

    @property
    def _children(self):
        """Iterable of child objects associated with this object."""
        yield from self.varlist.iter_vars()

    def child_deactivation_handler(self, failed_v, failed_v_exc):
        """Update the status of which VarlistEntries are "active" (not failed
        somewhere in the query/fetch process) based on new information. If the
        process has failed for a :class:`VarlistEntry`, try to find a set of
        alternate VarlistEntries. If successful, activate them; if not, raise a
        :class:`PodDataError`.
        """
        if self.failed:
            return

        self.log.info("Request for %s failed; looking for alternate data.",
            failed_v)
        success = False
        for i, alt_list in enumerate(failed_v.iter_alternates()):
            failed_list = [alt_v for alt_v in alt_list if alt_v.failed]
            if failed_list:
                # skip sets of alternates where any variables have already failed
                self.log.debug(("Eliminated alternate set #%d due to deactivated "
                    "members: %s."), i, failed_v.alternates_str(failed_list))
                continue
            # found a viable set of alternates
            success = True
            self.log.info("Selected alternate set #%d: %s.",
                i+1, failed_v.alternates_str(alt_list))
            for alt_v in alt_list:
                alt_v.status = core.ObjectStatus.ACTIVE
            break
        if not success:
            try:
                raise util.PodDataError((f"No alternate data available for "
                    f"{failed_v.full_name}."), self)
            except Exception as exc:
                self.deactivate(exc)

    def close_log_file(self, log=True):
        if self.log_file is not None:
            if log:
                self.log_file.write(self.format_log(children=False))
            self.log_file.close()
            self.log_file = None

    # -------------------------------------

    def setup(self, data_source):
        """Configuration set by the DataSource on the POD (after the POD is
        initialized, but before pre-run checks.)
        """
        # set up paths/working directories
        paths = core.PathManager()
        paths = paths.pod_paths(self, data_source)
        for k,v in paths.items():
            setattr(self, k, v)
        self.setup_pod_directories()
        self.set_entry_point()
        self.set_interpreter()
        config = core.ConfigManager()
        if config.get('overwrite_file_metadata', False):
            self.log.warning(('User has disabled preprocessing functionality that '
                'uses input metadata.'), tags=util.ObjectLogTag.BANNER)
        # set up env vars
        self.pod_env_vars.update(data_source.env_vars)

        self.nc_largefile = config.get('large_file', False)
        if self.nc_largefile:
            if self.program == 'ncl':
                # argument to ncl setfileoption()
                self.pod_env_vars['MDTF_NC_FORMAT'] = "NetCDF4"
            else:
                # argument to netCDF4-python/xarray/etc.
                self.pod_env_vars['MDTF_NC_FORMAT'] = "NETCDF4"
        else:
            if self.program == 'ncl':
                # argument to ncl setfileoption()
                self.pod_env_vars['MDTF_NC_FORMAT'] = "NetCDF4Classic"
            else:
                # argument to netCDF4-python/xarray/etc.
                self.pod_env_vars['MDTF_NC_FORMAT'] = "NETCDF4_CLASSIC"

    def setup_pod_directories(self):
        """Check and create directories specific to this POD.
        """
        util.check_dir(self, 'POD_CODE_DIR', create=False)
        util.check_dir(self, 'POD_OBS_DATA', create=False)
        util.check_dir(self, 'POD_WK_DIR', create=True)

        dirs = ('model/PS', 'model/netCDF', 'obs/PS', 'obs/netCDF')
        for d in dirs:
            util.check_dir(os.path.join(self.POD_WK_DIR, d), create=True)

    def set_entry_point(self):
        """Locate the top-level driver script for the POD.

        Raises: :class:`~util.PodRuntimeError` if driver script can't be found.
        """
        if not self.driver:
            self.log.warning("No valid driver script found for %s.", self.full_name)
            # try to find one anyway
            script_names = [self.name, "driver"]
            file_names = [f"{script}{ext}" for script in script_names \
                for ext in self._interpreters.keys()]
            for f in file_names:
                path_ = os.path.join(self.POD_CODE_DIR, f)
                if os.path.exists(path_):
                    self.log.debug("Setting driver script for %s to '%s'.",
                        self.full_name, f)
                    self.driver = path_
                    break    # go with the first one found
        if not self.driver:
            raise util.PodRuntimeError((f"No driver script found in "
                f"{self.POD_CODE_DIR}. Specify 'driver' in settings.jsonc."),
                self)

        if not os.path.isabs(self.driver): # expand relative path
            self.driver = os.path.join(self.POD_CODE_DIR, self.driver)
        if not os.path.exists(self.driver):
            raise util.PodRuntimeError(
                f"Unable to locate driver script '{self.driver}'.",
                self
            )

    def set_interpreter(self):
        """Determine what executable should be used to run the driver script.

        .. note::
           Existence of the program on teh environment's ``$PATH`` isn't checked
           until before the POD runs (see :mod:`src.environment_manager`.)
        """

        if not self.program:
            # Find ending of filename to determine the program that should be used
            _, driver_ext  = os.path.splitext(self.driver)
            # Possible error: Driver file type unrecognized
            if driver_ext not in self._interpreters:
                raise util.PodRuntimeError((f"Don't know how to call a '{driver_ext}' "
                    f"file.\nSupported programs: {list(self._interpreters.values())}"),
                    self
                )
            self.program = self._interpreters[driver_ext]
            self.log.debug("Set program for %s to '%s'.",
                self.full_name, self.program)

    def pre_run_setup(self):
        """Perform filesystem operations and checks prior to running the POD.

        In order, this 1) sets environment variables specific to the POD, 2)
        creates POD-specific working directories, and 3) checks for the existence
        of the POD's driver script.

        Note:
            The existence of data files is checked with
            :meth:`data_manager.DataManager.fetchData`
            and the runtime environment is validated separately as a function of
            :meth:`environment_manager.EnvironmentManager.run`. This is because
            each POD is run in a subprocess (due to the necessity of supporting
            multiple languages) so the validation must take place in that
            subprocess.

        Raises: :exc:`~diagnostic.PodRuntimeError` if requirements
            aren't met. This is re-raised from the
            :meth:`~diagnostic.Diagnostic.set_entry_point` and
            :meth:`~diagnostic.Diagnostic._check_for_varlist_files`
            subroutines.
        """
        try:
            self.set_pod_env_vars()
            self.set_entry_point()
        except Exception as exc:
            raise util.PodRuntimeError("Caught exception during pre_run_setup",
                self) from exc

    def set_pod_env_vars(self):
        """Sets all environment variables for the POD: paths and names of each
        variable and coordinate. Raise a :class:`~src.util.exceptions.WormKeyError`
        if any of these definitions conflict.
        """
        self.pod_env_vars.update({
            "POD_HOME": self.POD_CODE_DIR, # location of POD's code
            "OBS_DATA": self.POD_OBS_DATA, # POD's observational data
            "WK_DIR": self.POD_WK_DIR,     # POD's subdir within working directory
            "DATADIR": self.POD_WK_DIR     # synonym so we don't need to change docs
        })
        for var in self.iter_children(status=core.ObjectStatus.SUCCEEDED):
            try:
                self.pod_env_vars.update(var.env_vars)
            except util.WormKeyError as exc:
                raise util.WormKeyError((f"{var.full_name} defines coordinate names "
                    f"that conflict with those previously set. (Tried to update "
                    f"{self.pod_env_vars} with {var.env_vars}.)")) from exc
        for var in self.iter_children(status_neq=core.ObjectStatus.SUCCEEDED):
            # define env vars for varlist entries without data. Name collisions
            # are OK in this case.
            try:
                self.pod_env_vars.update(var.env_vars)
            except util.WormKeyError:
                continue

