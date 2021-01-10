"""Utility functions to support the site-specific classes in gfdl.py.
"""
import os
import re
import subprocess
from src import util, core, datelabel

import logging
_log = logging.getLogger(__name__)

class ModuleManager(util.Singleton):
    _current_module_versions = {
        'python2':   'python/2.7.12',
        # most recent version common to analysis and workstations; use conda anyway
        'python3':   'python/3.4.3',
        'ncl':      'ncarg/6.5.0',
        'r':        'R/3.4.4',
        'anaconda': 'anaconda2/5.1',
        'gcp':      'gcp/2.3',
        # install nco in conda environment, rather than using GFDL module
        # 'nco':      'nco/4.5.4', # 4.7.6 still broken on workstations
        'netcdf':   'netcdf/4.2'
    }

    def __init__(self):
        if 'MODULESHOME' not in os.environ:
            # could set from module --version
            raise OSError(("Unable to determine how modules are handled "
                "on this host."))
        _ = os.environ.setdefault('LOADEDMODULES', '')

        # capture the modules the user has already loaded once, when we start up,
        # so that we can restore back to this state in revert_state()
        self.user_modules = set(self._list())
        self.modules_i_loaded = set()

    def _module(self, *args):
        # based on $MODULESHOME/init/python.py
        if isinstance(args[0], list): # if we're passed explicit list, unpack it
            args = args[0]
        cmd = '{}/bin/modulecmd'.format(os.environ['MODULESHOME'])
        proc = subprocess.Popen([cmd, 'python'] + args, stdout=subprocess.PIPE)
        (output, error) = proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=proc.returncode, 
                cmd=' '.join([cmd, 'python'] + args), output=error)
        exec(output)

    def _parse_names(self, *module_names):
        return [m if ('/' in m) else self._current_module_versions[m] \
            for m in module_names]

    def load(self, *module_names):
        """Wrapper for module load.
        """
        mod_names = self._parse_names(*module_names)
        for mod_name in mod_names:
            if mod_name not in self.modules_i_loaded:
                self.modules_i_loaded.add(mod_name)
                self._module(['load', mod_name])

    def load_commands(self, *module_names):
        return ['module load {}'.format(m) \
            for m in self._parse_names(*module_names)]

    def unload(self, *module_names):
        """Wrapper for module unload.
        """
        mod_names = self._parse_names(*module_names)
        for mod_name in mod_names:
            if mod_name in self.modules_i_loaded:
                self.modules_i_loaded.discard(mod_name)
                self._module(['unload', mod_name])

    def unload_commands(self, *module_names):
        return ['module unload {}'.format(m) \
            for m in self._parse_names(*module_names)]

    def _list(self):
        """Wrapper for module list.
        """
        return os.environ['LOADEDMODULES'].split(':')
    
    def revert_state(self):
        mods_to_unload = self.modules_i_loaded.difference(self.user_modules)
        for mod in mods_to_unload:
            self._module(['unload', mod])
        # User's modules may have been unloaded if we loaded a different version
        for mod in self.user_modules:
            self._module(['load', mod])
        assert set(self._list()) == self.user_modules

# ========================================================================

def gcp_wrapper(source_path, dest_dir, timeout=None, dry_run=None):
    """Wrapper for file and recursive directory copying using the GFDL 
    site-specific General Copy Program (`https://gitlab.gfdl.noaa.gov/gcp/gcp`__.)
    Assumes GCP environment module has been loaded beforehand, and calls GCP in
    a subprocess.
    """
    modMgr = ModuleManager()
    modMgr.load('gcp')
    config = core.ConfigManager()
    if timeout is None:
        timeout = config.get('file_transfer_timeout', 0)
    if dry_run is None:
        dry_run = config.get('dry_run', False)

    source_path = os.path.normpath(source_path)
    dest_dir = os.path.normpath(dest_dir)
    # gcp requires trailing slash, ln ignores it
    if os.path.isdir(source_path):
        source = ['-r', 'gfdl:' + source_path + os.sep]
        # gcp /A/B/ /C/D/ will result in /C/D/B, so need to specify parent dir
        dest = ['gfdl:' + os.path.dirname(dest_dir) + os.sep]
    else:
        source = ['gfdl:' + source_path]
        dest = ['gfdl:' + dest_dir + os.sep]
    _log.info('\tGCP {} -> {}'.format(source[-1], dest[-1]))
    util.run_command(
        ['gcp', '--sync', '-v', '-cd'] + source + dest,
        timeout=timeout, 
        dry_run=dry_run
    )

def make_remote_dir(dest_dir, timeout=None, dry_run=None):
    """Workaround to create a directory on a remote filesystem by GCP'ing it.
    """
    try:
        os.makedirs(dest_dir)
    except OSError as exc:
        # use GCP for this because output dir might be on a read-only filesystem.
        # apparently trying to test this with os.access is less robust than 
        # just catching the error
        _log.debug("os.makedirs at %s failed (%r); trying GCP.", dest_dir, exc)
        tmpdirs = core.TempDirManager()
        work_dir = tmpdirs.make_tempdir()
        work_dir = os.path.join(work_dir, os.path.basename(dest_dir))
        os.makedirs(work_dir)
        gcp_wrapper(work_dir, dest_dir, timeout=timeout, dry_run=dry_run)

