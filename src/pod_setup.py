"""Classes for POD setup routines previously located in data_manager.DataSourceBase
"""
from abc import ABC
import logging
import os
from pathlib import Path
from src import cli, util, varlistentry_util, varlist_util
import intake_esm

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


class PodObject(PodBaseClass, ABC):
    """Class to hold pod information"""
    name = str
    pod_dims = dict
    pod_vars = dict
    pod_settings = dict

    def __init__(self, name: str):
        self.name = name

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
    def setup_pod(self, runtime_config: util.NameSpace):
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
            # translate variable(s) to user_specified standard if necessary

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
            if case_dict.status == core.ObjectStatus.NOTSET and \
                    any(v.status == core.ObjectStatus.ACTIVE for v in case_dict.iter_children()):
                case_dict.status = core.ObjectStatus.ACTIVE
        # set MultirunDiagnostic object status to Active if all case statuses are Active
        if self.status == core.ObjectStatus.NOTSET and \
                all(case_dict.status == core.ObjectStatus.ACTIVE for case_name, case_dict in self.cases.items()):
            self.status = core.ObjectStatus.ACTIVE

    def setup_var(self, v, date_range: util.DateRange, case_name: str):
        """Update VarlistEntry fields "v" with information that only becomes
        available after DataManager and Diagnostic have been configured (ie,
        only known at runtime, not from settings.jsonc.)

        Could arguably be moved into VarlistEntry's init, at the cost of
        dependency inversion.
        """
        translate = core.VariableTranslator().get_convention(self.convention)
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
