from __future__ import absolute_import, division, print_function, unicode_literals
import os
from src import six
import dataclasses
import enum
import glob
import shutil
import typing
from src import util, util_mdtf, verify_links, datelabel, data_model

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
            s = s + f"\nReason: {self.msg}."
        return s

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
class VarlistSettings(object):
    """Class to describe options affecting all variables requested by this POD.
    Corresponds to the "data" section of the POD's settings.jsonc file.
    """
    format: PodDataFileFormat = PodDataFileFormat.ANY_NETCDF_CLASSIC
    rename_dimensions: bool = False
    rename_variables: bool = False
    multi_file_ok: bool = False
    min_duration: str = 'any'
    max_duration: str = 'any'
    dimensions_ordered: bool = False
    frequency: datelabel.DateFrequency = None
    min_frequency: datelabel.DateFrequency = None
    max_frequency: datelabel.DateFrequency = None

@util.mdtf_dataclass(frozen=True)
class VarlistCoordinateMixin(object):
    """Class to describe a single dimension (in the netcdf data model sense)
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
class VarlistTimeCoordinate(data_model.DMTimeCoordinate, VarlistCoordinateMixin):
    pass

VarlistEntryRequirement = util.MDTFEnum(
    'VarlistEntryRequirement', 
    'REQUIRED OPTIONAL ALTERNATE AUX_COORDINATE', module=__name__
)

VarlistEntryStatus = util.MDTFEnum(
    'VarlistEntryStatus', 'INIT QUERY FETCH', module=__name__
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
    path_variable: str = dataclasses.field(default=None, compare=False)
    use_exact_name: bool = False
    requirement: VarlistEntryRequirement = dataclasses.field(
        default=VarlistEntryRequirement.REQUIRED, compare=False
    )
    alternates: list = dataclasses.field(default_factory=list, compare=False)
    active: bool = dataclasses.field(init=False, compare=False)
    status: VarlistEntryStatus = dataclasses.field(init=False, compare=False)
    exception: Exception = dataclasses.field(init=False, compare=False)

    def __post_init__(self):
        super(VarlistEntry, self).__post_init__()
        self.active = (self.requirement == VarlistEntryRequirement.REQUIRED)
        self.status = VarlistEntryStatus.INIT
        self.exception = None
        if not self.path_variable:
            self.path_variable = self.name.upper() + '_FILE'
        # self.alternates is either [] or a list of nonempty lists of VEs
        if self.alternates:
            if not isinstance(self.alternates[0], list):
                self.alternates = [self.alternates]
            self.alternates = [vs for vs in self.alternates if vs]

    @property
    def failed(self):
        return (self.exception is not None)

    @classmethod
    def from_struct(cls, varlist_settings, dim_dict, name, **kwargs):
        """Instantiate from a struct in the varlist section of a POD's
        settings.jsonc.
        """
        new_kw = dataclasses.asdict(varlist_settings)
        new_kw['dims'] = []
        new_kw['scalar_coords'] = set([])

        if 'dimensions' not in kwargs:
            raise ValueError(f"No dimensions specified for varlist entry {name}.")
        for d_name in kwargs.pop('dimensions'):
            if d_name not in dim_dict:
                raise ValueError((f"Unknown dimension name {d_name} in varlist "
                    f"entry for {name}."))
            new_kw['dims'].append(dim_dict[d_name])
        new_kw['dims'] = tuple(new_kw['dims'])

        if 'scalar_coordinates' in kwargs:
            for d_name, scalar_val in kwargs.pop('scalar_coordinates').items():
                if d_name not in dim_dict:
                    raise ValueError((f"Unknown dimension name {d_name} in varlist "
                        f"entry for {name}."))
                new_kw['scalar_coords'].add(
                    dim_dict[d_name].make_scalar(scalar_val)
                )
        new_kw.update(kwargs)
        return cls(name=name, **new_kw)

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
        def _pod_dimension_from_struct(name, dd):
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
                    return VarlistTimeCoordinate(name=name, **dd)
                else:
                    return VarlistCoordinate(name=name, **dd)
            except Exception:
                raise ValueError(f"Couldn't parse dimension entry for {name}: {dd}")

        vlist_settings = VarlistSettings(**(d.get('data', dict())))
        assert 'dimensions' in d
        vlist_dims = {k: _pod_dimension_from_struct(k, v) \
            for k,v in d['dimensions'].items()}

        assert 'varlist' in d
        vlist_vars = {
            k: VarlistEntry.from_struct(vlist_settings, vlist_dims, k, **v) \
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
        return cls(
            dims=set(vlist_dims.values()),
            vars=list(vlist_vars.values())
        )

    @property
    def active_vars(self):
        return [v for v in self.vars if v.active]

    def update_active_vars(self):
        """Update the status of which VarlistEntries are "active" (not failed
        somewhere in the query/fetch process) based on new information. If the
        process has failed for a VarlistEntry, try to find a set of alternate 
        VarlistEntries. If successful, activate them; if not, raise a 
        :class:`PodDataError`.
        """
        old_active_vars = self.active_vars
        failed_vs = []
        for v in old_active_vars:
            if v.failed:
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
                    # failed; ran through all sets of alternates
                    failed_vs.append(v)
        if failed_vs:
            for v in self.active_vars:
                v.active = False
            raise PodDataError(
                f"No alternates available for {[v.name for v in failed_vs]}."
            )

# ------------------------------------------------------------

DiagnosticStatus = util.MDTFEnum(
    'DiagnosticStatus', 'INIT QUERY FETCH RUN OUTPUT', module=__name__
)

@util.mdtf_dataclass
class Diagnostic(object):
    """Class holding configuration for a diagnostic script. Object attributes 
    are read from entries in the settings section of the POD's settings.jsonc 
    file upon initialization.

    See `settings file documentation 
    <https://mdtf-diagnostics.readthedocs.io/en/latest/sphinx/ref_settings.html>`__
    for documentation on attributes.
    """
    name: str
    long_name: str = ""
    description: str = ""
    convention: str = "CF"
    realm: str = ""

    POD_CODE_DIR = ""
    POD_OBS_DATA = ""
    POD_WK_DIR = ""
    POD_OUT_DIR = ""
    TEMP_HTML = ""
    CODE_ROOT = ""

    varlist: Varlist = None
    driver: str = ""
    program: str = ""
    runtime_requirements: dict = dataclasses.field(default_factory=dict)
    pod_env_vars: dict = dataclasses.field(default_factory=dict)
    dry_run: bool = False

    status: DiagnosticStatus = dataclasses.field(init=False)
    exception: Exception = dataclasses.field(init=False)
    
    def __post_init__(self):
        self.status = DiagnosticStatus.INIT
        self.exception = None
        self.process_obj = None
        self.logfile_obj = None
        for k,v in self.runtime_requirements.items():
            self.runtime_requirements[k] = util.coerce_to_iter(v)

    @property
    def active(self):
        return (self.exception is None)

    @property
    def failed(self):
        return (self.exception is not None)

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
                "Caught exception while parsing settings: {0}({1!r})".format(
                    type(exc).__name__, exc.args)
            )
        try:
            pod.varlist = Varlist.from_struct(d)
        except Exception as exc:
            raise PodConfigError(pod_name, 
                "Caught exception while parsing varlist: {0}({1!r})".format(
                    type(exc).__name__, exc.args)
            )
        return pod

    @classmethod
    def from_config(cls, pod_name):
        """Usual method of instantiating Diagnostic objects, from the contents
        of its settings.jsonc file as stored in the 
        :class:`~util_mdtf.ConfigManager`.
        """
        config = util_mdtf.ConfigManager()
        assert pod_name in config.pods # catch errors in input validation
        return cls.from_struct(
            pod_name, config.pods[pod_name],
            CODE_ROOT=config.paths.CODE_ROOT, 
            dry_run=config.config.get('dry_run', False)
        )

    def iter_vars(self):
        yield from self.varlist.active_vars

    def update_active_vars(self):
        self.varlist.update_active_vars()

    def configure_paths(self, paths):
        for k,v in paths.items():
            setattr(self, k, v)

    # -------------------------------------

    def setup(self):
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
            if self.failed:
                raise self.exception
            self.set_pod_env_vars()
            self.setup_pod_directories()
            self.check_pod_driver()
        except Exception as exc:
            raise PodRuntimeError(self, 
                "Caught exception during setup: {0}({1!r})".format(
                    type(exc).__name__, exc.args)
            )

    def set_pod_env_vars(self, verbose=0):
        """Private method called by :meth:`~diagnostic.Diagnostic.setUp`.
        Sets all environment variables for POD.

        Args:
            verbose (:py:obj:`int`, optional): Logging verbosity level. Default 0.
        """
        self.pod_env_vars.update({
            "POD_HOME": self.POD_CODE_DIR, # location of POD's code
            "OBS_DATA": self.POD_OBS_DATA, # POD's observational data
            "WK_DIR": self.POD_WK_DIR,     # POD's subdir within working directory
        })
        # Set env vars POD has inherited globally and from current case 
        # (set in DataManager._setup_pod).
        for key, val in iter(self.pod_env_vars.items()):
            util_mdtf.setenv(key, val, self.pod_env_vars, verbose=verbose, overwrite=True) 

        # Set env vars for variable and axis names:
        axes = dict()
        ax_bnds = dict()
        ax_status = dict()
        for var in self.iter_vars_and_alts():
            # util_mdtf.setenv(var.original_name, var.name_in_model, 
            #     self.pod_env_vars, verbose=verbose)
            # make sure axes found for different vars are consistent
            for ax_name, ax_attrs in iter(var.axes.items()):
                if 'MDTF_envvar' not in ax_attrs:
                    print(("\tWarning: don't know env var to set" 
                        "for axis name {}").format(ax_name))
                    envvar_name = ax_name+'_coord'
                else:
                    envvar_name = ax_attrs['MDTF_envvar']
                set_from_axis = ax_attrs.get('MDTF_set_from_axis', None)
                if envvar_name not in axes:
                    # populate dict
                    axes[envvar_name] = ax_name
                    ax_status[envvar_name] = set_from_axis
                elif axes[envvar_name] != ax_name and ax_status[envvar_name] is None:
                    # populated with defaults, but now overwrite with name that
                    # was confirmed from file
                    axes[envvar_name] = ax_name
                    ax_status[envvar_name] = set_from_axis
                elif axes[envvar_name] != ax_name \
                    and ax_status[envvar_name] == set_from_axis:
                    # names found in two different files disagree - raise error
                    raise PodRuntimeError(self,
                        ("Two variables have conflicting axis names {}:"
                            "({}!={})").format(
                                envvar_name, axes[envvar_name], ax_name
                    ))
        for key, val in axes.items():
            # Define ax bounds variables; TODO do this more honestly
            ax_bnds[key+'_bnds'] = val + '_bnds'
        for key, val in axes.items(): 
            util_mdtf.setenv(key, val, self.pod_env_vars, verbose=verbose)
        for key, val in ax_bnds.items(): 
            util_mdtf.setenv(key, val, self.pod_env_vars, verbose=verbose)

    def setup_pod_directories(self, verbose =0):
        """Private method called by :meth:`~diagnostic.Diagnostic.setUp`.

        Args:
            verbose (:py:obj:`int`, optional): Logging verbosity level. Default 0.
        """
        util_mdtf.check_required_dirs(
            already_exist =[self.POD_CODE_DIR, self.POD_OBS_DATA], 
            create_if_nec = [self.POD_WK_DIR], 
            verbose=verbose)
        dirs = ['', 'model', 'model/PS', 'model/netCDF', 
            'obs', 'obs/PS','obs/netCDF']
        for d in dirs:
            if not os.path.exists(os.path.join(self.POD_WK_DIR, d)):
                os.makedirs(os.path.join(self.POD_WK_DIR, d))

    def check_pod_driver(self, verbose=0):
        """Private method called by :meth:`~diagnostic.Diagnostic.setUp`.

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
        self.append_result_link(self.exception)

        if not isinstance(self.exception, Exception):
            self.make_pod_html()
            self.convert_pod_figures(os.path.join('model', 'PS'), 'model')
            self.convert_pod_figures(os.path.join('obs', 'PS'), 'obs')
            self.cleanup_pod_files()
            self.verify_pod_links()

        if verbose > 0: 
            print("---  MDTF.py Finished POD "+self.name+"\n")
            # elapsed = timeit.default_timer() - start_time
            # print(pod+" Elapsed time ",elapsed)

    def make_pod_html(self):
        """Perform templating on POD's html results page(s).

        A wrapper for :func:`~util_mdtf.append_html_template`. Looks for all 
        html files in POD_CODE_DIR, templates them, and copies them to 
        POD_WK_DIR, respecting subdirectory structure (see doc for
        :func:`~util.recursive_copy`).
        """
        config = util_mdtf.ConfigManager()
        template = config.global_envvars.copy()
        template.update(self.pod_env_vars)
        source_files = util.find_files(self.POD_CODE_DIR, '*.html')
        util.recursive_copy(
            source_files,
            self.POD_CODE_DIR,
            self.POD_WK_DIR,
            copy_function=lambda src, dest: util_mdtf.append_html_template(
                src, dest, template_dict=template, append=False
            ),
            overwrite=True
        )

    def append_result_link(self, error=None):
        """Update the top level index.html page with a link to this POD's results.

        This simply appends one of two html fragments to index.html: 
        pod_result_snippet.html if the POD completed successfully, or
        pod_error_snippet.html if an exception was raised during the POD's setup
        or execution.

        Args:
            error (default None): :py:class:`Exception` object (if any) that was
                raised during POD's attempted execution. If this is None, assume
                that POD ran successfully.
        """
        src_dir = os.path.join(self.CODE_ROOT, 'src', 'html')
        template_dict = self.__dict__.copy()
        if error is None:
            # normal exit
            src = os.path.join(src_dir, 'pod_result_snippet.html')
        else:
            # report error
            src = os.path.join(src_dir, 'pod_error_snippet.html')
            template_dict['error_text'] = str(error)
        util_mdtf.append_html_template(src, self.TEMP_HTML, template_dict)

    def verify_pod_links(self):
        """Check for missing files linked to from POD's html page.

        See documentation for :class:`~verify_links.LinkVerifier`. This method
        calls LinkVerifier to check existence of all files linked to from the 
        POD's own top-level html page (after templating). If any files are
        missing, an error message listing them is written to the run's index.html 
        (located in src/html/pod_missing_snippet.html).
        """
        verifier = verify_links.LinkVerifier(
            self.POD_HTML, os.path.dirname(self.POD_WK_DIR), verbose=False
        )
        missing_out = verifier.verify_pod_links(self.name)
        if missing_out:
            print('ERROR: {} has missing output files.'.format(self.name))
            template_dict = self.__dict__.copy()
            template_dict['missing_output'] = '<br>'.join(missing_out)
            util_mdtf.append_html_template(
                os.path.join(self.CODE_ROOT,'src','html','pod_missing_snippet.html'),
                self.TEMP_HTML, template_dict
            )

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
            _ = util.run_shell_command(
                'gs {flags} -sOutputFile="{f_out}" {f_in}'.format(
                flags=config.config.get('convert_flags',''),
                f_in=f,
                f_out=f_stem+'_MDTF_TEMP_%d.png'
            ))
            # syntax for f_out above appends "_MDTF_TEMP" + page number to 
            # output files. If input .ps/.pdf file had multiple pages, this will
            # generate 1 png per page. Page numbering starts at 1. Now check 
            # how many files gs created:
            out_files = glob.glob(f_stem+'_MDTF_TEMP_?.png')
            if not out_files:
                raise OSError("Error: no png generated from {}".format(f))
            elif len(out_files) == 1:
                # got one .png, so remove suffix.
                os.rename(out_files[0], f_stem+'.png')
            else:
                # Multiple .pngs. Drop the MDTF_TEMP suffix and renumber starting
                # from zero (forget which POD requires this.)
                for n in list(range(len(out_files))):
                    os.rename(
                        f_stem+'_MDTF_TEMP_{}.png'.format(n+1),
                        f_stem+'-{}.png'.format(n)
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
