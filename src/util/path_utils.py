"""Utility functions for defining directory paths
"""
import os
from . import check_dir
from . import exit_handler
from . import Singleton
from . import NameSpace
from . import from_iter
from . import resolve_path
import shutil
from . import filesystem
import logging
_log = logging.getLogger(__name__)


class PathManagerBase:
    """:class:`~util.Singleton` holding the root directories for all paths used
    by the code.
    """
    WORK_DIR: str
    OUTPUT_DIR: str
    TEMP_DIR_ROOT: str
    CODE_ROOT: str
    OBS_DATA_ROOT: str
    _unittest: bool = False

    def __init__(self, config: NameSpace = None,
                 env: dict = None,
                 unittest: bool = False,
                 new_work_dir: bool = True):
        self._unittest = unittest
        if self._unittest:
            for path in ['CODE_ROOT', 'OBS_DATA_ROOT',
                         'WORK_DIR', 'OUTPUT_DIR']:
                setattr(self, path, 'TEST_' + path)
            self.TEMP_DIR_ROOT = self.WORK_DIR
        else:
            # normal code path
            self.CODE_ROOT = config.CODE_ROOT
            assert os.path.isdir(self.CODE_ROOT)

            # set following explicitly: redundant, but keeps linter from complaining
            if hasattr(config, "OBS_DATA_ROOT"):
                self.OBS_DATA_ROOT = self._init_path('OBS_DATA_ROOT', config, env=env)
            if 'MDTF_output' not in config.WORK_DIR:
                self.WORK_DIR = os.path.join(self._init_path('WORK_DIR', config, env=env),
                                             'MDTF_output')
            else:
                self.WORK_DIR = os.path.join(self._init_path('WORK_DIR', config, env=env))

            if not hasattr(config, 'OUTPUT_DIR'):
                self.OUTPUT_DIR = self.WORK_DIR
            elif len(config['OUTPUT_DIR']) < 1:
                self.OUTPUT_DIR = self.WORK_DIR
            else:
                if 'MDTF_output' not in config.WORK_DIR:
                    self.OUTPUT_DIR = os.path.join(self._init_path('OUTPUT_DIR', config, env=env),
                                                   'MDTF_output')
                else:
                    self.OUTPUT_DIR = os.path.join(self._init_path('OUTPUT_DIR', config, env=env))

            if new_work_dir:
                output_dir_main = os.path.abspath(os.path.join(self.OUTPUT_DIR, ".."))
                self.WORK_DIR, ver = filesystem.bump_version(
                    self.WORK_DIR, extra_dirs=[output_dir_main])
                self.OUTPUT_DIR, _ = filesystem.bump_version(self.OUTPUT_DIR, new_v=ver)

            # set root directory for TempDirManager
            if not getattr(self, 'TEMP_DIR_ROOT', ''):
                if env is not None and 'MDTF_TMPDIR' in env:
                    self.TEMP_DIR_ROOT = env['MDTF_TMPDIR']
                else:
                    # default to writing temp files in working directory
                    self.TEMP_DIR_ROOT = self.WORK_DIR

    def _init_path(self, key, d, env=None):
        if self._unittest:  # use in unit testing only
            return 'TEST_'+key
        else:
            # need to check existence in case we're being called directly
            if not d.get(key, False):
                _log.fatal(f"Error: {key} not initialized.")
                exit_handler(code=1)
            return resolve_path(
                from_iter(d[key]), root_path=self.CODE_ROOT,
                env_vars=env,
                log=_log
            )


