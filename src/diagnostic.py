"""Classes representing configuration and status of individual diagnostic scripts
(PODs) and variables required by the scripts.
"""
from abc import ABC
import os
import dataclasses as dc
import io
import itertools
import typing
from pathlib import Path
from src import util, translation, varlistentry_util, varlist_util, data_model, preprocessor

import logging

_log = logging.getLogger(__name__)


class Varlist(data_model.DMDataSet, ABC):
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
                    'self': varlist_util.VarlistTimeCoordinate,
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

        v.stage = varlistentry_util.VarlistEntryStage.INITED

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
            parent: instance of the parent class object

        Returns:
            :py:obj:`dict`, keys are names of the dimensions in POD's convention,
            values are :class:`PodDataDimension` objects.
        """

        def _pod_dimension_from_struct(name, dd, v_settings):
            class_dict = {
                'X': varlist_util.VarlistHorizontalCoordinate,
                'Y': varlist_util.VarlistHorizontalCoordinate,
                'Z': varlist_util.VarlistVerticalCoordinate,
                'T': varlist_util.VarlistPlaceholderTimeCoordinate,
                'OTHER': varlist_util.VarlistCoordinate
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
            parent.pod_data, varlist_util.VarlistSettings)
        globals_d = vlist_settings.global_settings

        dims_d = parent.pod_dims

        vlist_vars = {
            k: varlistentry_util.VarlistEntry.from_struct(globals_d, dims_d, name=k, parent=parent, **v)
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




class NoPPVarlist(Varlist, ABC):
    @classmethod
    def from_struct(cls, d, parent):
        """Parse the "dimensions", "data" and "varlist" sections of the POD's
        settings.jsonc file when instantiating a new :class:`Diagnostic` object.

        Args:
            parent: instance of the parent class object
            d (:py:obj:`dict`): Contents of the POD's settings.jsonc file.

        Returns:
            :py:obj:`dict`, keys are names of the dimensions in POD's convention,
            values are :class:`PodDataDimension` objects.
        """

        def _pod_dimension_from_struct(name, dd, v_settings):
            class_dict = {
                'X': varlist_util.VarlistLongitudeCoordinate,
                'Y': varlist_util.VarlistLatitudeCoordinate,
                'Z': varlist_util.VarlistVerticalCoordinate,
                'T': varlist_util.VarlistPlaceholderTimeCoordinate,
                'OTHER': varlist_util.VarlistCoordinate
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
            d.get('data', dict()), varlist_util.VarlistSettings)
        globals_d = vlist_settings.global_settings

        assert 'dimensions' in d
        dims_d = {k: _pod_dimension_from_struct(k, v, vlist_settings)
                  for k, v in d['dimensions'].items()}

        assert 'varlist' in d
        vlist_vars = {
            k: NoPPVarlistEntry.from_struct(globals_d, dims_d, name=k, parent=parent, **v)
            for k, v in d['varlist'].items()
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


class NoPPVarlistEntry(varlistentry_util.VarlistEntry, varlistentry_util.VarlistEntryMixin):
    use_exact_name: bool = False
    env_var: str = dc.field(default="", compare=False)
    path_variable: str = dc.field(default="", compare=False)
    dest_path: str = ""
    requirement: varlistentry_util.VarlistEntryRequirement = dc.field(
        default=varlistentry_util.VarlistEntryRequirement.REQUIRED, compare=False
    )
    alternates: list = dc.field(default_factory=list, compare=False)
    translation: typing.Any = dc.field(default=None, compare=False)
    data: util.ConsistentDict = dc.field(default_factory=util.ConsistentDict,
                                         compare=False)
    stage: varlistentry_util.VarlistEntryStage = dc.field(
        default=varlistentry_util.VarlistEntryStage.NOTSET, compare=False
    )

    _deactivation_log_level = logging.INFO  # default log level for failure

    @property
    def env_vars(self):
        """Get env var definitions for:
            - The path to the raw data file for this variable,
            - The name for this variable in that data file,
            - The names for all of this variable's coordinate axes in that file,
            - The names of the bounds variables for all of those coordinate
              dimensions, if provided by the data.

        """

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
            d[dim.name + varlistentry_util._coord_env_var_suffix] = trans_dim.name
            if trans_dim.has_bounds:
                d[dim.name + varlistentry_util._coord_bounds_env_var_suffix] = trans_dim.bounds
        return d


@util.mdtf_dataclass
class Diagnostic(util.MDTFObjectBase, util.PODLoggerMixin):
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
    """Test docstring for long_name."""
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

    def __post_init__(self, *args, **kwargs):
        util.MDTFObjectBase.__post_init__(self)
        # set up log (PODLoggerMixin)
        self.init_log()

        for k, v in self.runtime_requirements.items():
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
        config = util.ConfigManager()
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
        for k, v in paths.items():
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
            file_names = [f"{script}{ext}" for script in script_names
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
           Existence of the program on the environment's ``$PATH`` isn't checked
           until before the POD runs (see :mod:`src.environment_manager`.)
        """

        if not self.program:
            # Find ending of filename to determine the program that should be used
            _, driver_ext = os.path.splitext(self.driver)
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
            :meth:`~data_manager.DataManager.fetchData`
            and the runtime environment is validated separately as a function of
            :meth:`~environment_manager.EnvironmentManager.run`. This is because
            each POD is run in a subprocess (due to the necessity of supporting
            multiple languages) so the validation must take place in that
            subprocess.

        Raises:
            :exc:`~diagnostic.PodRuntimeError` if requirements aren't met. This
                is re-raised from the :meth:`diagnostic.Diagnostic.set_entry_point`
                and :meth:`diagnostic.Diagnostic._check_for_varlist_files`
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
                if var.rename_coords is False:
                    pass
                else:
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


