"""Utility functions for defining directory paths
"""
import os
import io
import glob
from . import check_dir
from . import exit_handler
from . import Singleton
from . import NameSpace
import shutil
import string
from . import basic
from . import exceptions
import yaml

import logging
_log = logging.getLogger(__name__)


class PathManager(Singleton, NameSpace):
    """:class:`~util.Singleton` holding the root directories for all paths used
    by the code.
    """
    def __init__(self, cli_obj=None, env_vars=None, unittest=False):
        self._unittest = unittest
        if self._unittest:
            for path in ['CODE_ROOT', 'OBS_DATA_ROOT',
                         'WORK_DIR', 'OUTPUT_DIR']:
                setattr(self, path, 'TEST_'+path)
            self.TEMP_DIR_ROOT = self.WORKING_DIR
        else:
            # normal code path
            self.CODE_ROOT = cli_obj.code_root
            assert os.path.isdir(self.CODE_ROOT)

            d = cli_obj.config
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            # set following explictly: redundant, but keeps linter from complaining
            self.OBS_DATA_ROOT = self._init_path('OBS_DATA_ROOT', d, env=env)
            self.WORK_DIR = self._init_path('WOR_DIR', d, env=env)
            self.OUTPUT_DIR = self._init_path('OUTPUT_DIR', d, env=env)

            if not self.OUTPUT_DIR:
                self.OUTPUT_DIR = self.WORK_DIR

            # set as attribute any CLI setting that has "action": "PathAction"
            # in its definition in the .jsonc file
            cli_paths = [act.dest for act in cli_obj.iter_actions()
                         if isinstance(act, cli.PathAction)]
            if not cli_paths:
                _log.warning("Didn't get list of paths from CLI.")
            for key in cli_paths:
                self[key] = self._init_path(key, d, env=env)
                if key in d:
                    d[key] = self[key]

            # set root directory for TempDirManager
            if not getattr(self, 'TEMP_DIR_ROOT', ''):
                if 'MDTF_TMPDIR' in env:
                    self.TEMP_DIR_ROOT = env['MDTF_TMPDIR']
                else:
                    # default to writing temp files in working directory
                    self.TEMP_DIR_ROOT = self.WORKING_DIR

    def _init_path(self, key, d, env=None):
        if self._unittest: # use in unit testing only
            return 'TEST_'+key
        else:
            # need to check existence in case we're being called directly
            if not d.get(key, False):
                _log.fatal(f"Error: {key} not initialized.")
                util.exit_handler(code=1)
            return util.resolve_path(
                util.from_iter(d[key]), root_path=self.CODE_ROOT, env=env,
                log=_log
            )

    def multirun_model_paths(self, pod, case):
        # define directory paths for multirun mode
        # Each case directory is a subdirectory in wk_dir/pod_name
        d = util.NameSpace()
        if isinstance(case, dict):
            name = case['CASENAME']
            yr1 = case['FIRSTYR']
            yr2 = case['LASTYR']
        else:
            name = case.name
            yr1 = case.attrs.date_range.start.format(precision=1)
            yr2 = case.attrs.date_range.end.format(precision=1)
        case_wk_dir = 'MDTF_{}_{}_{}'.format(name, yr1, yr2)
        d.MODEL_DATA_DIR = os.path.join(self.MODEL_DATA_ROOT, name)
        # Cases are located in a common POD directory
        d.MODEL_WK_DIR = os.path.join(pod.POD_WK_DIR, case_wk_dir)
        d.MODEL_OUT_DIR = os.path.join(pod.POD_OUT_DIR, case_wk_dir)
        return d

    def pod_paths(self, pod, case):
        d = util.NameSpace()
        d.POD_CODE_DIR = os.path.join(self.CODE_ROOT, 'diagnostics', pod.name)
        d.POD_OBS_DATA = os.path.join(self.OBS_DATA_ROOT, pod.name)
        d.POD_WK_DIR = os.path.join(case.MODEL_WK_DIR, pod.name)
        d.POD_OUT_DIR = os.path.join(case.MODEL_OUT_DIR, pod.name)
        return d
def verify_paths(self, config, p):
    # needs to be here, instead of PathManager, because we subclass it in
    # NOAA_GFDL
    keep_temp = config.get('keep_temp', False)
    # clean out WORKING_DIR if we're not keeping temp files:
    if os.path.exists(p.WORKING_DIR) and not \
            (keep_temp or p.WORKING_DIR == p.OUTPUT_DIR):
        shutil.rmtree(p.WORKING_DIR)

    try:
        for dir_name, create_ in (
                ('CODE_ROOT', False), ('OBS_DATA_ROOT', False),
                ('MODEL_DATA_ROOT', True), ('WORKING_DIR', True)
        ):
            check_dir(p, dir_name, create=create_)
    except Exception as exc:
        _log.fatal((f"Input settings for {dir_name} mis-specified (caught "
                    f"{repr(exc)}.)"))
        exit_handler(code=1)