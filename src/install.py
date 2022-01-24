#!/usr/bin/env python
"""Currently unused; intended as a standalone installer script for the package's
conda environments and supporting data.
"""

import sys
# do version check before importing other stuff
if sys.version_info[0] != 3 or sys.version_info[1] < 7:
    sys.exit("ERROR: MDTF currently only supports python >= 3.7.*. Please check "
    "which version is on your $PATH (e.g. with `which python`.)\n"
    f"Attempted to run with following python version:\n{sys.version}")
# passed; continue with imports
import os
import io
import glob
import collections
import platform
import ftplib
import socket
import shutil
from src import cli
from src import util
from src.verify_links import LinkVerifier


# ------------------------------------------------------------------------------
# Functions that call external programs to do all the work
# Separate out instead of making them static methods

def shell_command_wrapper(cmd, **kwargs):
    print('SHELL RUN:')
    print('  ', cmd)
    try:
        stdout = util.run_shell_command(cmd, **kwargs)
    except Exception:
        raise
    if stdout:
        print('SHELL STDOUT:')
        for line in stdout:
            print(' ', line)
    else:
        print('SHELL STDOUT: (no output returned)')
    return stdout

def fatal_exception_handler(exc, msg=None):
    # if subprocess failed, will have already logged its own info
    print('ERROR: caught exception {0}({1!r})'.format(type(exc).__name__, exc.args))
    if msg:
        print(msg)
    util.exit_handler(code=1)

def find_conda(code_root, conda_config):
    """Attempt to determine conda location on this system.
    """
    d = dict()
    try:
        conda_info = shell_command_wrapper(
            conda_config['init_script'] + ' -v'
        )
    except Exception:
        print("ERROR: attempt to find conda installation failed.")
        return dict()
    for line in conda_info:
        if '=' in line:
            key, val = line.split('=')
            if key == '_CONDA_EXE':
                d['conda_exe'] = val
            elif key == '_CONDA_ROOT':
                d['conda_root'] = val
    if d['conda_exe'] and os.path.exists(d['conda_exe']):
        return d
    else:
        print("ERROR: attempt to find conda installation failed.")
        return dict()

def conda_env_create(envs, code_root, conda_config):
    """Create a set of conda environments from yaml files.
    """
    flags = ' --all --conda_root "{conda_root}"'.format(**conda_config)
    if conda_config.get('conda_env_root', False):
        print("Installing envs into {conda_env_root}".format(**conda_config))
        print(("To use envs interactively, run `conda config --append envs_dirs "
            '"{conda_env_root}"`'.format(**conda_config)))
        flags = flags + ' --env_dir "{conda_env_root}"'.format(**conda_config)
    else:
        print("Installing envs into system conda")
    try:
        _ = shell_command_wrapper(conda_config['setup_script'] + flags)
    except Exception as exc:
        fatal_exception_handler(exc, "ERROR: conda installation failed.")

def ftp_download(ftp_config, ftp_data, install_config):
    """Download files via anonymous FTP.
    """
    def _format_bytes(num):
        # https://stackoverflow.com/a/52379087
        if not isinstance(num, (int, float)):
            return ""
        step_unit = 1024.0
        for x in ['bytes', 'Kb', 'Mb', 'Gb', 'Tb']:
            if num < step_unit:
                return "%3.1f %s" % (num, x)
            num /= step_unit

    try:
        print("Initiating anonymous FTP connection to {}.".format(ftp_config['host']))
        ftp = ftplib.FTP(**ftp_config)
        ftp.set_debuglevel(1)
        ftp.set_pasv(True) # should be passive by default, though
        ftp.sendcmd("TYPE i")    # switch to binary mode
        # https://stackoverflow.com/a/5269068 , replacing the multiple-thread
        # solution from https://stackoverflow.com/a/19693709 tried previously
        ftp.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        ftp.voidcmd('NOOP') # test connection
    except Exception as exc:
        # do whatever we can to cleanup gracefully before exiting
        try: ftp.quit()
        except Exception:
            pass
        fatal_exception_handler(exc,
            "ERROR: could not establish FTP connection to {}.".format(ftp_config['host'])
        )
    for f in iter(ftp_data.values()):
        try:
            local_path = os.path.join(install_config[f.target_dir], f.file)
            ftp.cwd(f.source_dir)
            f_size = ftp.size(f.file)
            print("Starting download of {} ({}), please be patient.".format(
                f.file, _format_bytes(f_size)
            ))
            with open(local_path, 'wb') as f_out:
                ftp.retrbinary('RETR ' + f.file, f_out.write)
            print("Successfully downloaded {}".format(f.file))
            ftp.cwd('/')
        except Exception as exc:
            # do whatever we can to cleanup gracefully before exiting
            try: f_out.close()
            except Exception:
                pass
            try: ftp.quit()
            except Exception:
                pass
            fatal_exception_handler(exc,
                "ERROR: could not download {} from {}.".format(f.file, ftp_config['host'])
            )
    try:
        # ftp may have closed if we hit an error
        ftp.voidcmd('NOOP')
        ftp.quit()
    except Exception:
        pass
    print("Closed connection to {}.".format(ftp_config['host']))