class PodPathManager(PathManagerBase):
    POD_WORK_DIR: str
    POD_OUTPUT_DIR: str
    POD_OBS_DATA: str
    POD_CODE_DIR: str

    def __init__(self, pod_name: str,
                 config: NameSpace = None,
                 env: dict = None,
                 unittest: bool = False,
                 new_work_dir: bool = True):

        super().__init__(config, env, unittest, new_work_dir)

        self.POD_CODE_DIR = os.path.join(self.CODE_ROOT, 'diagnostics', pod_name)
        self.POD_WORK_DIR = os.path.join(self.WORK_DIR, pod_name)
        self.POD_OUTPUT_DIR = os.path.join(self.OUTPUT_DIR, pod_name)
        if any(self.OBS_DATA_ROOT):
            self.POD_OBS_DATA = os.path.join(self.OBS_DATA_ROOT, pod_name)
        filesystem.check_dir(self.POD_WORK_DIR, 'POD_WORK_DIR', create=True)
        filesystem.check_dir(self.POD_OUTPUT_DIR, 'POD_OUTPUT_DIR', create=True)
        # OBS data are unique to POD, so the obs output is copied to the POD subdirectory
        dirs = ('model/PS', 'model/netCDF', 'obs/PS', 'obs/netCDF')
        for d in dirs:
            filesystem.check_dir(os.path.join(self.POD_WORK_DIR, d), create=True)


class ModelDataPathManager(PathManagerBase):
    MODEL_DATA_ROOT: str
    MODEL_DATA_DIR: dict
    MODEL_WORK_DIR: dict
    MODEL_OUTPUT_DIR: dict

    def __init__(self, config: NameSpace,
                 env=None,
                 unittest: bool = False,
                 new_work_dir: bool = False):
        super().__init__(config, env, unittest, new_work_dir)

        if hasattr(config, "MODEL_DATA_ROOT"):
            self.MODEL_DATA_ROOT = self._init_path('MODEL_DATA_ROOT', config, env=env)
        else:
            self.MODEL_DATA_ROOT = ""
        self.MODEL_DATA_DIR = dict()
        self.MODEL_OUTPUT_DIR = dict()
        self.MODEL_WORK_DIR = dict()

    def setup_data_paths(self, case_list: NameSpace):
        # define directory paths for multirun mode
        # Each case directory is a subdirectory in wk_dir/pod_name
        for case_name, case_dict in case_list.items():
            if case_dict.startdate in case_name and case_dict.enddate in case_name:
                case_wk_dir = 'MDTF_{}'.format(case_name)
            else:
                startdate = case_dict.startdate.format(precision=1)
                enddate = case_dict.enddate.format(precision=1)
                case_wk_dir = 'MDTF_{}_{}_{}'.format(case_name, startdate, enddate)
            # TODO: Remove refs to MODEL_DATA_ROOT when catalogs are implemented in
            # older PODs
            # Model data DIR retained for backwards compatibility
            if len(self.MODEL_DATA_ROOT) > 1:
                self.MODEL_DATA_DIR[case_name] = os.path.join(self.MODEL_DATA_ROOT, case_name)
                filesystem.check_dir(self.MODEL_DATA_DIR[case_name], 'MODEL_DATA_DIR', create=False)
                # Cases are located in a common POD directory
            self.MODEL_WORK_DIR[case_name] = os.path.join(self.WORK_DIR, case_wk_dir)
            self.MODEL_OUTPUT_DIR[case_name] = os.path.join(self.OUTPUT_DIR, case_wk_dir)

            filesystem.check_dir(self.MODEL_WORK_DIR[case_name], 'MODEL_WORK_DIR', create=True)
            filesystem.check_dir(self.MODEL_OUTPUT_DIR[case_name], 'MODEL_OUTPUT_DIR', create=True)


def verify_paths(config, p):
    # needs to be here, instead of PathManager, because we subclass it in
    # NOAA_GFDL
    keep_temp = config.get('keep_temp', False)
    # clean out WORKING_DIR if we're not keeping temp files:
    if os.path.exists(p.WORK_DIR) and not \
            (keep_temp or p.WORK_DIR == p.OUTPUT_DIR):
        shutil.rmtree(p.WORK_DIR)

    try:
        check_dirs = (('CODE_ROOT', False), ('MODEL_DATA_ROOT', True), ('WORK_DIR', True))
        if hasattr(config, 'OBS_DATA_ROOT'):
            check_dirs.append('OBS_DATA_ROOT', False)
        for dir_name, create_ in check_dirs:
            check_dir(p, dir_name, create=create_)
    except Exception as exc:
        _log.fatal((f"Input settings for {dir_name} mis-specified (caught "
                    f"{repr(exc)}.)"))
        exit_handler(code=1)
