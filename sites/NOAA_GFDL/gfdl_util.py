import os
import re
import shutil
import subprocess
import tempfile
from src import util, configs, datelabel

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


class GFDLMDTFConfigurer(configs.MDTFConfigurer):
    def parse_mdtf_args(self, cli_obj):
        super(GFDLMDTFConfigurer, self).parse_mdtf_args(cli_obj)
        # set up cooperative mode -- hack to pass config settings
        self.frepp_mode = cli_obj.config.get('frepp', False)
        if self.frepp_mode:
            cli_obj.config['diagnostic'] = 'Gfdl'

    def parse_env_vars(self, cli_obj):
        super(GFDLMDTFConfigurer, self).parse_env_vars(cli_obj)
        # set temp directory according to where we're running
        if running_on_PPAN():
            gfdl_tmp_dir = cli_obj.config.get('GFDL_PPAN_TEMP', '$TMPDIR')
        else:
            gfdl_tmp_dir = cli_obj.config.get('GFDL_WS_TEMP', '$TMPDIR')
        gfdl_tmp_dir = util.resolve_path(
            gfdl_tmp_dir, root_path=self.code_root, env=self.global_env_vars
        )
        if not os.path.isdir(gfdl_tmp_dir):
            make_remote_dir(gfdl_tmp_dir)
        tempfile.tempdir = gfdl_tmp_dir
        os.environ['MDTF_GFDL_TMPDIR'] = gfdl_tmp_dir
        self.global_env_vars['MDTF_GFDL_TMPDIR'] = gfdl_tmp_dir

    def _post_parse_hook(self, cli_obj, config, paths):
        ### call parent class method
        super(GFDLMDTFConfigurer, self)._post_parse_hook(cli_obj, config, paths)

        self.reset_case_pod_list(cli_obj, config, paths)
        self.dry_run = config.get('dry_run', False)
        self.timeout = config.get('file_transfer_timeout', 0)
        # copy obs data from site install
        fetch_obs_data(
            paths.OBS_DATA_REMOTE, paths.OBS_DATA_ROOT,
            timeout=self.timeout, dry_run=self.dry_run
        )

    def reset_case_pod_list(self, cli_obj, config, paths):
        if self.frepp_mode:
            for case in config.case_list:
                # frepp mode:only attempt PODs other instances haven't already done
                case_outdir = paths.modelPaths(case, overwrite=True)
                case_outdir = case_outdir.MODEL_OUT_DIR
                pod_list = case['pod_list']
                for p in pod_list:
                    if os.path.isdir(os.path.join(case_outdir, p)):
                        print(("\tDEBUG: preexisting {} in {}; "
                            "skipping b/c frepp mode").format(p, case_outdir))
                case['pod_list'] = [p for p in pod_list if not \
                    os.path.isdir(os.path.join(case_outdir, p))
                ]

    def verify_paths(self, config, p):
        keep_temp = config.get('keep_temp', False)
        # clean out WORKING_DIR if we're not keeping temp files:
        if os.path.exists(p.WORKING_DIR) and not \
            (keep_temp or p.WORKING_DIR == p.OUTPUT_DIR):
            shutil.rmtree(p.WORKING_DIR)
        configs.check_dirs(p.CODE_ROOT, p.OBS_DATA_REMOTE, create=False)
        configs.check_dirs(p.MODEL_DATA_ROOT, p.OBS_DATA_ROOT, p.WORKING_DIR, 
            create=True)
        # Use GCP to create OUTPUT_DIR on a volume that may be read-only
        if not os.path.exists(p.OUTPUT_DIR):
            make_remote_dir(p.OUTPUT_DIR, self.timeout, self.dry_run)


# ====================================================================

def gcp_wrapper(source_path, dest_dir, timeout=0, dry_run=False):
    modMgr = ModuleManager()
    modMgr.load('gcp')
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
    print('\tDEBUG: GCP {} -> {}'.format(source[-1], dest[-1]))
    util.run_command(
        ['gcp', '--sync', '-v', '-cd'] + source + dest,
        timeout=timeout, 
        dry_run=dry_run
    )

def make_remote_dir(dest_dir, timeout=None, dry_run=None):
    try:
        os.makedirs(dest_dir)
    except OSError:
        # use GCP for this because output dir might be on a read-only filesystem.
        # apparently trying to test this with os.access is less robust than 
        # just catching the error
        config = configs.ConfigManager()
        tmpdirs = configs.TempDirManager()
        work_dir = tmpdirs.make_tempdir()
        if timeout is None:
            timeout = config.get('file_transfer_timeout', 0)
        if dry_run is None:
            dry_run = config.get('dry_run', False)
        work_dir = os.path.join(work_dir, os.path.basename(dest_dir))
        os.makedirs(work_dir)
        gcp_wrapper(work_dir, dest_dir, timeout=timeout, dry_run=dry_run)

def fetch_obs_data(source_dir, dest_dir, timeout=0, dry_run=False):
    if source_dir == dest_dir:
        return
    if not os.path.exists(source_dir) or not os.listdir(source_dir):
        print("Observational data directory at {} is empty.".format(source_dir))
    if not os.path.exists(dest_dir) or not os.listdir(dest_dir):
        print("Observational data directory at {} is empty.".format(dest_dir))
    if running_on_PPAN():
        print("\tGCPing data from {}.".format(source_dir))
        # giving -cd to GCP, so will create dirs
        gcp_wrapper(
            source_dir, dest_dir, timeout=timeout, dry_run=dry_run
        )
    else:
        print("\tSymlinking obs data dir to {}.".format(source_dir))
        dest_parent = os.path.dirname(dest_dir)
        if os.path.exists(dest_dir):
            assert os.path.isdir(dest_dir)
            try:
                os.remove(dest_dir) # remove symlink only, not source dir
            except OSError:
                print('Warning: expected symlink at {}'.format(dest_dir))
                os.rmdir(dest_dir)
        elif not os.path.exists(dest_parent):
            os.makedirs(dest_parent)
        if dry_run:
            print('DRY_RUN: symlink {} -> {}'.format(source_dir, dest_dir))
        else:
            os.symlink(source_dir, dest_dir)

# ========================================================================

def running_on_PPAN():
    """Return true if current host is in the PPAN cluster."""
    host = os.uname()[1].split('.')[0]
    return (re.match(r"(pp|an)\d{3}", host) is not None)

def is_on_tape_filesystem(path):
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
        print("line = '{}'".format(line))
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