def untar_data(ftp_data, install_config):
    """Extract tar files of obs/model data and move contents to correct location.
    """
    if platform.system() == 'Darwin': # workaround for macos
        tar_cmd = 'open -W -g -j -a "{}" '
        test_path = "/System/Library/CoreServices/Applications/Archive Utility.app"
        if os.path.exists(test_path):
            tar_cmd = tar_cmd.format(test_path)
        else:
            # Location on Yosemite and earlier
            test_path = "/System/Library/CoreServices/Archive Utility.app"
            if os.path.exists(test_path):
                tar_cmd = tar_cmd.format(test_path)
            else:
                print("ERROR: could not find Archive Utility.app.")
                util.exit_handler(code=1)
    else:
        tar_cmd = 'tar -xf '

    for f in iter(ftp_data.values()):
        print("Extracting {}".format(f.file))
        cwd = install_config[f.target_dir]
        f_subdir_0 = f.contents_subdir.split(os.sep)[0]
        try:
            _ = shell_command_wrapper(tar_cmd + f.file, cwd=cwd)
        except Exception as exc:
            fatal_exception_handler(exc,
                "ERROR: could not extract {}.".format(f.file)
            )
        try:
            for d in os.listdir(os.path.join(cwd, f.contents_subdir)):
                shutil.move(
                    os.path.join(cwd, f.contents_subdir, d),
                    os.path.join(cwd, d)
                )
            shutil.rmtree(os.path.join(cwd, f_subdir_0))
        except Exception as exc:
            fatal_exception_handler(exc,
                "ERROR: could not move contents of {}.".format(f.file)
            )
        try:
            os.remove(os.path.join(cwd, f.file))
        except Exception as exc:
            fatal_exception_handler(exc,
                "ERROR: could not delete {}.".format(f.file)
            )

def set_cli_defaults(code_root, cli_config, install_config):
    """Write install-time configuration options to the cli.jsonc file used to
    set run-time default values.
    """
    def _set_cli_default(template, name, default):
        template[name] = default

    in_path = os.path.join(code_root, cli_config['config_in'])
    out_path = os.path.join(code_root, cli_config['config_out'])
    print("Writing default settings to {}".format(out_path))
    try:
        cli_template = util.read_json(in_path)
    except Exception as exc:
        fatal_exception_handler(exc, "ERROR: Couldn't read {}.".format(in_path))
    for key in cli_config['default_keys']:
        try:
            _set_cli_default(cli_template, key, install_config[key])
        except Exception as exc:
            fatal_exception_handler(exc, "ERROR: {} not set".format(key))
    if os.path.exists(out_path):
        print("{} exists; overwriting".format(out_path))
        os.remove(out_path)
    try:
        util.write_json(cli_template, out_path, sort_keys=False)
    except Exception as exc:
        fatal_exception_handler(exc, "ERROR: Couldn't write {}.".format(out_path))

def framework_test(code_root, output_dir, cli_config):
    print("Starting framework test run")
    abs_out_dir = util.resolve_path(
        output_dir, root_path=code_root, env=os.environ
    )
    try:
        log_str = shell_command_wrapper(
            './mdtf -f {input_file}'.format(
                input_file=os.path.join(code_root, cli_config['config_out'])
            ),
            cwd=code_root
        )
        log_str = util.to_iter(log_str)
        # write to most recent directory in output_dir
        runs = [d for d in glob.glob(os.path.join(abs_out_dir,'*')) if os.path.isdir(d)]
        if not runs:
            raise IOError("Can't find framework output in {}".format(abs_out_dir))
        run_output = max(runs, key=os.path.getmtime)
        with io.open(
            os.path.join(run_output, 'mdtf_test.log'),
            'w', encoding='utf-8'
        ) as f:
            f.write('\n'.join(log_str))
    except Exception as exc:
        fatal_exception_handler(exc, "ERROR: framework test run failed.")
    print("Finished framework test run at {}".format(run_output))
    return run_output

def framework_verify(code_root, run_output):
    print("Checking linked output files")
    try:
        html_root = os.path.join(run_output, 'index.html')
        if not os.path.exists(html_root):
            raise IOError("Can't find framework html output in {}".format(html_root))
        link_verifier = LinkVerifier(html_root, verbose=False)
        missing_dict = link_verifier.verify_all_links()
    except Exception as exc:
        fatal_exception_handler(exc, "ERROR in link verification.")
    if missing_dict:
        print("ERROR: the following files are missing:")
        print(util.pretty_print_json(missing_dict))
        util.exit_handler(code=1)
    print("SUCCESS: no missing links found.")
    print("Finished: framework test run successful!")


# ------------------------------------------------------------------------------
# classes just handle the configuration logic


class InstallCLIHandler(cli.MDTFArgParser):
    def make_parser(self, d):
        _ = d.setdefault('usage', "%(prog)s [options] [env_setup]")
        p = super(InstallCLIHandler, self).make_parser(d)
        p._positionals.title = None
        p._optionals.title = 'INSTALLER OPTIONS'
        return p


