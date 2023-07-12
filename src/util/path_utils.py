"""Utility functions for defining directory paths
"""
import os
import io
import glob
from . import check_dir
from . import exit_handler
from . import Singleton
from . import NameSpace
from . import from_iter
from . import resolve_path
import shutil
from . import filesystem
import string
from . import basic
from . import exceptions
import yaml

import logging
_log = logging.getLogger(__name__)


class PathManager(metaclass=Singleton):
    """:class:`~util.Singleton` holding the root directories for all paths used
    by the code.
    """
    WORK_DIR: str
    OUTPUT_DIR: str
    TEMP_DIR_ROOT: str
    CODE_ROOT: str
    OBS_DATA_ROOT: str
    POD_WORK_DIR: str
    POD_OUT_DIR: str
    POD_OBS_DATA: str
    POD_CODE_DIR: str
    MODEL_DATA_DIR: str
    MODEL_WORK_DIR: str
    MODEL_OUT_DIR: str

    overwrite: bool = False

    _unittest: bool = False

    def __init__(self, config: NameSpace = None,
                 env: dict = None, unittest: bool = False):
        self.POD_OBS_DATA = ""
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
            self.OBS_DATA_ROOT = self._init_path('OBS_DATA_ROOT', config, env=env)
            self.WORK_DIR = self._init_path('WORK_DIR', config, env=env)
            self.OUTPUT_DIR = self._init_path('OUTPUT_DIR', config, env=env)

            if not self.OUTPUT_DIR:
                self.OUTPUT_DIR = self.WORK_DIR

            if not config.persist_data:
                self.overwrite = True

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

    def model_paths(self, pod_name: str, case: dict):
        # define directory paths for multirun mode
        # Each case directory is a subdirectory in wk_dir/pod_name
        startdate = case.attrs.date_range.start.format(precision=1)
        enddate = case.attrs.date_range.end.format(precision=1)
        case_wk_dir = 'MDTF_{}_{}_{}'.format(case, startdate, enddate)
        self.MODEL_DATA_DIR = os.path.join(self.MODEL_DATA_ROOT, pod_name)
        # Cases are located in a common POD directory
        self.MODEL_WORK_DIR = os.path.join(self.POD_WORK_DIR, case_wk_dir)
        self.MODEL_OUT_DIR = os.path.join(self.POD_OUT_DIR, case_wk_dir)

    def set_pod_paths(self, pod_name: str, config: NameSpace, env_vars: dict):
        """Check and create directories specific to this POD.
        """

        self.POD_CODE_DIR = os.path.join(config.CODE_ROOT, 'diagnostics', pod_name)
        if hasattr(config, "OBS_DATA_ROOT"):
            self.POD_OBS_DATA = os.path.join(config.OBS_DATA_ROOT, pod_name)
        self.POD_WORK_DIR = os.path.join(config.WORK_DIR, pod_name)
        self.POD_OUT_DIR = os.path.join(config.OUTPUT_DIR, pod_name)
        if not self.overwrite:
            # bump both WORK_DIR and OUT_DIR to same version because name of
            # former may be preserved when we copy to latter, depending on
            # copy method
            self.POD_WORK_DIR, ver = filesystem.bump_version(
                self.POD_WORK_DIR, extra_dirs=[self.OUTPUT_DIR])
            self.POD_OUT_DIR, _ = filesystem.bump_version(self.POD_OUT_DIR, new_v=ver)
        filesystem.check_dir(self.POD_WORK_DIR, 'POD_WORK_DIR', create=True)
        filesystem.check_dir(self.POD_OUT_DIR, 'POD_OUT_DIR', create=True)
        # append obs and model outdirs
        dirs = ('model/PS', 'model/netCDF', 'obs/PS', 'obs/netCDF')
        for d in dirs:
            filesystem.check_dir(os.path.join(self.POD_WORK_DIR, d), create=True)

        # set root directory for TempDirManager
        if not getattr(self, 'TEMP_DIR_ROOT', ''):
            if 'MDTF_TMPDIR' in env_vars:
                self.TEMP_DIR_ROOT = env_vars['MDTF_TMPDIR']
            else:
                # default to writing temp files in working directory
                self.TEMP_DIR_ROOT = self.WORK_DIR


def verify_paths(self, config, p):
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
