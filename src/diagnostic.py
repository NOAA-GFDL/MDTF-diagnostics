from __future__ import absolute_import, division, print_function, unicode_literals
import os
from src import six
import collections
import dataclasses
import enum
import glob
import shutil
import typing
from src import util, util_mdtf, verify_links, datelabel, data_model
from src import cli # HACK for now

@six.python_2_unicode_compatible
class PodExceptionBase(Exception):
    """Base class and common formatting code for exceptions affecting a single
    POD.
    """
    _error_str = ""

    def __init__(self, pod, msg=None):
        self.pod = pod
        self.msg = msg

    def __str__(self):
        if hasattr(self.pod, 'name'):
            pod_name = self.pod.name
        else:
            pod_name = self.pod
        s = f"Error in {pod_name}: " + self._error_str
        if self.msg is not None:
            s += f"\nReason: {self.msg}."
        return s

    def __repr__(self):
        # full repr of Diagnostic takes lots of space to print
        return f"{self.__class__.__name__}({str(self)})"

@six.python_2_unicode_compatible
class PodConfigError(PodExceptionBase):
    """Exception raised if we can't parse info in a POD's settings.jsonc file.
    (Covers issues with the file format/schema; malformed JSONC will raise a
    :py:class:`~json.JSONDecodeError` when :func:`~util.parse_json` attempts to
    parse the file.
    """
    _error_str = "Couldn't parse configuration in settings.jsonc file."

@six.python_2_unicode_compatible
class PodDataError(PodExceptionBase):
    """Exception raised if POD doesn't have required data to run. 
    """
    _error_str = "Requested data not available."

@six.python_2_unicode_compatible
class PodRuntimeError(PodExceptionBase):
    """Exception raised if POD doesn't have required resources to run. 
    """
    _error_str = "An error occurred in setting up the POD's runtime environment."

@six.python_2_unicode_compatible
class PodExecutionError(PodExceptionBase):
    """Exception raised if POD doesn't have required resources to run. 
    """
    _error_str = "An error occurred during the POD's execution."

PodDataFileFormat = util.MDTFEnum(
    'PodDataFileFormat', 
    ("ANY_NETCDF ANY_NETCDF_CLASSIC "
    "ANY_NETCDF3 NETCDF3_CLASSIC NETCDF_64BIT_OFFSET NETCDF_64BIT_DATA "
    "ANY_NETCDF4 NETCDF4_CLASSIC NETCDF4"),
    module=__name__
)

@util.mdtf_dataclass
class _VarlistGlobalSettings(object):
    format: PodDataFileFormat = PodDataFileFormat.ANY_NETCDF_CLASSIC
    rename_dimensions: bool = False
    rename_variables: bool = False
    multi_file_ok: bool = False
    dimensions_ordered: bool = False

@util.mdtf_dataclass
class _VarlistTimeSettings(object):
    frequency: typing.Any = "" # datelabel.AbstractDateFrequency = None
    min_frequency: typing.Any = "" # datelabel.AbstractDateFrequency = None
    max_frequency: typing.Any = "" # datelabel.AbstractDateFrequency = None
    min_duration: str = 'any'
    max_duration: str = 'any'

@util.mdtf_dataclass
class VarlistSettings(_VarlistGlobalSettings, _VarlistTimeSettings):
    """Class to describe options affecting all variables requested by this POD.
    Corresponds to the "data" section of the POD's settings.jsonc file.
    """
    pass

    @property
    def global_settings(self):
        return util.filter_dataclass(self, _VarlistGlobalSettings)

    @property
    def time_settings(self):
        return util.filter_dataclass(self, _VarlistTimeSettings)

@util.mdtf_dataclass(frozen=True)
class VarlistCoordinateMixin(object):
    """Base class to describe a single dimension (in the netcdf data model sense)
    used by one or more variables. Corresponds to list entries in the 
    "dimensions" section of the POD's settings.jsonc file.
    """
    need_bounds: bool = False

@util.mdtf_dataclass(frozen=True)
class VarlistCoordinate(data_model.DMCoordinate, VarlistCoordinateMixin):
    pass