class MDTFInstaller(object):
    _env_paths = ["conda_env_root", "venv_root", "r_lib_root"]
    _data_paths = ["MODEL_DATA_ROOT", "OBS_DATA_ROOT"]
    _shared_conda_keys = ["conda_exe", "conda_root", "conda_env_root"] #HACK

    def __init__(self, code_root, settings_file):
        self.code_root = code_root
        _settings = util.read_json(os.path.join(code_root, settings_file))
        self.settings = util.NameSpace.fromDict(_settings['settings'])
        self.cli_settings = _settings['cli']
        self.config = util.NameSpace.fromDict({
            k:self.settings.conda[k] for k in self._shared_conda_keys
        })
        self.settings.conda['init_script'] = os.path.join(
            code_root, self.settings.conda['init_script']
        )

    def configure(self, args=None):
        self.config.update(find_conda(self.code_root, self.settings.conda))
        self.get_config(args)
        self.parse_config()
        self.print_config()

    def get_config(self, args=None):
        # assemble from CLI
        cli_dict = util.read_json(
            os.path.join(self.code_root, self.settings.cli_defaults['template'])
        )
        for key, val in iter(self.cli_settings.items()):
            cli_dict[key] = val
        # filter only the defaults we're setting
        for arg_gp in cli_dict['argument_groups']:
            arg_gp['arguments'] = [
                arg for arg in arg_gp['arguments'] \
                if arg['name'] in self.settings.cli_defaults['default_keys']
            ]
        cli_obj = InstallCLIHandler(self.code_root, cli_dict, partial_defaults=self.config)
        cli_obj.parse_cli(args)
        self.config = util.NameSpace.fromDict(cli_obj.config)

    def parse_config(self):
        d = self.config # abbreviation
        # determine downloads
        d.downloads_list = ['obs']
        if not d.no_cesm:
            d.downloads_list.append('model_cesm')
        if not d.no_am4:
            d.downloads_list.append('model_am4')

        # determine runtime setup
        d.pods = 'all'
        d.conda_envmgr = True
        if d.env_setup == 'conda-basic':
            d.conda_envs = [self.settings.conda['framework_env'], 'NCL_base']
            d.environment_manager = "Conda"
            d.pods = ["Wheeler_Kiladis", "EOF_500hPa", "MJO_suite", "MJO_teleconnection"]
            if 'model_am4' in d.downloads_list:
                d.downloads_list.remove('model_am4')
        elif d.env_setup == 'conda-full':
            d.conda_envs = ['all']
            d.environment_manager = "Conda"
        elif d.env_setup == 'no-conda':
            d.conda_envmgr = False
            d.conda_envs = []
            d.environment_manager = "VirtualEnv"
        if d.conda_install_dev and not d.conda_envmgr:
            d.conda_envs.append('dev')

        # make settings consistent with config
        ordered_data = collections.OrderedDict()
        for k in d.downloads_list:
            ordered_data[k] = self.settings.data[k]
        self.settings.data = ordered_data
        for k in self._shared_conda_keys:
            self.settings.conda[k] = d[k]
        # convert relative paths to absolute
        for key in (self._env_paths + self._data_paths):
            if d[key]:
                d[key] = util.resolve_path(
                    d[key], root_path=self.code_root, env=os.environ
                )

    def print_config(self):
        _tmp = {'settings': dict(), 'defaults to assign': dict()}
        for key, val in iter(self.config.items()):
            if key in self.settings.cli_defaults['default_keys']:
                _tmp['defaults to assign'][key] = val
            else:
                _tmp['settings'][key] = val
        print(util.pretty_print_json(_tmp, sort_keys=True))

    def makedirs(self, path_keys, delete_existing):
        path_keys = util.to_iter(path_keys)
        for key in path_keys:
            path = self.config[key]
            if path:
                if not os.path.isdir(path):
                    os.makedirs(path) # recursive mkdir if needed
                elif delete_existing:
                    shutil.rmtree(path) # overwrite everything

    def install(self):
        d = self.config # abbreviation
        if not d.no_downloads:
            self.makedirs(self._data_paths, delete_existing=True)
            ftp_download(self.settings.ftp, self.settings.data, d)
            untar_data(self.settings.data, d)
        self.makedirs(self._env_paths, delete_existing=False) # both conda and non-conda envs
        if not d.no_conda_install:
            conda_env_create(d.conda_envs, self.code_root, self.settings.conda)

        set_cli_defaults(self.code_root, self.settings.cli_defaults, d)
        if not d.no_test_run:
            run_output = framework_test(self.code_root, d.OUTPUT_DIR, self.settings.cli_defaults)
            framework_verify(self.code_root, run_output)

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    # get dir of currently executing script:
    cwd = os.path.dirname(os.path.realpath(__file__))
    code_root, src_dir = os.path.split(cwd)
    install = MDTFInstaller(code_root, os.path.join(src_dir, 'install_settings.jsonc'))
    install.configure()
    install.install()
