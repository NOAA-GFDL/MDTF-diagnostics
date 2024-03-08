"""Code specific to the computing environment at NOAA's Geophysical Fluid
Dynamics Laboratory (Princeton, NJ, USA).
"""
import io
import os
from abc import ABC
from src import util, multirun, core, diagnostic, preprocessor, output_manager
from src import query_fetch_preprocess as qfp
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


class MultirunGfdlarchivecmip6DataManager(Multirun_GFDL_GCP_FileDataSourceBase,
                                          gfdl.Gfdlarchivecmip6DataManager, ABC):
    """DataSource for accessing more extensive set of CMIP6 data on DMF tape-backed
    storage at /archive/pcmdi/repo/CMIP6.
    """
    #_FileRegexClass = cmip6.CMIP6_DRSPath
    #_DirectoryRegex = cmip6.drs_directory_regex
    #_AttributesClass = GFDL_archive_CMIP6DataSourceAttributes
    # _fetch_method = "gcp"
    # borrow MDTFObjectBase initialization from data_manager:~DataSourceBase

    def __init__(self, case_dict, parent):
        super(MultirunGfdlarchivecmip6DataManager, self).__init__(case_dict, parent)

class MultirunGfdludacmip6DataManager(Multirun_GFDL_GCP_FileDataSourceBase,
                                      gfdl.Gfdludacmip6DataManager, ABC
                                      ):
    """DataSource for accessing CMIP6 data stored on spinning disk at /uda/CMIP6.
    """
    # _FileRegexClass = cmip6.CMIP6_DRSPath
    # _DirectoryRegex = cmip6.drs_directory_regex
    # _AttributesClass = GFDL_UDA_CMIP6DataSourceAttributes
    # _fetch_method = "cp"  # copy locally instead of symlink due to NFS hanging
    # _DiagnosticClass = MultirunGfdlDiagnostic
    # _PreprocessorClass = preprocessor.MultirunDefaultPreprocessor

    def __init__(self, case_dict, parent):
        super(MultirunGfdludacmip6DataManager, self).__init__(case_dict, parent)


class MultirunGfdldatacmip6DataManager(Multirun_GFDL_GCP_FileDataSourceBase,
                                       gfdl.Gfdldatacmip6DataManager, ABC
                                       ):
    """DataSource for accessing pre-publication CMIP6 data on /data_cmip6.
    """
    # _FileRegexClass = cmip6.CMIP6_DRSPath
    # _DirectoryRegex = cmip6.drs_directory_regex
    # _AttributesClass = GFDL_data_CMIP6DataSourceAttributes
    # _fetch_method = "gcp"
    # _DiagnosticClass = MultirunGfdlDiagnostic
    # _PreprocessorClass = preprocessor.MultirunDefaultPreprocessor

    def __init__(self, case_dict, parent):
        super(MultirunGfdldatacmip6DataManager, self).__init__(case_dict, parent)


class MultirunGfdlAutoDataManager(gfdl.GfdlAutoDataManager):
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
            dispatched_cls = MultirunGfdlppDataManager
        else:
            dispatched_cls = MultirunGfdludacmip6DataManager
            # could use more careful logic here, but for now assume CMIP6 on
            # /uda as a fallback

        _log.debug("%s: Dispatched DataManager to %s.",
                   cls.__name__, dispatched_cls.__name__)
        obj = dispatched_cls.__new__(dispatched_cls)
        obj.__init__(case_dict, parent)
        return obj


class MultirunGfdlppDataManager(Multirun_GFDL_GCP_FileDataSourceBase,
                                gfdl.GfdlppDataManager):
    # _FileRegexClass = PPTimeseriesDataFile
    # _DirectoryRegex = pp_dir_regex
    # _AttributesClass = PPDataSourceAttributes
    # _fetch_method = 'auto'  # symlink if not on /archive, else gcp
    # map "name" field in VarlistEntry's query_attrs() to "variable" field of
    # PPTimeseriesDataFile
    # _query_attrs_synonyms = {'name': 'variable'}
    # _DiagnosticClass = MultirunGfdlDiagnostic
    # _PreprocessorClass = preprocessor.MultirunDefaultPreprocessor
    def __init__(self, case_dict, parent):
        super(MultirunGfdlppDataManager, self).__init__(case_dict, parent)

class MultirunGFDLHTMLOutputManager(output_manager.MultirunHTMLOutputManager,
                                    gfdl.GFDLHTMLOutputManager):
    _PodOutputManagerClass = gfdl.GFDLHTMLPodOutputManager

    def __init__(self, pod):
        config = core.ConfigManager()
        try:
            self.frepp_mode = config.get('frepp', False)
            self.dry_run = config.get('dry_run', False)
            self.timeout = config.get('file_transfer_timeout', 0)
        except (AttributeError, KeyError) as exc:
            pod.log.store_exception(exc)

        super(MultirunGFDLHTMLOutputManager, self).__init__(pod)

    def make_html(self, cleanup=False):
        """Never cleanup html if we're in frepp_mode, since framework may run
        later when another component finishes. Instead just append current
        progress to CASE_TEMP_HTML.
        """
        prev_html = os.path.join(self.OUT_DIR, self._html_file_name)
        if self.frepp_mode and os.path.exists(prev_html):
            self.obj.log.debug("Found previous HTML at %s; appending.", self.OUT_DIR)
            with io.open(prev_html, 'r', encoding='utf-8') as f1:
                contents = f1.read()
            contents = contents.split('<!--CUT-->')
            assert len(contents) == 3
            contents = contents[1]

            if os.path.exists(self.CASE_TEMP_HTML):
                mode = 'a'
            else:
                self.obj.log.warning("No file at %s.", self.CASE_TEMP_HTML)
                mode = 'w'
            with io.open(self.CASE_TEMP_HTML, mode, encoding='utf-8') as f2:
                f2.write(contents)
        super(MultirunGFDLHTMLOutputManager, self).make_html(
            cleanup=(not self.frepp_mode)
        )
