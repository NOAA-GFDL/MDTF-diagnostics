"""Code specific to the computing environment at NOAA's Geophysical Fluid
Dynamics Laboratory (Princeton, NJ, USA).
"""
import os
from abc import ABC
from src import util, multirun, core, diagnostic, preprocessor
from sites.NOAA_GFDL import gfdl_util, gfdl

import logging
_log = logging.getLogger(__name__)


@util.mdtf_dataclass
class MultirunGfdlDiagnostic(diagnostic.MultirunDiagnostic,
                             gfdl.GfdlDiagnostic):
    """Wrapper for MultirunDiagnostic that adds writing a placeholder directory
    (POD_OUT_DIR) to the output as a lockfile if we're running in frepp
    cooperative mode.
    """
    # extra dataclass fields
    # _has_placeholder: bool = False

    def pre_run_setup(self):
        """Extra code only applicable in frepp cooperative mode. If this code is
        called, all the POD's model data has been generated. Write a placeholder
        directory to POD_OUT_DIR, so if frepp invokes the MDTF package again
        while we're running, only our results will be written to the overall
        output.
        """
        super(MultirunGfdlDiagnostic, self).pre_run_setup()

        config = core.ConfigManager()
        frepp_mode = config.get('frepp', False)
        if frepp_mode and not os.path.exists(self.POD_OUT_DIR):
            try:
                gfdl_util.make_remote_dir(self.POD_OUT_DIR, log=self.log)
                self._has_placeholder = True
            except Exception as exc:
                chained_exc = util.chain_exc(exc, (f"Making output directory at "
                                                   f"{self.POD_OUT_DIR}."), util.PodRuntimeError)
                self.deactivate(chained_exc)


class MultirunGfdludacmip6DataManager(multirun.MultirunDataframeQueryDataSourceBase,
                                      gfdl.Gfdludacmip6DataManager, ABC
                                      ):
    """DataSource for accessing CMIP6 data stored on spinning disk at /uda/CMIP6.
    """
    # _FileRegexClass = cmip6.CMIP6_DRSPath
    # _DirectoryRegex = cmip6.drs_directory_regex
    # _AttributesClass = GFDL_UDA_CMIP6DataSourceAttributes
    # _fetch_method = "cp"  # copy locally instead of symlink due to NFS hanging
    _DiagnosticClass = MultirunGfdlDiagnostic
    _PreprocessorClass = preprocessor.MultirunDefaultPreprocessor


class MultirunGfdldatacmip6DataManager(multirun.MultirunDataframeQueryDataSourceBase,
                                       gfdl.Gfdldatacmip6DataManager, ABC
                                       ):
    """DataSource for accessing pre-publication CMIP6 data on /data_cmip6.
    """
    # _FileRegexClass = cmip6.CMIP6_DRSPath
    # _DirectoryRegex = cmip6.drs_directory_regex
    # _AttributesClass = GFDL_data_CMIP6DataSourceAttributes
    # _fetch_method = "gcp"
    _DiagnosticClass = MultirunGfdlDiagnostic
    _PreprocessorClass = preprocessor.MultirunDefaultPreprocessor


class MultirunGfdlAutoDataManager(gfdl.GfdlautoDataManager):
    """Wrapper for dispatching DataManager based on user input. If CASE_ROOT_DIR
    ends in "pp", use :class:`MultirunGfdlppDataManager`, otherwise use CMIP6 data on
    /uda via :class:`MultirunGfdludacmip6DataManager`.
    """
    # Note, object is explicitly defined as a parameter for Python 2/3
    # compatibility reasons; omitting object in Python2 yields "old-style" classes
    # All classes are "new-style" in Python3 by default.
    # TODO: Since WE DO NOT SUPPORT PYTHON2, remove object parm and verify that it doesn't destroy everything
    def __new__(cls, case_dict, parent, *args, **kwargs):
        """Dispatch DataManager instance creation based on the contents of
        case_dict."""
        config = core.ConfigManager()
        dir_ = case_dict.get('CASE_ROOT_DIR', config.CASE_ROOT_DIR)
        if 'pp' in os.path.basename(os.path.normpath(dir_)):
            dispatched_cls = MultirunGfdlAutoDataManager
        else:
            dispatched_cls = MultirunGfdludacmip6DataManager
            # could use more careful logic here, but for now assume CMIP6 on
            # /uda as a fallback

        _log.debug("%s: Dispatched DataManager to %s.",
                   cls.__name__, dispatched_cls.__name__)
        obj = dispatched_cls.__new__(dispatched_cls)
        obj.__init__(case_dict, parent)
        return obj


class MultirunGfdlppDataManager(multirun.MultirunDataframeQueryDataSourceBase,
                                gfdl.GfdlppDataManager):
    # _FileRegexClass = PPTimeseriesDataFile
    # _DirectoryRegex = pp_dir_regex
    # _AttributesClass = PPDataSourceAttributes
    # _fetch_method = 'auto'  # symlink if not on /archive, else gcp

    _DiagnosticClass = MultirunGfdlDiagnostic
    _PreprocessorClass = preprocessor.MultirunDefaultPreprocessor

    # map "name" field in VarlistEntry's query_attrs() to "variable" field of
    # PPTimeseriesDataFile
    # _query_attrs_synonyms = {'name': 'variable'}

    def __init__(self, case_dict, parent):
        super(MultirunGfdlppDataManager, self).__init__(case_dict, parent)
        # default behavior when run interactively:
        # frepp_mode = False, any_components = True
        # default behavior when invoked by FRE wrapper:
        # frepp_mode = True (set to False by calling wrapper with --run_once)
        # any_components = True (set to False with --component_only)
        config = core.ConfigManager()
        self.frepp_mode = config.get('frepp', False)
        self.any_components = config.get('any_components', False)