@util.mdtf_dataclass
class NoPPDiagnostic(Diagnostic):
    """Class holding configuration for a diagnostic with non-preprocessed variables
    Identical to Diagnostic, but varlist attribute is set to the NoPPVarlist
    """
    varlist: NoPPVarlist = None

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
            pod.varlist = NoPPVarlist.from_struct(d, parent=pod)
        except Exception as exc:
            raise util.PodConfigError("Caught exception while parsing varlist",
                                      pod_name) from exc
        return pod

    def link_input_data_to_wkdir(self):
        if os.path.isdir(self.POD_OBS_DATA) and os.listdir(self.POD_OBS_DATA):
            for f in os.listdir(self.POD_OBS_DATA):
                os.symlink(os.path.join(self.POD_OBS_DATA, f), os.path.join(self.POD_WK_DIR, 'obs', f))

        for v in self.varlist.iter_vars():
            for kk, vv in v.env_vars.items():
                if v.name.lower() + '_file' in kk.lower():
                    path_components = os.path.split(vv)
                    path_split_again = os.path.split(path_components[0])
                    freq = path_split_again[1]
                    # Note--assume that file names adhere to local file convention with variable names
                    # that match those in the POD settings file
                    inpath = os.path.join(self._parent.MODEL_DATA_DIR, freq, path_components[1])
                    Path(path_components[0]).mkdir(parents=True, exist_ok=True)
                    try:
                        os.path.isfile(inpath)
                        os.symlink(os.path.join(self._parent.MODEL_DATA_DIR, freq, path_components[1]), vv)
                    except FileNotFoundError:
                        print("Can't find file", inpath, ". Continuing with run setup. POD may not complete")
                        continue

    def pre_run_setup(self):
        """Perform filesystem operations and checks prior to running the POD.

        In order, this 1) sets environment variables specific to the POD, 2)
        creates POD-specific working directories, and 3) checks for the existence
        of the POD's driver script.

        Raises:
            :exc:`~NoPPdiagnostic.PodRuntimeError` if requirements aren't met. This
                is re-raised from the :meth:`diagnostic.Diagnostic.set_entry_point`
                and :meth:`diagnostic.NoPPDiagnostic._check_for_varlist_files`
                subroutines.
        """
        try:
            self.set_pod_env_vars()
            self.set_entry_point()
            self.link_input_data_to_wkdir()
        except Exception as exc:
            raise util.PodRuntimeError("Caught exception during pre_run_setup",
                                       self) from exc


