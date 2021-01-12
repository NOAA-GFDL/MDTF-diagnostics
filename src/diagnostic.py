import os
import dataclasses as dc
import typing
from src import util, core, datelabel, data_model

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
    frequency:     datelabel.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    min_frequency: datelabel.DateFrequency = \
        dc.field(default=util.NOTSET, metadata={'query': True})
    max_frequency: datelabel.DateFrequency = \
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
    # units: util.Units
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

VarlistEntryStatus = util.MDTFIntEnum(
    'VarlistEntryStatus', 
    'NOTSET INITED QUERIED FETCHED PREPROCESSED', 
    module=__name__
)

@util.mdtf_dataclass
class VarlistEntry(data_model.DMVariable, _VarlistGlobalSettings):
    """Class to describe data for a single variable requested by a POD. 
    Corresponds to list entries in the "varlist" section of the POD's 
    settings.jsonc file.

    Two VarlistEntries are equal (as determined by the ``__eq__`` method, which
    compares fields without ``compare=False``) if they specify the same data 
    product, ie if the same output file from the preprocessor can be symlinked 
    to two different locations.
    """
    _id: int = dc.field(init=False) # assigned by DataSource (avoids unsafe_hash)
    pod_name: str = ""
    use_exact_name: bool = False
    dest_path: str = ""
    env_var: str = dc.field(default="", compare=False)
    path_variable: str = dc.field(default="", compare=False)
    requirement: VarlistEntryRequirement = dc.field(
        default=VarlistEntryRequirement.REQUIRED, compare=False
    )
    alternates: list = dc.field(default_factory=list, compare=False)
    translation: typing.Any = dc.field(default=None, compare=False)
    remote_data: util.WormDict = dc.field(
        default_factory=util.WormDict, compare=False
    )
    local_data: list = dc.field(default_factory=list, compare=False)
    status: VarlistEntryStatus = dc.field(
        default=VarlistEntryStatus.NOTSET, compare=False
    )
    active: bool = dc.field(init=False, compare=False)
    exception: Exception = dc.field(init=False, compare=False)

    def __post_init__(self, coords=None):
        super(VarlistEntry, self).__post_init__(coords)
        self.active = (self.requirement == VarlistEntryRequirement.REQUIRED)
        self.exception = None

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
    def failed(self):
        return (self.exception is not None)

    def deactivate(self, exc):
        """Mark request for this variable as having failed.

        .. note::
           This doesn't manipulate the ``active`` attribute directly: that's set
           by :meth:`~Diagnostic.update_active_vars` after activating possible
           alternates for this variable.
        """
        if self.exception is not None:
            raise Exception(f"Var {str(self)} already deactivated.")
        self.exception = exc

    @property
    def name_in_model(self):
        if self.translation and self.translation.name:
            return self.translation.name
        else:
            raise ValueError(f"Translation not defined for {self.name}.")

    @property
    def env_vars(self):
        """Get env var definitions for:
            - The path to the preprocessed data file for this variable,
            - The name for this variable in that data file,
            - The names for all of this variable's coordinate axes in that file,
            - The names of the bounds variables for all of those coordinate
                dimensions, if provided by the data.
        """
        if not self.active:
            # Signal to POD's code that vars are not provided by setting 
            # variable to the empty string
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
            if trans_dim.bounds:
                d[dim.name + _coord_bounds_env_var_suffix] = trans_dim.bounds
        return d

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

    @classmethod
    def from_struct(cls, global_settings_d, dims_d, name, **kwargs):
        """Instantiate from a struct in the varlist section of a POD's
        settings.jsonc.
        """
        new_kw = global_settings_d.copy()
        new_kw['coords'] = []

        if 'dimensions' not in kwargs:
            raise ValueError(f"No dimensions specified for varlist entry {name}.")
        for d_name in kwargs.pop('dimensions'):
            if d_name not in dims_d:
                raise ValueError((f"Unknown dimension name {d_name} in varlist "
                    f"entry for {name}."))
            new_kw['coords'].append(dims_d[d_name])

        if 'scalar_coordinates' in kwargs:
            for d_name, scalar_val in kwargs.pop('scalar_coordinates').items():
                if d_name not in dims_d:
                    raise ValueError((f"Unknown dimension name {d_name} in varlist "
                        f"entry for {name}."))
                new_kw['coords'].append(dims_d[d_name].make_scalar(scalar_val))
        filter_kw = util.filter_dataclass(kwargs, cls, init=True)
        obj = cls(name=name, **new_kw, **filter_kw)
        # specialize time coord
        time_kw = util.filter_dataclass(kwargs, _VarlistTimeSettings)
        if time_kw:
            obj.change_coord('T', None, **time_kw)
        return obj

    @property
    def full_name(self):
        return '<' + self.pod_name + ':' + self.name + '>'

    def iter_alternate_entries(self):
        """Iterator over all VarlistEntries referenced as parts of "sets" of 
        alternates. ("Sets" is in quotes because they're implemented as lists 
        here, since VarlistEntries aren't immutable.) 
        """
        for alt_vs in self.alternates:
            yield from alt_vs

    def iter_alternates(self):
        """Breadth-first traversal of "sets" of alternate VarlistEntries, 
        alternates for those alternates, etc. ("Sets" is in quotes because 
        they're implemented as lists here, since VarlistEntries aren't immutable.)
        Unlike :meth:`iter_alternate_entries`, this is a "deep" iterator and 
        yields the "sets" of alternates instead of the VarlistEntries themselves.

        Note that all local state (``stack`` and ``already_encountered``) is 
        maintained across successive calls -- see docs on python generators.
        """
        stack = [[self]]
        already_encountered = []
        while stack:
            alt_vs = stack.pop(0)
            if alt_vs not in already_encountered:
                yield alt_vs
            already_encountered.append(alt_vs)
            for ve in alt_vs:
                for alt_of_alt in ve.alternates:
                    if alt_of_alt not in already_encountered:
                        stack.append(alt_of_alt)

    def debug_str(self):
        """String representation with more debugging information.
        """
        def _format(v):
            str_ = str(v)[1:-1]
            act_str = ('active' if v.active else 'inactive')
            fail_str = (f"failed (exc={v.exception})" if v.failed else 'ok')
            return (f"<{str_}; {act_str}:{v.status.name}, {fail_str}, "
                f"{v.requirement}>\n    Translation: {v.translation}")

        s = _format(self)
        for i, altvs in enumerate(self.alternates):
            s += f"\n  Alternate set #{i+1}:"
            s += '\n'.join(_format(vv) for vv in altvs)
        return s