def fetch_obs_data(source_dir, dest_dir, timeout=None, dry_run=None):
    """Function to fetch site-wide copy of the MDTF package observational data
    to local disk (taken to be source_dir and dest_dir, respectively.)
    """
    if source_dir == dest_dir:
        return
    if not os.path.exists(source_dir) or not os.listdir(source_dir):
        _log.error("Empty obs data directory at '%s'.", source_dir)
    if not os.path.exists(dest_dir) or not os.listdir(dest_dir):
        _log.debug("Empty obs data directory at '%s'.", dest_dir)
    if running_on_PPAN():
        _log.info("\tGCPing data from {}.".format(source_dir))
        # giving -cd to GCP, so will create dirs
        gcp_wrapper(
            source_dir, dest_dir, timeout=timeout, dry_run=dry_run
        )
    else:
        _log.info("\tSymlinking obs data dir to {}.".format(source_dir))
        dest_parent = os.path.dirname(dest_dir)
        if os.path.exists(dest_dir):
            assert os.path.isdir(dest_dir)
            try:
                os.remove(dest_dir) # remove symlink only, not source dir
            except OSError:
                _log.error('Expected symlink at %s', dest_dir)
                os.rmdir(dest_dir)
        elif not os.path.exists(dest_parent):
            os.makedirs(dest_parent)
        if dry_run:
            print('DRY_RUN: symlink {} -> {}'.format(source_dir, dest_dir))
        else:
            os.symlink(source_dir, dest_dir)

def running_on_PPAN():
    """Return true if current host is in the PPAN cluster.
    """
    host = os.uname()[1].split('.')[0]
    return (re.match(r"(pp|an)\d{3}", host) is not None)

def is_on_tape_filesystem(path):
    """Return true if path is on a DMF tape-backed filesystem. Does not attempt
    to determine status of path (active disk vs. tape).
    """
    # handle eg. /arch0 et al as well as /archive.
    return any(os.path.realpath(path).startswith(s) \
        for s in ['/arch', '/ptmp', '/work'])

def frepp_freq(date_freq):
    # logic as written would give errors for 1yr chunks (?)
    if date_freq is None:
        return date_freq
    assert isinstance(date_freq, datelabel.DateFrequency)
    if date_freq.unit == 'hr' or date_freq.quantity != 1:
        return date_freq.format()
    else:
        # weekly not used in frepp
        _frepp_dict = {
            'yr': 'annual',
            'season': 'seasonal',
            'mo': 'monthly',
            'day': 'daily',
            'hr': 'hourly'
        }
        return _frepp_dict[date_freq.unit]

frepp_translate = {
    'in_data_dir': 'data_root_dir', # /pp/ directory
    'descriptor': 'CASENAME',
    'out_dir': 'OUTPUT_DIR',
    'WORKDIR': 'WORKING_DIR',
    'yr1': 'FIRSTYR',
    'yr2': 'LASTYR'
}

def parse_frepp_stub(frepp_stub):
    """Converts the frepp arguments to a Python dictionary.

    See `<https://wiki.gfdl.noaa.gov/index.php/FRE_User_Documentation#Automated_creation_of_diagnostic_figures>`__.

    Returns: :py:obj:`dict` of frepp parameters.
    """
    # parse arguments and relabel keys
    d = {}
    regex = re.compile(r"""
        \s*set[ ]     # initial whitespace, then 'set' followed by 1 space
        (?P<key>\w+)  # key is simple token, no problem
        \s+=?\s*      # separator is any whitespace, with 0 or 1 "=" signs
        (?P<value>    # want to capture all characters to end of line, so:
            [^=#\s]   # first character = any non-separator, or '#' for comments
            .*        # capture everything between first and last chars
            [^\s]     # last char = non-whitespace.
            |[^=#\s]\b) # separate case for when value is a single character.
        \s*$          # remainder of line must be whitespace.
        """, re.VERBOSE)
    for line in frepp_stub.splitlines():
        _log.debug("line = '{}'".format(line))
        match = re.match(regex, line)
        if match:
            if match.group('key') in frepp_translate:
                key = frepp_translate[match.group('key')]
            else:
                key = match.group('key')
            d[key] = match.group('value')

    # cast from string
    for int_key in ['FIRSTYR', 'LASTYR', 'verbose']:
        if int_key in d:
            d[int_key] = int(d[int_key])
    for bool_key in ['make_variab_tar', 'test_mode']:
        if bool_key in d:
            d[bool_key] = bool(d[bool_key])

    d['frepp'] = (d != {})
    return d
