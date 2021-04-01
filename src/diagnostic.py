import os
import dataclasses as dc
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
    _VarlistGlobalSettings, util.MDTFObjectLoggerMixin):
    """Class to describe data for a single variable requested by a POD. 
    Corresponds to list entries in the "varlist" section of the POD's 
    settings.jsonc file.

    Two VarlistEntries are equal (as determined by the ``__eq__`` method, which
    compares fields without ``compare=False``) if they specify the same data 
    product, ie if the same output file from the preprocessor can be symlinked 
    to two different locations.
    """
    # _id = util.MDTF_ID()           # fields inherited from core.MDTFObjectBase
    # name: str
    # _parent: object
    # log = util.MDTFObjectLogger 
    # status: ObjectStatus
    # attrs: dict                  # fields inherited from data_model.DMVariable
    # standard_name: str
    # units: Units
    # dims: list
    # scalar_coords: list
    use_exact_name: bool = False
    dest_path: str = ""
    env_var: str = dc.field(default="", compare=False)
    path_variable: str = dc.field(default="", compare=False)
    requirement: VarlistEntryRequirement = dc.field(
        default=VarlistEntryRequirement.REQUIRED, compare=False
    )
    alternates: list = dc.field(default_factory=list, compare=False)
    translation: typing.Any = dc.field(default=None, compare=False)
    remote_data: util.WormDict = dc.field(default_factory=util.WormDict, compare=False)
    local_data: list = dc.field(default_factory=list, compare=False)
    stage: VarlistEntryStage = dc.field(
        default=VarlistEntryStage.NOTSET, compare=False
    )

    def __post_init__(self, coords=None):
        # inherited from two dataclasses, so need to call post_init on each directly
        core.MDTFObjectBase.__post_init__(self)
        # set up log (MDTFObjectLoggerMixin)
        self.init_log(module_logger=_log)
        data_model.DMVariable.__post_init__(self, coords)

        # (re)initialize mutable fields here so that if we copy VE (eg with .replace)
        # the fields on the copy won't point to the same object as the fields on
        # the original.
        self.translation = None
        self.remote_data: util.WormDict()
        self.local_data = []
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

        (Recall that all local state (``stack`` and ``already_encountered``) is 
        maintained across successive calls.)
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
        next(iterator_)
        yield from iterator_

    def debug_str(self):
        """String representation with more debugging information.
        """
        def _format(v):
            str_ = str(v)[1:-1]
            status_str = f"{v.status.name.lower()}.{v.stage.name.lower()}"
            fail_str = (f"(exc={repr(v.exception)})" \
                if v.failed else 'ok')
            trans_str = (str(v.translation) \
                if getattr(v, 'translation', None) is not None \
                else "(not translated)")
            return (f"<{str_}; {status_str}, {fail_str}, {v.requirement}>\n"
                f"\tTranslation: {trans_str}")

        s = _format(self)
        for i, altvs in enumerate(self.iter_alternates()):
            alt_str = ', '.join(str(vv) for vv in altvs)
            s += f"\n\tAlternate set #{i+1}: [{alt_str}]"
        return s
    
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
class Diagnostic(core.MDTFObjectBase, util.MDTFObjectLoggerMixin):
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

    varlist: Varlist = None
    preprocessor: typing.Any = dc.field(default=None, compare=False)

    POD_CODE_DIR = ""
    POD_OBS_DATA = ""
    POD_WK_DIR = ""
    POD_OUT_DIR = ""
    
    def __post_init__(self):
        core.MDTFObjectBase.__post_init__(self)
        # set up log (MDTFObjectLoggerMixin)
        self.init_log(module_logger=_log)

        for k,v in self.runtime_requirements.items():
            self.runtime_requirements[k] = util.to_iter(v)

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

    def child_deactivation_handler(self, failed_var, level=logging.ERROR):
        """Update the status of which VarlistEntries are "active" (not failed
        somewhere in the query/fetch process) based on new information. If the
        process has failed for a :class:`VarlistEntry`, try to find a set of 
        alternate VarlistEntries. If successful, activate them; if not, raise a 
        :class:`PodDataError`.
        """
        if self.failed:
            # should never get here
            raise ValueError('Active var on failed POD')
        # self.log.debug("Updating active vars for POD '%s'", self.name)

        self.log.info("Request for %s failed; finding alternate vars.", failed_var)
        success = False
        for alt_list in failed_var.iter_alternates():
            if any(alt_v.failed for alt_v in alt_list):
                # skip sets of alternates where any variables have already failed
                continue
            # found a viable set of alternates
            success = True
            for alt_v in alt_list:
                alt_v.status = core.ObjectStatus.ACTIVE
            break
        if not success:
            self.log.info("No alternates available for %s.", failed_var.full_name)
            try:
                raise util.PodDataError(f"No alternates available for {failed_var}.", 
                    self) from failed_var.exception
            except Exception as exc:
                self.deactivate(exc=exc, level=level)

    # -------------------------------------

    def setup_pod_directories(self):
        """Check and create directories specific to this POD.
        """
        util.check_dir(self, 'POD_CODE_DIR', create=False)
        util.check_dir(self, 'POD_OBS_DATA', create=False)
        util.check_dir(self, 'POD_WK_DIR', create=True)

        dirs = ('model/PS', 'model/netCDF', 'obs/PS', 'obs/netCDF')
        for d in dirs:
            util.check_dir(os.path.join(self.POD_WK_DIR, d), create=True)

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
        for var in self.iter_children(status=core.ObjectStatus.ACTIVE):
            try:
                self.pod_env_vars.update(var.env_vars)
            except util.WormKeyError as exc:
                raise util.WormKeyError((f"{var.full_name} defines coordinate names "
                    f"that conflict with those previously set. (Tried to update "
                    f"{self.pod_env_vars} with {var.env_vars}.)")) from exc
        for var in self.iter_children(status_neq=core.ObjectStatus.ACTIVE):
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
            self.log.warning("No valid driver entry found for POD '%s'.", self.name)
            # try to find one anyway
            try_filenames = [self.name+".", "driver."]      
            file_combos = [ file_root + ext for file_root \
                in try_filenames for ext in programs]
            self.log.debug("Checking for possible driver names in {} {}".format(
                self.POD_CODE_DIR, file_combos))
            for try_file in file_combos:
                try_path = os.path.join(self.POD_CODE_DIR, try_file)
                self.log.debug(" looking for driver file "+try_path)
                if os.path.exists(try_path):
                    self.driver = try_path
                    self.log.debug("Found driver script for {}: {}".format(
                        self.name, self.driver))
                    break    # go with the first one found
                else:
                    self.log.debug("\t "+try_path+" not found...")
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
            self.log.debug("Found program '%s'.", programs[driver_ext])

