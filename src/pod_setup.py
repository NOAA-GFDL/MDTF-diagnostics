"""Classes for POD setup routines previously located in data_manager.DataSourceBase
"""
from abc import ABC
import logging
import os
import io
from pathlib import Path
from typing import Type

from src import cli, util, data_sources, translation, varlistentry_util, varlist_util
import intake_esm
import dataclasses as dc

_log = logging.getLogger(__name__)


class PodBaseClass(metaclass=util.MDTFABCMeta):
    """Base class for POD setup methods
    """
    def parse_pod_settings_file(self, code_root: str):
        pass

    def setup_pod(self, config: util.NameSpace):
        pass

    def setup_var(self, pod, v):
        pass


class PodObject(util.PODLoggerMixin, util.MDTFObjectBase, PodBaseClass, ABC):
    """Class to hold pod information"""
    # name: str  Class atts inherited from MDTFObjectBase
    # _id
    # _parent: object
    # status: ObjectStatus
    pod_dims = util.NameSpace
    pod_vars = util.NameSpace
    pod_settings = util.NameSpace
    cases = util.NameSpace

    MODEL_DATA_DIR = dict()
    MODEL_WORK_DIR = dict()
    MODEL_OUT_DIR = dict()

    overwrite: bool = False
    # explict 'program' attribute in settings
    _interpreters = {'.py': 'python', '.ncl': 'ncl', '.R': 'Rscript'}
    runtime_requirements: dict = dc.field(default_factory=dict)
    driver: str = ""
    program: str = ""
    pod_env_vars: util.ConsistentDict = dc.field(default_factory=util.ConsistentDict)
    log_file: io.IOBase = dc.field(default=None, init=False)
    nc_largefile: bool = False
    log_file: io.IOBase = dc.field(default=None, init=False)

    def __init__(self, name: str, runtime_config: util.NameSpace):
        self.name = name
        self.init_log()
        # define global environment variables: those that apply to the entire POD
        self.pod_env_vars = os.environ.copy()
        self.pod_env_vars['RGB'] = os.path.join(runtime_config.code_root, 'shared', 'rgb')
        # globally enforce non-interactive matplotlib backend
        # see https://matplotlib.org/3.2.2/tutorials/introductory/usage.html#what-is-a-backend
        self.pod_env_vars['MPLBACKEND'] = "Agg"
        self.nc_largefile = runtime_config.large_file
        # set up work/output directories
        self.paths = util.PathManager(runtime_config, self.global_env_vars)
        self.paths.set_pod_paths(self.name, runtime_config, self.global_env_vars)

    @property
    def _log_name(self):
        # POD loggers sit in a subtree of the DataSource logger distinct from
        # the DataKey loggers; the two subtrees are distinguished by class name
        _log_name = f"{self.name}_{self._id}".replace('.', '_')
        return f"{self._parent._log_name}.{self.__class__.__name__}.{_log_name}"

    def close_log_file(self, log=True):
        if self.log_file is not None:
            if log:
                self.log_file.write(self.format_log(children=False))
            self.log_file.close()

    def parse_pod_settings_file(self, code_root: str) -> util.NameSpace:
        """Parse the POD settings file"""
        settings_file_query = Path(code_root, 'diagnostics', self.name).glob('*settings.*')
        settings_file_path = str([p for p in settings_file_query][0])
        # Use wildcard to support settings file in yaml and jsonc format
        settings_dict = cli.parse_config_file(settings_file_path)
        return util.NameSpace.fromDict({k: settings_dict[k] for k in settings_dict.keys()})

    def _get_pod_settings(self, pod_settings_dict: util.NameSpace):
        self.pod_settings = util.NameSpace.toDict(pod_settings_dict.settings)

    def _get_pod_dims(self, pod_settings_dict: util.NameSpace):
        self.pod_dims = util.NameSpace.toDict(pod_settings_dict.dims)

    def _get_pod_vars(self, pod_settings_dict: util.NameSpace):
        self.pod_vars = util.NameSpace.toDict(pod_settings_dict.vars)

    def get_pod_data_subset(self, catalog_path, case_list):
        cat = intake.open_esm_datastore(catalog_path)
        # filter catalog by desired variable and output frequency
        tas_subset = cat.search(variable_id=tas_var, frequency="day")

    def query_files_in_time_range(self, startdate, enddate):
        pass

    def append_pod_env_vars(self, pod_input):
        self.global_env_vars.update(v for v in pod_input.pod_env_vars)

    def set_entry_point(self):
        """Locate the top-level driver script for the POD.

        Raises: :class:`~util.PodRuntimeError` if driver script can't be found.
        """
        if not self.pod_settings.driver:
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
                    break  # go with the first one found
        if not self.driver:
            raise util.PodRuntimeError((f"No driver script found in "
                                        f"{self.POD_CODE_DIR}. Specify 'driver' in settings.jsonc."),
                                       self)

        if not os.path.isabs(self.driver):  # expand relative path
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

    def setup_pod(self, runtime_config: util.NameSpace,):
        """Update POD information
        """
        # Parse the POD settings file
        pod_input = self.parse_pod_settings_file(runtime_config.code_root)
        self._get_pod_settings(pod_input)
        self._get_pod_vars(pod_input)
        self._get_pod_dims(pod_input)

        # run the PODs on data that has already been preprocessed
        # PODs will ingest input directly from catalog that (should) contain
        # the information for the saved preprocessed files, and a pre-existing case_env file
        if runtime_config.persist_data:
            pass
        elif runtime_config.run_pp:

            for case_name, case_dict in runtime_config.case_list.items():
                # instantiate the data_source class instance for the specified convention
                self.cases.case_name = data_sources.data_source[case_dict.convention.upper() +
                                                                "DataSource"](case_dict, parent=self)

                #util.NameSpace.fromDict({k: case_dict[k] for k in case_dict.keys()})
                if self.pod_settings.convention != case_dict.convention:
                    # translate variable(s) to user_specified standard if necessary

                    self.cases.case_name.varlist = Varlist.from_struct(case_dict)
                else:
                    pass


            # get level

        else:
            pass
        # run custom scripts on dataset
        if any([s for s in runtime_config.my_scripts]):
            pass

        # ref for dict comparison
        # https://stackoverflow.com/questions/20578798/python-find-matching-values-in-nested-dictionary

        cat_subset = get_pod_data_subset(runtime_config.CATALOG_PATH, runtime_config.case_list)

        self.setup_var(v, case_dict.attrs.date_range, case_name)

        # preprocessor will edit case varlist alternates, depending on enabled functions
        # self is the Mul
        self.preprocessor = self._PreprocessorClass(self)
        # self=MulirunDiagnostic instance, and is passed as data_mgr parm to access
        # cases
        self.preprocessor.edit_request(self)

        for case_name, case_dict in self.cases.items():
            for v in case_dict.iter_children():
                # deactivate failed variables, now that alternates are fully
                # specified
                if v.last_exception is not None and not v.failed:
                    v.deactivate(v.last_exception, level=logging.WARNING)
            if case_dict.status == util.ObjectStatus.NOTSET and \
                    any(v.status == util.ObjectStatus.ACTIVE for v in case_dict.iter_children()):
                case_dict.status = util.ObjectStatus.ACTIVE
        # set MultirunDiagnostic object status to Active if all case statuses are Active
        if self.status == util.ObjectStatus.NOTSET and \
                all(case_dict.status == util.ObjectStatus.ACTIVE for case_name, case_dict in self.cases.items()):
            self.status = util.ObjectStatus.ACTIVE

    def setup_var(self, v, date_range: util.DateRange, case_name: str):
        """Update VarlistEntry fields "v" with information that only becomes
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
                range=date_range,
                calendar=util.NOTSET,
                units=util.NOTSET
            )

        v.dest_path = self.variable_dest_path(v, case_name)
        try:
            trans_v = translate.translate(v)
            v.translation = trans_v
            # copy preferred gfdl post-processing component during translation
            if hasattr(trans_v, "component"):
                v.component = trans_v.component
            if hasattr(trans_v,"rename_coords"):
                v.rename_coords = trans_v.rename_coords
        except KeyError as exc:
            # can happen in normal operation (eg. precip flux vs. rate)
            chained_exc = util.PodConfigEvent((f"Deactivating {v.full_name} for multirun case {case_name} due to "
                                               f"variable name translation: {str(exc)}."))
            # store but don't deactivate, because preprocessor.edit_request()
            # may supply alternate variables
            v.log.store_exception(chained_exc)
        except Exception as exc:
            chained_exc = util.chain_exc(exc, f"translating name of {v.full_name} for multirun case {case_name}.",
                                         util.PodConfigError)
            # store but don't deactivate, because preprocessor.edit_request()
            # may supply alternate variables
            v.log.store_exception(chained_exc)

        v.stage = varlistentry_util.VarlistEntryStage.INITED

    def variable_dest_path(self, var, case_name):
        """Returns the absolute path of the POD's preprocessed, local copy of
        the file containing the requested dataset. Files not following this
        convention won't be found by the POD.
        """
        # TODO add option for file(s) with just the var name in a designated directory
        # Would involve a regex search for the variable name for a single file, or match
        # all files in a specified file list (txt file, json, yaml)

        if var.is_static:
            f_name = f"{case_name}.{var.name}.static.nc"
            return os.path.join(self.MODEL_WK_DIR[case_name], f_name)
        else:
            freq = var.T.frequency.format_local()
            f_name = f"{case_name}.{var.name}.{freq}.nc"
            return os.path.join(self.MODEL_WK_DIR[case_name], freq, f_name)