class Varlist(data_model.DMDataSet):
    """Class to perform bookkeeping for the model variables requested by a 
    single POD.
    """
    @classmethod
    def from_struct(cls, d):
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

        vlist_settings = util.coerce_to_dataclass(
            d.get('data', dict()), VarlistSettings)
        globals_d = vlist_settings.global_settings

        assert 'dimensions' in d
        vlist_dims = {k: _pod_dimension_from_struct(k, v, vlist_settings) \
            for k,v in d['dimensions'].items()}

        assert 'varlist' in d
        vlist_vars = {
            k: VarlistEntry.from_struct(globals_d, vlist_dims, k, **v) \
            for k,v in d['varlist'].items()
        }
        for v in vlist_vars.values():
            # validate & replace names of alt vars with references to VE objects
            for altv_name in v.iter_alternate_entries():
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
class Diagnostic(object):
    """Class holding configuration for a diagnostic script. Object attributes 
    are read from entries in the settings section of the POD's settings.jsonc 
    file upon initialization.

    See `settings file documentation 
    <https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/ref_settings.html>`__
    for documentation on attributes.
    """
    _id: int = dc.field(init=False) # assigned by DataSource (avoids unsafe_hash)
    name: str = util.MANDATORY
    long_name: str = ""
    description: str = ""
    convention: str = "CF"
    realm: str = ""

    varlist: Varlist = None
    preprocessor: typing.Any = dc.field(default=None, compare=False)
    exceptions: util.ExceptionQueue = dc.field(init=False)

    driver: str = ""
    program: str = ""
    runtime_requirements: dict = dc.field(default_factory=dict)
    pod_env_vars: util.ConsistentDict = dc.field(default_factory=util.ConsistentDict)

    POD_CODE_DIR = ""
    POD_OBS_DATA = ""
    POD_WK_DIR = ""
    POD_OUT_DIR = ""
    
    def __post_init__(self):
        self.exceptions = util.ExceptionQueue()
        for k,v in self.runtime_requirements.items():
            self.runtime_requirements[k] = util.to_iter(v)

    @property
    def active(self):
        return self.exceptions.is_empty

    @property
    def failed(self):
        return not self.exceptions.is_empty

    @classmethod
    def from_struct(cls, pod_name, d, **kwargs):
        """Instantiate a Diagnostic object from the JSON format used in its
        settings.jsonc file.
        """
        try:
            kwargs.update(d.get('settings', dict()))
            pod = cls(name=pod_name, **kwargs)
        except Exception as exc:
            raise util.PodConfigError("Caught exception while parsing settings",
                pod_name) from exc
        try:
            pod.varlist = Varlist.from_struct(d)
            for v in pod.iter_vars():
                v.pod_name = pod_name
        except Exception as exc:
            raise util.PodConfigError("Caught exception while parsing varlist", 
                pod_name) from exc
        return pod

    @classmethod
    def from_config(cls, pod_name):
        """Usual method of instantiating Diagnostic objects, from the contents
        of its settings.jsonc file as stored in the 
        :class:`~core.ConfigManager`.
        """
        config = core.ConfigManager()
        return cls.from_struct(pod_name, config.pod_data[pod_name])

    def iter_vars(self, active=None):
        """Generator iterating over all VarlistEntries associated with this POD.

        Args:
            active: bool or None, default None. Selects subset of VarlistEntries
                which are returned.
                - active = True: only iterate over currently active VarlistEntries
                    (variables that are currently being queried, fetched and
                    preprocessed.)
                - active = False: only iterate over inactive VarlistEntries 
                    (Either alternates which have not yet been considered, or
                    variables which have experienced an error during query-fetch.)
                - active = None: iterate over all VarlistEntries.
        """
        if active is None:
            # default: all variables
            yield from self.varlist.iter_vars()
        else:
            # either all active or inactive vars
            yield from filter(
                (lambda v: v.active == active), self.varlist.iter_vars()
            )

    def deactivate_if_failed(self):
        """Deactivate all variables for this POD if the POD itself has failed.
        """
        # should be called from a hook whenever we log an exception
        # only need to keep track of this up to pod execution
        if self.failed:
            # Originating exception will have been logged at a higher priority?
            _log.debug("Execution of POD %s couldn't be completed successfully.", 
                self.name)
            for v in self.iter_vars():
                v.active = False

    def update_active_vars(self):
        """Update the status of which VarlistEntries are "active" (not failed
        somewhere in the query/fetch process) based on new information. If the
        process has failed for a VarlistEntry, try to find a set of alternate 
        VarlistEntries. If successful, activate them; if not, raise a 
        :class:`PodDataError`.
        """
        _log.debug('Updating active vars for POD %s', self.name)
        if self.failed:
            self.deactivate_if_failed()
            return
        old_active_vars = list(self.iter_vars(active=True))
        for v in old_active_vars:
            if v.failed:
                _log.info("Request for %s failed; finding alternate vars.", v)
                v.active = False
                alt_success_flag = False
                for alts in v.iter_alternates():
                    if any(v.failed for v in alts):
                        continue
                    # found a viable set of alternates
                    alt_success_flag = True
                    for alt_v in alts:
                        alt_v.active = True
                if not alt_success_flag:
                    _log.info("No alternates available for %s.", v.full_name)
                    try:
                        raise util.PodDataError(f"No alternates available for {v}.", 
                            self) from v.exception
                    except Exception as exc:
                        self.exceptions.log(exc)    
                    continue
        self.deactivate_if_failed()

    # -------------------------------------

    def setup_pod_directories(self):
        """Check and create directories specific to this POD.
        """
        util.check_dirs(self.POD_CODE_DIR, self.POD_OBS_DATA, create=False)
        util.check_dirs(self.POD_WK_DIR, create=True)
        dirs = ('model/PS', 'model/netCDF', 'obs/PS', 'obs/netCDF')
        for d in dirs:
            util.check_dirs(os.path.join(self.POD_WK_DIR, d), create=True)

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
            :meth:`~diagnostic.Diagnostic._check_pod_driver` and
            :meth:`~diagnostic.Diagnostic._check_for_varlist_files` 
            subroutines.
        """
        try:
            self.set_pod_env_vars()
            self.check_pod_driver()
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
        for var in self.iter_vars(active=True):
            try:
                self.pod_env_vars.update(var.env_vars)
            except util.WormKeyError as exc:
                raise util.WormKeyError((f"{var.full_name} defines coordinate names "
                    f"that conflict with those previously set. (Tried to update "
                    f"{self.pod_env_vars} with {var.env_vars}.)")) from exc
        for var in self.iter_vars(active=False):
            # define env vars for varlist entries without data. Name collisions
            # are OK in this case.
            try:
                self.pod_env_vars.update(var.env_vars)
            except util.WormKeyError:
                continue

    def check_pod_driver(self):
        """Private method called by :meth:`~diagnostic.Diagnostic.setup`.

        Raises: :exc:`~diagnostic.PodRuntimeError` if driver script
            can't be found.
        """
        programs = util.get_available_programs()

        if not self.driver:  
            _log.warning("No valid driver entry found for %s", self.full_name)
            #try to find one anyway
            try_filenames = [self.name+".", "driver."]      
            file_combos = [ file_root + ext for file_root \
                in try_filenames for ext in programs]
            _log.debug("Checking for possible driver names in {} {}".format(
                self.POD_CODE_DIR, file_combos))
            for try_file in file_combos:
                try_path = os.path.join(self.POD_CODE_DIR, try_file)
                _log.debug(" looking for driver file "+try_path)
                if os.path.exists(try_path):
                    self.driver = try_path
                    _log.debug("Found driver script for {}: {}".format(
                        self.name, self.driver))
                    break    #go with the first one found
                else:
                    _log.debug("\t "+try_path+" not found...")
        if self.driver == '':
            raise util.PodRuntimeError((f"No driver script found in "
                f"{self.POD_CODE_DIR}. Specify 'driver' in settings.jsonc."),
                self)

        if not os.path.isabs(self.driver): # expand relative path
            self.driver = os.path.join(self.POD_CODE_DIR, self.driver)
        if not os.path.exists(self.driver):
            raise util.PodRuntimeError(f"Unable to locate driver script {self.driver}.", 
                self)

        if self.program == '':
            # Find ending of filename to determine the program that should be used
            driver_ext  = self.driver.split('.')[-1]
            # Possible error: Driver file type unrecognized
            if driver_ext not in programs:
                raise util.PodRuntimeError((f"Don't know how to call a .{driver_ext} "
                        f"file.\nSupported programs: {programs}"), self)
            self.program = programs[driver_ext]
            _log.debug("Found program "+programs[driver_ext])