@util.mdtf_dataclass
class MultirunDiagnostic(pod_setup.MultiRunPod, Diagnostic):
    """Class holding configuration for a Multirun diagnostic script. Object attributes
       are read from entries in the settings section of the POD's settings.jsonc
       file upon initialization.
    """
    # _id = util.MDTF_ID()           # fields inherited from core.MDTFObjectBase
    # name: str
    # _parent: object
    # log = util.MDTFObjectLogger
    # status: ObjectStatus
    # long_name: str = "" # fields inherited from Diagnostic
    # description: str = ""
    # convention: str = "CF"
    # realm: str = ""
    # driver: str = ""
    # program: str = ""
    # runtime_requirements: dict = dc.field(default_factory=dict)
    # pod_env_vars: util.ConsistentDict = dc.field(default_factory=util.ConsistentDict)
    # log_file: io.IOBase = dc.field(default=None, init=False)
    # nc_largefile: bool = False
    # preprocessor: typing.Any = dc.field(default=None, compare=False)
    # POD_CODE_DIR = ""
    # POD_OBS_DATA = ""
    # POD_WK_DIR = ""
    # POD_OUT_DIR = ""
    _deactivation_log_level = logging.ERROR  # default log level for failure
    # recognized interpreters for supported script types; can ovverride with
    # explict 'program' attribute in settings
    _interpreters = {'.py': 'python', '.ncl': 'ncl', '.R': 'Rscript'}
    _PreprocessorClass = preprocessor.MultirunDefaultPreprocessor
    runtime_requirements: dict = dc.field(default_factory=dict)
    MODEL_DATA_DIR = dict()
    MODEL_WK_DIR = dict()
    MODEL_OUT_DIR = dict()
    cases = dict()
    # __post_init__ launches after instantiating the MultirunDiagnostic as-is,
    # or via a method.
    # In this case, it triggers during the from_struct

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(self, *args, **kwargs)  # redirects to Diagnostic.__post_init__ to set up logger
        # configure paths
        config = core.ConfigManager()
        self.overwrite = config.overwrite
        self.strict = config.get('strict', False)

    @property
    def _children(self):
        """Iterable of the cases associated with the multirun diagnostic object
        """
        return self.cases.values()

    # override MDTFFramework.pod_paths
    def pod_paths(self):
        """Check and create directories specific to this POD.
        """
        paths = core.PathManager()
        self.POD_CODE_DIR = os.path.join(paths.CODE_ROOT, 'diagnostics', self.name)
        self.POD_OBS_DATA = os.path.join(paths.OBS_DATA_ROOT, self.name)
        self.POD_WK_DIR = os.path.join(paths.WORKING_DIR, self.name)
        self.POD_OUT_DIR = os.path.join(paths.OUTPUT_DIR, self.name)
        if not self.overwrite:
            # bump both WK_DIR and OUT_DIR to same version because name of
            # former may be preserved when we copy to latter, depending on
            # copy method
            self.POD_WK_DIR, ver = util.bump_version(
                self.POD_WK_DIR, extra_dirs=[paths.OUTPUT_DIR])
            self.POD_OUT_DIR, _ = util.bump_version(self.POD_OUT_DIR, new_v=ver)
        util.check_dir(self.POD_WK_DIR, 'POD_WK_DIR', create=True)
        util.check_dir(self.POD_OUT_DIR, 'POD_OUT_DIR', create=True)
        # append obs and model outdirs
        dirs = ('model/PS', 'model/netCDF', 'obs/PS', 'obs/netCDF')
        for d in dirs:
            util.check_dir(os.path.join(self.POD_WK_DIR, d), create=True)

    def configure_cases(self, case_dict, data_source):
        """ Instantiate case objects, set case directories, and define case attributes
        following the procedure in data_manager:DataSourceBase. Cases are entries in a dictionary that
        is attached to the MultirunDiagnostic object instead of a Diagnostic Object defined in a case
        object in the single run design.
        """
        config = core.ConfigManager()
        paths = core.PathManager()
        translate = core.VariableTranslator()
        for case_name, case_d in case_dict.items():
            # Info for each case is initialized in a Multirun data source object
            self.log.info("###diagnostic.py %s: initializing case '%s'.", self.full_name, case_name)
            # update the dictionary entry for each case
            self.cases[case_name] = data_source(case_d, parent=self)
            self.cases[case_name].overwrite = config.overwrite
            self.cases[case_name].strict = config.get('strict', False)
            # pass case_d as first arg b/c case atts have not yet been defined
            # model_paths will use the FIRSTYR and LASTYR entries in the case_d dict
            # to define the case directories
            d = paths.multirun_model_paths(self, case_d)
            self.MODEL_DATA_DIR[case_name] = d.MODEL_DATA_DIR
            self.MODEL_WK_DIR[case_name] = d.MODEL_WK_DIR
            self.MODEL_OUT_DIR[case_name] = d.MODEL_OUT_DIR
            util.check_dir(self.MODEL_DATA_DIR[case_name], 'MODEL_DATA_DIR', create=True)
            util.check_dir(self.MODEL_WK_DIR[case_name], 'MODEL_WK_DIR', create=True)
            util.check_dir(self.MODEL_OUT_DIR[case_name], 'MODEL_OUT_DIR', create=True)
            # set up log(CaseLoggerMixin)
            self.cases[case_name].init_log(log_dir=self.MODEL_WK_DIR[case_name])
            # Set the case attributes. Pass case_d as first parm b/c it contains the
            # info specified in _AttributesClass (set in data_sources parent classes)
            # In particular, we need FIRSTYR and LASTYR to define the date_range attribute
            # that is set by the data_manager:DataSourceAttributesBase post_init call
            self.cases[case_name].attrs = util.coerce_to_dataclass(
                case_d, self.cases[case_name]._AttributesClass, log=self.log, init=True
            )
            if hasattr(self.cases[case_name], '_convention'):
                self.cases[case_name].convention = self.cases[case_name]._convention
                if hasattr(self.cases[case_name].attrs, 'convention') \
                        and self.cases[case_name].attrs.convention != self.cases[case_name].convention:
                    self.cases[case_name].log.warning(f"{self.cases[case_name].__class__.__name__} requires convention"
                                     f"'{self.cases[case_name].convention}'; ignoring argument "
                                     f"'{self.cases[case_name].attrs.convention}'.")
            elif hasattr(self.cases[case_name].attrs, 'convention') and self.cases[case_name].attrs.convention:
                self.cases[case_name].convention = self.cases[case_name].attrs.convention
            else:
                raise util.GenericDataSourceEvent((f"'convention' not configured "
                                                   f"for {self.cases[case_name].__class__.__name__}."))
            self.cases[case_name].convention = translate.get_convention_name(self.cases[case_name].convention)

            # configure case-specific env vars
            self.cases[case_name].env_vars = util.WormDict.from_struct(
                config.global_env_vars.copy()
            )
            self.cases[case_name].env_vars.update({
                k: case_d[k] for k in ("CASENAME", "FIRSTYR", "LASTYR")
            })
            # add naming-convention-specific env vars
            convention_obj = translate.get_convention(self.cases[case_name].convention)
            self.cases[case_name].env_vars.update(getattr(convention_obj, 'env_vars', dict()))

    def setup_varlist(self, settings_dict):
        """Append the varlist information from the POD settings file in settings_dict
         to each case object
        """
        for case_name, case_d in self.cases.items():
            self.cases[case_name].varlist = MultirunVarlist.from_struct(settings_dict, parent=self)

    def setup(self, data_source, case_dict):
        """Configuration set by the DataSource on the POD (after the POD is
        initialized, but before pre-run checks.)
        """
        # set up the POD paths to the working and output directories
        self.pod_paths()
        # instantiate each case object as a diagnostics.cases entry,
        # define the case paths, attributes, logs, and environment variables
        self.configure_cases(case_dict, data_source)
        # define the location of the POD driver script
        self.set_entry_point()
        self.set_interpreter()
        # TODO: redefine convention as its own entry in the config file similarly to POD_LIST
        # all cases have same convention, so just use first entry for now
        # Will also assume that the date range is the same for all cases for now
        first_case = list(self.cases.items())[0]
        self.convention = first_case[1].convention

        config = core.ConfigManager()
        if config.get('overwrite_file_metadata', False):
            self.log.warning(('User has disabled preprocessing functionality that '
                              'uses input metadata.'), tags=util.ObjectLogTag.BANNER)
        # set up env vars
        # NOTE: will need to work toward referencing case env vars via self.cases[case_name].env_vars
        # single run method uses env_vars.update to copy case info
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

    # cls is a PEP-8 convention to designate a class method
    # class methods modify the class, and thus all instances of the class.
    # Class methods do not modify individual instances; instance
    # methods use the "self" parameter
    @classmethod
    def from_struct(cls, pod_name, d, parent, **kwargs):
        """Instantiate a Diagnostic object from the JSON format used in its
        settings.jsonc file.
        """
        try:
            kwargs.update(d.get('settings', dict()))
            # Instantiate a MultirunDiagnostic object.
            # This call triggers the __post_init__() method of the enclosing MultirunDiagnostic class
            # The name, _parent, and **kwargs parameters are used later in the call tree
            # by several parent init/post_init methods, but are not explicitly defined
            # arguments in all of these methods
            pod = cls(name=pod_name, _parent=parent, **kwargs)
        except Exception as exc:
            raise util.PodConfigError("Caught exception while parsing settings in multirun mode",
                                      pod_name) from exc
        try:
            pod.setup(parent.DataSource, parent.cases)
        except Exception as exc:
            raise util.PodConfigError("Error while running Multirun pod.setup method on ", pod_name) \
                from exc
        try:
            pod.setup_varlist(d)
        except Exception as exc:
            raise util.PodConfigError("Caught exception while parsing multirun settings dict and adding to cases for",
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

    def pre_run_setup(self):
        """Perform filesystem operations and checks prior to running the POD.

        In order, this 1) sets environment variables specific to the POD, 2)
        creates POD-specific working directories, and 3) checks for the existence
        of the POD's driver script.

        Note:
            The existence of data files is checked with
            :meth:`~data_manager.DataManager.fetchData`
            and the runtime environment is validated separately as a function of
            :meth:`~environment_manager.EnvironmentManager.run`. This is because
            each POD is run in a subprocess (due to the necessity of supporting
            multiple languages) so the validation must take place in that
            subprocess.

        Raises:
            :exc:`~diagnostic.PodRuntimeError` if requirements aren't met. This
                is re-raised from the :meth:`diagnostic.Diagnostic.set_entry_point`
                and :meth:`diagnostic.Diagnostic._check_for_varlist_files`
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

        for case_name, case_dict in self.cases.items():
            for var in case_dict.iter_children(status_neq=core.ObjectStatus.ACTIVE):
                # define env vars for varlist entries without data. Name collisions
                # are OK in this case.
                try:
                    self.pod_env_vars.update(var.env_vars)
                except util.WormKeyError:
                    continue


@util.mdtf_dataclass
class MultirunNoPPDiagnostic(MultirunDiagnostic):
    """Class holding configuration for a Multirun diagnostic that will not be preprocessed.
    """
    _PreprocessorClass = preprocessor.MultirunNullPreprocessor

    def pre_run_setup(self):
        """Perform filesystem operations and checks prior to running the POD.

        In order, this 1) sets environment variables specific to the POD, 2)
        creates POD-specific working directories, and 3) checks for the existence
        of the POD's driver script.


        Raises:
            :exc:`~diagnostic.PodRuntimeError` if requirements aren't met. This
                is re-raised from the :meth:`diagnostic.Diagnostic.set_entry_point`
                and :meth:`diagnostic.Diagnostic._check_for_varlist_files`
                subroutines.
        """
        try:
            self.set_pod_env_vars()
            self.set_entry_point()
            self.link_input_data_to_wkdir()
        except Exception as exc:
            raise util.PodRuntimeError("Caught exception during pre_run_setup",
                                       self) from exc

    def link_input_data_to_wkdir(self):
        for case_name, case_dict in self.cases.items():
            for v in case_dict.varlist.iter_vars():
                for kk, vv in v.env_vars.items():
                    if v.name.lower() + '_file' in kk.lower():
                        path_components = os.path.split(vv)
                        path_split_again = os.path.split(path_components[0])
                        freq = path_split_again[1]
                        # Note--assume that file names adhere to local file convention with variable names
                        # that match those in the POD settings file
                        inpath = os.path.join(v._parent.MODEL_DATA_DIR[case_name], freq, path_components[1])
                        try:
                            os.path.isfile(inpath)
                            v.env_vars[kk].replace(vv, inpath)
                        except FileNotFoundError:
                            print("Can't find file", inpath, ". Continuing with run setup. POD may not complete")
                            continue
                v.dest_path = inpath