@util.mdtf_dataclass(frozen=True)
class VarlistLongitudeCoordinate(data_model.DMLongitudeCoordinate, \
    VarlistCoordinateMixin):
    range: tuple = None

@util.mdtf_dataclass(frozen=True)
class VarlistLatitudeCoordinate(data_model.DMLatitudeCoordinate, \
    VarlistCoordinateMixin):
    range: tuple = None

@util.mdtf_dataclass(frozen=True)
class VarlistVerticalCoordinate(data_model.DMVerticalCoordinate, \
    VarlistCoordinateMixin):
    pass

@util.mdtf_dataclass(frozen=True)
class VarlistPlaceholderTimeCoordinate(data_model.DMGenericTimeCoordinate, \
    VarlistCoordinateMixin):
    frequency: typing.Any = ""
    min_frequency: typing.Any = ""
    max_frequency: typing.Any = ""
    min_duration: typing.Any = 'any'
    max_duration: typing.Any = 'any'

    standard_name = 'time'
    axis = 'T'

@util.mdtf_dataclass(frozen=True)
class VarlistTimeCoordinate(data_model.DMTimeCoordinate, _VarlistTimeSettings, 
    VarlistCoordinateMixin):
    pass

VarlistEntryRequirement = util.MDTFEnum(
    'VarlistEntryRequirement', 
    'REQUIRED OPTIONAL ALTERNATE AUX_COORDINATE', module=__name__
)

