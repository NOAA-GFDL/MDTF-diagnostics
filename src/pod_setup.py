"""Classes for POD setup routines previously located in data_manager.DataSourceBase
"""
from abc import ABC
import logging
import os
from src import util, core, diagnostic

_log = logging.getLogger(__name__)


class PodSetupBaseClass(metaclass=util.MDTFABCMeta):
    """Base class for POD setup methods
    """
    def setup_pod(self, pod):
        pass

    def setup_var(self, pod, v):
        pass

    def variable_dest_path(self):
        pass


class SingleRunPod(PodSetupBaseClass, ABC):

    def setup_pod(self, pod):
        """Update POD with information that only becomes available after
        DataManager and Diagnostic have been configured (ie, only known at
        runtime, not from settings.jsonc.)

        Could arguably be moved into Diagnostic's init, at the cost of
        dependency inversion.
        """
        pod.setup(self)
        for v in pod.iter_children():
            try:
                self.setup_var(pod, v)
            except Exception as exc:
                chained_exc = util.chain_exc(exc, f"configuring {v.full_name}.",
                                             util.PodConfigError)
                v.deactivate(chained_exc)
                continue
        # preprocessor will edit varlist alternates, depending on enabled functions
        pod.preprocessor = self._PreprocessorClass(self, pod)
        pod.preprocessor.edit_request(self, pod)

        for v in pod.iter_children():
            # deactivate failed variables, now that alternates are fully
            # specified
            if v.last_exception is not None and not v.failed:
                v.deactivate(v.last_exception, level=logging.WARNING)
        if pod.status == core.ObjectStatus.NOTSET and \
                any(v.status == core.ObjectStatus.ACTIVE for v in pod.iter_children()):
            pod.status = core.ObjectStatus.ACTIVE

    def setup_var(self, pod, v):
        """Update VarlistEntry fields with information that only becomes
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
                    'self': diagnostic.VarlistTimeCoordinate,
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
            if hasattr(trans_v,"rename_coords"):
                v.rename_coords = trans_v.rename_coords
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

        v.stage = diagnostic.VarlistEntryStage.INITED

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


class MultiRunPod(PodSetupBaseClass, ABC):
    # MultiRunDiagnostic class inherits directly from MultiRunPod class
    # and there is no need to define a 'pod' parameter

    def setup_pod(self):
        """Update POD with information that only becomes available after
        DataManager and Diagnostic have been configured (i.e., only known at
        runtime, not from settings.jsonc.)
        """
        for case_name, case_dict in self.cases.items():
            for v in case_dict.iter_children():
                try:
                    self.setup_var(v, case_dict.attrs.date_range, case_dict.name)
                except Exception as exc:
                    chained_exc = util.chain_exc(exc, f"configuring {v.full_name} in multirun mode.",
                                                 util.PodConfigError)
                    v.deactivate(chained_exc)
                    continue
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
                    'self': diagnostic.VarlistTimeCoordinate,
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

        v.stage = diagnostic.VarlistEntryStage.INITED

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
