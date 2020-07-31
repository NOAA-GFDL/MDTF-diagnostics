#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
# do version check before importing other stuff
if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    print(("ERROR: MDTF currently only supports python >= 2.7. Please check "
    "which version is on your $PATH (e.g. with `which python`.)"))
    print("Attempted to run with following python version:\n{}".format(sys.version))
    exit()
# passed; continue with imports
import os
import shutil
import tempfile
from src import util
from src import util_mdtf
from src import mdtf
from src import data_manager
from src import environment_manager
from src import shared_diagnostic
from src import netcdf_helper
from src import gfdl

class GFDLMDTFFramework(mdtf.MDTFFramework):
    # add gfdl to search path for DataMgr, EnvMgr
    _dispatch_search = [
        data_manager, environment_manager, shared_diagnostic, netcdf_helper, gfdl
    ]

    def parse_mdtf_args(self, cli_obj, config):
        super(GFDLMDTFFramework, self).parse_mdtf_args(cli_obj, config)
        # set up cooperative mode -- hack to pass config settings
        self.frepp_mode = config.config.get('frepp', False)
        if self.frepp_mode:
            config.config['diagnostic'] = 'Gfdl'

    def parse_env_vars(self, cli_obj, config):
        super(GFDLMDTFFramework, self).parse_env_vars(cli_obj, config)
        # set temp directory according to where we're running
        if gfdl.running_on_PPAN():
            gfdl_tmp_dir = cli_obj.config.get('GFDL_PPAN_TEMP', '$TMPDIR')
        else:
            gfdl_tmp_dir = cli_obj.config.get('GFDL_WS_TEMP', '$TMPDIR')
        gfdl_tmp_dir = util.resolve_path(
            gfdl_tmp_dir, root_path=self.code_root, env=config.global_envvars
        )
        if not os.path.isdir(gfdl_tmp_dir):
            gfdl.make_remote_dir(gfdl_tmp_dir)
        tempfile.tempdir = gfdl_tmp_dir
        os.environ['MDTF_GFDL_TMPDIR'] = gfdl_tmp_dir
        config.global_envvars['MDTF_GFDL_TMPDIR'] = gfdl_tmp_dir

    def _post_parse_hook(self, cli_obj, config):
        ### call parent class method
        super(GFDLMDTFFramework, self)._post_parse_hook(cli_obj, config)

        self.dry_run = config.config.get('dry_run', False)
        self.timeout = config.config.get('file_transfer_timeout', 0)
        # copy obs data from site install
        fetch_obs_data(
            config.paths.OBS_DATA_REMOTE, config.paths.OBS_DATA_ROOT,
            timeout=self.timeout, dry_run=self.dry_run
        )

    def verify_paths(self, config):
        # clean out WORKING_DIR if we're not keeping temp files
        if os.path.exists(config.paths.WORKING_DIR) and not \
            (config.config.get('keep_temp', False) \
            or config.paths.WORKING_DIR == config.paths.OUTPUT_DIR):
            shutil.rmtree(config.paths.WORKING_DIR)
        util_mdtf.check_required_dirs(
            already_exist = [
                config.paths.CODE_ROOT, config.paths.OBS_DATA_REMOTE
            ], 
            create_if_nec = [
                config.paths.MODEL_DATA_ROOT, config.paths.WORKING_DIR,
                config.paths.OBS_DATA_ROOT
        ])
        # Use GCP to create OUTPUT_DIR on a volume that may be read-only
        if not os.path.exists(config.paths.OUTPUT_DIR):
            gfdl.make_remote_dir(
                config.paths.OUTPUT_DIR, self.timeout, self.dry_run
            )

    def set_case_pod_list(self, case, cli_obj, config):
        requested_pods = super(GFDLMDTFFramework, self).set_case_pod_list(
            case, cli_obj, config
        )
        if not config.config.get('frepp', False):
            # try to run everything if not in frepp cooperative mode
            return requested_pods
        else:
            # frepp mode:only attempt PODs other instances haven't already done
            case_outdir = config.paths.modelPaths(case, overwrite=True)
            case_outdir = case_outdir.MODEL_OUT_DIR
            for p in requested_pods:
                if os.path.isdir(os.path.join(case_outdir, p)):
                    print(("\tDEBUG: preexisting {} in {}; "
                        "skipping b/c frepp mode").format(p, case_outdir))
            return [p for p in requested_pods if not \
                os.path.isdir(os.path.join(case_outdir, p))
            ]


def fetch_obs_data(source_dir, dest_dir, timeout=0, dry_run=False):
    if source_dir == dest_dir:
        return
    if not os.path.exists(source_dir) or not os.listdir(source_dir):
        print("Observational data directory at {} is empty.".format(source_dir))
    if not os.path.exists(dest_dir) or not os.listdir(dest_dir):
        print("Observational data directory at {} is empty.".format(dest_dir))
    if gfdl.running_on_PPAN():
        print("\tGCPing data from {}.".format(source_dir))
        # giving -cd to GCP, so will create dirs
        gfdl.gcp_wrapper(
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

if __name__ == '__main__':
    # get dir of currently executing script: 
    cwd = os.path.dirname(os.path.realpath(__file__)) 
    code_root, src_dir = os.path.split(cwd)
    defaults_rel_path = os.path.join(src_dir, 'cli_gfdl.jsonc')
    if not os.path.exists(defaults_rel_path):
        # print('Warning: site-specific cli_gfdl.jsonc not found, using template.')
        defaults_rel_path = os.path.join(src_dir, 'cli_template.jsonc')
    mdtf = GFDLMDTFFramework(code_root, defaults_rel_path)
    print("\n======= Starting {}".format(__file__))
    mdtf.main_loop()
    print("Exiting normally from {}".format(__file__))