@util.mdtf_dataclass
class VarlistEntry(data_model.DMVariable, VarlistSettings):
    """Class to describe data for a single variable requested by a POD. 
    Corresponds to list entries in the "varlist" section of the POD's 
    settings.jsonc file.

    Two VarlistEntries are equal (as determined by the ``__eq__`` method, which
    compares fields without ``compare=False``) if they specify the same data 
    product, ie if the same output file from the preprocessor can be symlinked 
    to two different locations.
    """
    name_in_model: str = dataclasses.field(default="", compare=False)
    dest_path: str = ""
    env_var: str = ""
    path_variable: str = dataclasses.field(default="", compare=False)
    use_exact_name: bool = False
    requirement: VarlistEntryRequirement = dataclasses.field(
        default=VarlistEntryRequirement.REQUIRED, compare=False
    )
    alternates: list = dataclasses.field(default_factory=list, compare=False)
    active: bool = dataclasses.field(init=False, compare=False)

    preprocessor: typing.Any = dataclasses.field(default=None, compare=False)
    exception: Exception = dataclasses.field(init=False, compare=False)

    def __post_init__(self):
        super(VarlistEntry, self).__post_init__()
        self.active = (self.requirement == VarlistEntryRequirement.REQUIRED)
        self.exception = None
        if not self.path_variable:
            self.path_variable = self.name.upper() + '_FILE'
        # self.alternates is either [] or a list of nonempty lists of VEs
        if self.alternates:
            if not isinstance(self.alternates[0], list):
                self.alternates = [self.alternates]
            self.alternates = [vs for vs in self.alternates if vs]
        if not self.env_var:
            self.env_var = self.name # TODO: fix when we do standard_names right

    @property
    def failed(self):
        return (self.exception is not None)

    @classmethod
    def from_struct(cls, global_settings_d, dims_d, name, **kwargs):
        """Instantiate from a struct in the varlist section of a POD's
        settings.jsonc.
        """
        new_kw = global_settings_d.copy()
        new_kw['dims'] = []
        new_kw['scalar_coords'] = set([])

        if 'dimensions' not in kwargs:
            raise ValueError(f"No dimensions specified for varlist entry {name}.")
        for d_name in kwargs.pop('dimensions'):
            if d_name not in dims_d:
                raise ValueError((f"Unknown dimension name {d_name} in varlist "
                    f"entry for {name}."))
            new_kw['dims'].append(dims_d[d_name])
        new_kw['dims'] = tuple(new_kw['dims'])

        if 'scalar_coordinates' in kwargs:
            for d_name, scalar_val in kwargs.pop('scalar_coordinates').items():
                if d_name not in dims_d:
                    raise ValueError((f"Unknown dimension name {d_name} in varlist "
                        f"entry for {name}."))
                new_kw['scalar_coords'].add(
                    dims_d[d_name].make_scalar(scalar_val)
                )
        filter_kw = util.filter_dataclass(kwargs, cls)
        obj = cls(name=name, **new_kw, **filter_kw)
        # specialize time coord
        time_kw = util.filter_dataclass(kwargs, _VarlistTimeSettings)
        if time_kw:
            obj.change_coord('T', None, **time_kw)
        return obj

    def short_format(self):
        str_ = self.name
        if self.name_in_model:
            str_ += f" (= {self.name_in_model})"
        attrs_ = []
        if not self.is_static and hasattr(self.T, 'frequency'):
            attrs_.append(str(self.T.frequency))
        if self.get_scalar('Z'):
            lev = self.get_scalar('Z')
            attrs_.append(f"{lev.value} {lev.units}")
        if attrs_:
            str_ += " @ "
            str_ += ", ".join(attrs_)
        return str_

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
            try:
                if dd.get('axis', None) == 'X' \
                    or dd.get('standard_name', None) == 'longitude':
                    return VarlistLongitudeCoordinate(name=name, **dd)
                elif dd.get('axis', None) == 'Y' \
                    or dd.get('standard_name', None) == 'latitude':
                    return VarlistLatitudeCoordinate(name=name, **dd)
                elif dd.get('axis', None) == 'Z':
                    return VarlistVerticalCoordinate(name=name, **dd)
                elif dd.get('axis', None) == 'T' \
                    or dd.get('standard_name', None) == 'time':
                    return VarlistPlaceholderTimeCoordinate(
                        name=name, **dd, **(v_settings.time_settings)
                    )
                else:
                    return VarlistCoordinate(name=name, **dd)
            except Exception:
                raise ValueError(f"Couldn't parse dimension entry for {name}: {dd}")

        vlist_settings = VarlistSettings(**(d.get('data', dict())))
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
        return cls(vars= list(vlist_vars.values()))

    @property
    def active_vars(self):
        return [v for v in self.vars if v.active]

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
    name: str = util.MANDATORY
    long_name: str = ""
    description: str = ""
    convention: str = "CF"
    realm: str = ""

    varlist: Varlist = None
    exceptions: util.ExceptionQueue = dataclasses.field(init=False)

    driver: str = ""
    program: str = ""
    runtime_requirements: dict = dataclasses.field(default_factory=dict)
    pod_env_vars: dict = dataclasses.field(default_factory=dict)
    dry_run: bool = False

    CODE_ROOT: str = ""
    POD_CODE_DIR = ""
    POD_OBS_DATA = ""
    POD_WK_DIR = ""
    POD_OUT_DIR = ""
    TEMP_HTML = ""
    
    def __post_init__(self):
        self.exceptions = util.ExceptionQueue()
        for k,v in self.runtime_requirements.items():
            self.runtime_requirements[k] = util.coerce_to_iter(v)

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
            raise PodConfigError(pod_name, 
                "Caught exception while parsing settings") from exc
        try:
            pod.varlist = Varlist.from_struct(d)
        except Exception as exc:
            raise PodConfigError(pod_name, 
                "Caught exception while parsing varlist") from exc
        return pod

    @classmethod
    def from_config(cls, pod_name):
        """Usual method of instantiating Diagnostic objects, from the contents
        of its settings.jsonc file as stored in the 
        :class:`~util_mdtf.ConfigManager`.
        """
        config = util_mdtf.ConfigManager()
        # HACK - don't want to read config files twice, but this lets us
        # propagate syntax errors
        pod_config = cli.load_pod_settings(config.paths.CODE_ROOT, pod_name)
        # # following should have been caught in user input validation
        # assert pod_name in config.pods, \
        #     f"POD name {pod_name} not recognized." 
        return cls.from_struct(
            pod_name, pod_config,
            CODE_ROOT=config.paths.CODE_ROOT, 
            dry_run=config.config.get('dry_run', False)
        )

    def iter_vars(self, all_vars=False):
        if all_vars:
            yield from self.varlist.vars
        else:
            # only active vars
            yield from self.varlist.active_vars

    # this dependency inversion feels funny to me
    def configure_paths(self, data_mgr):
        config = util_mdtf.ConfigManager()
        paths = config.paths.pod_paths(self, data_mgr)
        for k,v in paths.items():
            setattr(self, k, v)

    def dest_path(self, data_mgr, var):
        """Returns the absolute path of the POD's preprocessed, local copy of 
        the file containing the requested dataset. Files not following this 
        convention won't be found by the POD.
        """
        if var.is_static:
            f_name = f"{data_mgr.case_name}.{var.name}.nc"
            return os.path.join(self.POD_WK_DIR, f_name)
        else:
            freq = var.T.frequency.format_local()
            f_name = f"{data_mgr.case_name}.{var.name}.{freq}.nc"
            return os.path.join(self.POD_WK_DIR, freq, f_name)

    # this dependency inversion feels funny to me
    def configure_vars(self, data_mgr):
        translate = util_mdtf.VariableTranslator()

        self.varlist.change_coord(
            'T', 
            new_class = {
                'self': VarlistTimeCoordinate,
                'range': data_mgr._DateRangeClass,
                'frequency': data_mgr._DateFreqClass
            },
            range=data_mgr.date_range
        )
        translate_d = translate.variables[data_mgr.convention].to_dict()
        for v in self.iter_vars(all_vars=True):
            v.dest_path = self.dest_path(data_mgr, v)
            try:
                v.name_in_model = translate_d[v.name]
            except KeyError:
                err_str = (f"Varlist entry {v.name} for POD {self.name} not "
                    f"recognized by naming convention '{data_mgr.convention}'.")
                print(err_str)
                v.exception = PodConfigError(self, err_str)
                try:
                    raise PodConfigError(self, "Bad varlist name") from v.exception
                except Exception as chained_exc:
                    self.exceptions.log(chained_exc)  
                continue

    def deactivate_if_failed(self):
        # should be called from a hook whenever we log an exception
        # only need to keep track of this up to pod execution
        if self.failed:
            for v in self.iter_vars():
                v.active = False

    def update_active_vars(self):
        """Update the status of which VarlistEntries are "active" (not failed
        somewhere in the query/fetch process) based on new information. If the
        process has failed for a VarlistEntry, try to find a set of alternate 
        VarlistEntries. If successful, activate them; if not, raise a 
        :class:`PodDataError`.
        """
        if self.failed:
            self.deactivate_if_failed()
            return
        old_active_vars = self.varlist.active_vars
        for v in old_active_vars:
            if v.failed:
                v_str = v.short_format()
                print((f"\t{self.name}: request for '{v_str}' failed; "
                    "finding alternate vars."))
                v.active = False
                alt_success_flag = False
                for alts in v.iter_alternates():
                    if any(v.failed for v in alts):
                        continue
                    # found a viable set of alternates
                    alt_success_flag = True
                    for v in alts:
                        v.active = True
                if not alt_success_flag:
                    print(f"\t{self.name}: no alternates available for '{v_str}'.")
                    try:
                        raise PodDataError(self, 
                            f"No alternates available for '{v_str}'.") from v.exception
                    except Exception as exc:
                        self.exceptions.log(exc)    
                    continue
        self.deactivate_if_failed()

    # -------------------------------------

    def setup_pod_directories(self):
        """Check and create directories specific to this POD.
        """
        util_mdtf.check_dirs(self.POD_CODE_DIR, self.POD_OBS_DATA, create=False)
        util_mdtf.check_dirs(self.POD_WK_DIR, create=True)
        dirs = ('model/PS', 'model/netCDF', 'obs/PS', 'obs/netCDF')
        for d in dirs:
            util_mdtf.check_dirs(os.path.join(self.POD_WK_DIR, d), create=True)

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
            raise PodRuntimeError(self, 
                "Caught exception during pre_run_setup") from exc

    def set_pod_env_vars(self, verbose=0):
        """Private method called by :meth:`~diagnostic.Diagnostic.setup`.
        Sets all environment variables for POD.

        Args:
            verbose (:py:obj:`int`, optional): Logging verbosity level. Default 0.
        """
        self.pod_env_vars.update({
            "POD_HOME": self.POD_CODE_DIR, # location of POD's code
            "OBS_DATA": self.POD_OBS_DATA, # POD's observational data
            "WK_DIR": self.POD_WK_DIR,     # POD's subdir within working directory
            "DATADIR": self.POD_WK_DIR     # synonym so we don't need to change docs
        })
        # Set env vars for variable and axis names:
        ax_name_verify = collections.defaultdict(set)
        for k,v in self.varlist.axes.items():
            ax_name_verify[k].add(v.name)
        for var in self.iter_vars():
            # env var for variable name currently set in data_manager, TODO: fix
            # env var for path to file:
            self.pod_env_vars[var.path_variable] = var.dest_path
            for k,v in var.axes.items():
                ax_name_verify[k].add(v.name)
        for ax, ax_set in ax_name_verify.items():
            if len(ax_set) > 1:
                # names found in two different files disagree - raise error
                raise PodRuntimeError(self,
                    f"POD's variables have conflicting names for {ax} axis: {ax_set}"
                )
        for ax, ax_set in ax_name_verify.items():
            ax_name = ax_set.pop()
            self.pod_env_vars[ax_name + '_coord'] = ax_name
            # Define ax bounds variables; TODO do this more honestly
            self.pod_env_vars[ax_name + '_bnds'] = ax_name + '_bnds'

    def check_pod_driver(self, verbose=0):
        """Private method called by :meth:`~diagnostic.Diagnostic.setup`.

        Args:
            verbose (:py:obj:`int`, optional): Logging verbosity level. Default 0.

        Raises: :exc:`~diagnostic.PodRuntimeError` if driver script
            can't be found.
        """
        func_name = "check_pod_driver "
        if (verbose > 1): 
            print(func_name," received POD settings: ", self.__dict__)
        programs = util_mdtf.get_available_programs()

        if self.driver == '':  
            print("WARNING: no valid driver entry found for ", self.name)
            #try to find one anyway
            try_filenames = [self.name+".", "driver."]      
            file_combos = [ file_root + ext for file_root \
                in try_filenames for ext in programs]
            if verbose > 1: 
                print("Checking for possible driver names in {} {}".format(
                    self.POD_CODE_DIR, file_combos
                ))
            for try_file in file_combos:
                try_path = os.path.join(self.POD_CODE_DIR, try_file)
                if verbose > 1: print(" looking for driver file "+try_path)
                if os.path.exists(try_path):
                    self.driver = try_path
                    if (verbose > 0): 
                        print("Found driver script for {}: {}".format(
                            self.name, self.driver
                        ))
                    break    #go with the first one found
                else:
                    if (verbose > 1 ): print("\t "+try_path+" not found...")
        if self.driver == '':
            raise PodRuntimeError(self, 
                """No driver script found in {}. Specify 'driver' in 
                settings.jsonc.""".format(self.POD_CODE_DIR)
                )

        if not os.path.isabs(self.driver): # expand relative path
            self.driver = os.path.join(self.POD_CODE_DIR, self.driver)
        if not os.path.exists(self.driver):
            raise PodRuntimeError(self, 
                "Unable to locate driver script {}.".format(self.driver)
                )

        if self.program == '':
            # Find ending of filename to determine the program that should be used
            driver_ext  = self.driver.split('.')[-1]
            # Possible error: Driver file type unrecognized
            if driver_ext not in programs:
                raise PodRuntimeError(self, 
                    ("{} doesn't know how to call a .{} file.\n"
                    "Supported programs: {}").format(
                        func_name, driver_ext, programs
                ))
            self.program = programs[driver_ext]
            if ( verbose > 1): 
                print(func_name +": Found program "+programs[driver_ext])

    # -------------------------------------

    def tear_down(self, verbose=0):
        """Performs cleanup tasks when the POD has finished running.

        In order, this 1) creates the POD's HTML output page from its included
        template, replacing ``CASENAME`` and other template variables with their
        current values, and adds a link to the POD's page from the top-level HTML
        report; 2) converts the POD's output plots (in PS or EPS vector format) 
        to a bitmap format for webpage display; 3) Copies all requested files to
        the output directory and deletes temporary files.

        Args:
            verbose (:py:obj:`int`, optional): Logging verbosity level. Default 0.
        """
        self.POD_HTML = os.path.join(self.POD_WK_DIR, self.name+'.html')
        # add link and description to main html page
        self.append_result_link()

        if self.active:
            self.make_pod_html()
            self.convert_pod_figures(os.path.join('model', 'PS'), 'model')
            self.convert_pod_figures(os.path.join('obs', 'PS'), 'obs')
            self.cleanup_pod_files()
            self.verify_pod_links()

            if verbose > 0: 
                print(f"---  MDTF.py Finished POD {self.name}")
                # elapsed = timeit.default_timer() - start_time
                # print(pod+" Elapsed time ",elapsed)

    def templating_dict(self):
        """Get the dict of recognized substitutions to perform in HTML templates.
        """
        config = util_mdtf.ConfigManager()
        template = config.global_env_vars.copy()
        template.update(self.pod_env_vars)
        return {str(k): str(v) for k,v in template.items()}

    def make_pod_html(self):
        """Perform templating on POD's html results page(s).

        A wrapper for :func:`~util_mdtf.append_html_template`. Looks for all 
        html files in POD_CODE_DIR, templates them, and copies them to 
        POD_WK_DIR, respecting subdirectory structure (see doc for
        :func:`~util.recursive_copy`).
        """
        template_d = self.templating_dict()
        source_files = util.find_files(self.POD_CODE_DIR, '*.html')
        util.recursive_copy(
            source_files,
            self.POD_CODE_DIR,
            self.POD_WK_DIR,
            copy_function=(
                lambda src, dest: util_mdtf.append_html_template(
                src, dest, template_dict=template_d, append=False
            )),
            overwrite=True
        )

    def append_result_link(self):
        """Update the top level index.html page with a link to this POD's results.

        This simply appends one of two html fragments to index.html: 
        pod_result_snippet.html if the POD completed successfully, or
        pod_error_snippet.html if an exception was raised during the POD's setup
        or execution.
        """
        src_dir = os.path.join(self.CODE_ROOT, 'src', 'html')
        template_d = self.templating_dict()
        if self.failed:
            # report error
            src = os.path.join(src_dir, 'pod_error_snippet.html')
            template_d['error_text'] = self.exceptions.format()
        else:
            # normal exit
            src = os.path.join(src_dir, 'pod_result_snippet.html')
        util_mdtf.append_html_template(src, self.TEMP_HTML, template_d)

    def verify_pod_links(self):
        """Check for missing files linked to from POD's html page.

        See documentation for :class:`~verify_links.LinkVerifier`. This method
        calls LinkVerifier to check existence of all files linked to from the 
        POD's own top-level html page (after templating). If any files are
        missing, an error message listing them is written to the run's index.html 
        (located in src/html/pod_missing_snippet.html).
        """
        print(f'Checking linked output files for {self.name}:')
        verifier = verify_links.LinkVerifier(
            self.POD_HTML, os.path.dirname(self.POD_WK_DIR), verbose=False
        )
        missing_out = verifier.verify_pod_links(self.name)
        if missing_out:
            print(f'ERROR: {self.name} has missing output files.')
            template_d = self.templating_dict()
            template_d['missing_output'] = '<br>'.join(missing_out)
            util_mdtf.append_html_template(
                os.path.join(self.CODE_ROOT, 'src', 'html', 
                    'pod_missing_snippet.html'),
                self.TEMP_HTML, 
                template_d
            )
            self.exceptions.log(FileNotFoundError(f'Missing {len(missing_out)} files.'))
        else:
            print(f'No files are missing.')

    def convert_pod_figures(self, src_subdir, dest_subdir):
        """Convert all vector graphics in `POD_WK_DIR/subdir` to .png files using
        ghostscript.

        All vector graphics files (identified by extension) in any subdirectory 
        of `POD_WK_DIR/src_subdir` are converted to .png files by running 
        `ghostscript <https://www.ghostscript.com/>`__ in a subprocess.
        Ghostscript is included in the _MDTF_base conda environment. Afterwards,
        any bitmap files (identified by extension) in any subdirectory of
        `POD_WK_DIR/src_subdir` are moved to `POD_WK_DIR/dest_subdir`, preserving
        and subdirectories (see doc for :func:`~util.recursive_copy`.)

        Args:
            src_subdir: Subdirectory tree of `POD_WK_DIR` to search for vector
                graphics files.
            dest_subdir: Subdirectory tree of `POD_WK_DIR` to move converted 
                bitmap files to.
        """
        config = util_mdtf.ConfigManager()
        abs_src_subdir = os.path.join(self.POD_WK_DIR, src_subdir)
        abs_dest_subdir = os.path.join(self.POD_WK_DIR, dest_subdir)
        files = util.find_files(
            abs_src_subdir,
            ['*.ps', '*.PS', '*.eps', '*.EPS', '*.pdf', '*.PDF']
        )
        for f in files:
            f_stem, _  = os.path.splitext(f)
            gs_flags = config.config.get('convert_flags', '')
            # %d = ghostscript's template for multi-page output
            f_out = f_stem + '_MDTF_TEMP_%d.png' 
            util.run_shell_command(f'gs {gs_flags} -sOutputFile="{f_out}" {f}')
            # syntax for f_out above appends "_MDTF_TEMP" + page number to 
            # output files. If input .ps/.pdf file had multiple pages, this will
            # generate 1 png per page. Page numbering starts at 1. Now check 
            # how many files gs created:
            out_files = glob.glob(f_stem + '_MDTF_TEMP_?.png')
            if not out_files:
                raise OSError(f"Error: no png generated from {f}")
            elif len(out_files) == 1:
                # got one .png, so remove suffix.
                os.rename(out_files[0], f_stem + '.png')
            else:
                # Multiple .pngs. Drop the MDTF_TEMP suffix and renumber starting
                # from zero (forget which POD requires this.)
                for n in range(len(out_files)):
                    os.rename(
                        f_stem + f'_MDTF_TEMP_{n+1}.png',
                        f_stem + f'-{n}.png'
                    )
        # move converted figures and any figures that were saved directly as bitmaps
        files = util.find_files(
            abs_src_subdir, ['*.png', '*.gif', '*.jpg', '*.jpeg']
        )
        util.recursive_copy(
            files, abs_src_subdir, abs_dest_subdir, 
            copy_function=shutil.move, overwrite=False
        )

    def cleanup_pod_files(self):
        """Copy and remove remaining files to `POD_WK_DIR`.

        In order, this 1) copies .pdf documentation (if any) from 
        `POD_CODE_DIR/doc`, 2) copies any bitmap figures in any subdirectory of
        `POD_OBS_DATA` to `POD_WK_DIR/obs` (needed for legacy PODs without 
        digested observational data), 3) removes vector graphics if requested,
        4) removes netCDF scratch files in `POD_WK_DIR` if requested.

        Settings are set at runtime, when :class:`~util_mdtf.ConfigManager` is 
        initialized.
        """
        config = util_mdtf.ConfigManager()
        # copy PDF documentation (if any) to output
        files = util.find_files(os.path.join(self.POD_CODE_DIR, 'doc'), '*.pdf')
        for f in files:
            shutil.copy2(f, self.POD_WK_DIR)

        # copy premade figures (if any) to output 
        # NOTE this will not respect 
        files = util.find_files(
            self.POD_OBS_DATA, ['*.gif', '*.png', '*.jpg', '*.jpeg']
        )
        for f in files:
            shutil.copy2(f, os.path.join(self.POD_WK_DIR, 'obs'))

        # remove .eps files if requested (actually, contents of any 'PS' subdirs)
        if not config.config.save_ps:
            for d in util.find_files(self.POD_WK_DIR, 'PS'+os.sep):
                shutil.rmtree(d)
        # delete netCDF files, keep everything else
        if config.config.save_non_nc:
            for f in util.find_files(self.POD_WK_DIR, '*.nc'):
                os.remove(f)
        # delete all generated data
        # actually deletes contents of any 'netCDF' subdirs
        elif not config.config.save_nc:
            for d in util.find_files(self.POD_WK_DIR, 'netCDF'+os.sep):
                shutil.rmtree(d)
            for f in util.find_files(self.POD_WK_DIR, '*.nc'):
                os.remove(f)
