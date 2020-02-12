#!/usr/bin/env python

from __future__ import print_function
import os
import tempfile
import data_manager
import environment_manager
import shared_diagnostic
import gfdl
import util
import util_mdtf
import mdtf

class GFDLMDTFFramework(mdtf.MDTFFramework):
    # add gfdl to search path for DataMgr, EnvMgr
    _dispatch_search = [data_manager, environment_manager, shared_diagnostic, gfdl]

    def parse_mdtf_args(self, cli_obj):
        dry_run = cli_obj.config['settings'].get('dry_run', False)
        timeout = cli_obj.config['settings'].get('timeout', False)
        # copy obs data from site install
        self.fetch_obs_data(timeout=timeout, dry_run=dry_run)
        # Use GCP to create OUTPUT_DIR otherwise parse_mdtf_args will throw error
        # when trying to create it on a read-only volume
        if not os.path.exists(cli_obj.config['paths']['OUTPUT_DIR']):
            gfdl.make_remote_dir(cli_obj.config['paths']['OUTPUT_DIR'], timeout, dry_run)

        ### call parent class method
        super(GFDLMDTFFramework, self).parse_mdtf_args(cli_obj)

        if self.config['settings'].get('frepp', False):
            # set up cooperative mode -- hack to pass config settings
            gfdl.GfdlDiagnostic._config = self.config
            self.config['settings']['diagnostic'] = 'Gfdl'

    def parse_env_vars(self, cli_obj):
        # set temp directory according to where we're running
        if gfdl.running_on_PPAN():
            gfdl_tmp_dir = cli_obj.config.get('GFDL_PPAN_TEMP', '$TMPDIR')
        else:
            gfdl_tmp_dir = cli_obj.config.get('GFDL_WS_TEMP', '$TMPDIR')
        # only let this be overridden if we're in a unit test
        rel_paths_root = cli_obj.config.get('CODE_ROOT', None)
        if not rel_paths_root or rel_paths_root == '.':
            rel_paths_root = self.code_root
        gfdl_tmp_dir = util.resolve_path(gfdl_tmp_dir, rel_paths_root)
        if not os.path.isdir(gfdl_tmp_dir):
            gfdl.make_remote_dir(gfdl_tmp_dir)
        tempfile.tempdir = gfdl_tmp_dir
        os.environ['MDTF_GFDL_TMPDIR'] = gfdl_tmp_dir

        ### call parent class method
        super(GFDLMDTFFramework, self).parse_env_vars(cli_obj)

    def set_case_pod_list(self, case_dict):
        ### call parent class method
        requested_pods = super(GFDLMDTFFramework, self).set_case_pod_list(case_dict)

        if not self.config['settings'].get('frepp', False):
            # try to run everything if not in frepp cooperative mode
            return requested_pods
        else:
            # only attempt PODs other instances haven't already done
            paths = util_mdtf.PathManager()
            case_outdir = paths.modelPaths(case_dict)['MODEL_OUT_DIR']
            for p in requested_pods:
                if os.path.isdir(os.path.join(case_outdir, p)):
                    print(("\tDEBUG: preexisting {} in {}; "
                        "skipping").format(p, case_outdir))
            return [p for p in requested_pods if not \
                os.path.isdir(os.path.join(case_outdir, p))
            ]

    def fetch_obs_data(self, timeout=0, dry_run=False):
        dest_dir = self.config['paths']['OBS_DATA_ROOT']
        source_dir = self.config['paths'].get('OBS_DATA_REMOTE', dest_dir)
        if source_dir == dest_dir:
            return
        if not os.path.exists(source_dir) or not os.listdir(source_dir):
            print("Observational data directory at {} is empty.".format(source_dir))
        if not os.path.exists(dest_dir) or not os.listdir(dest_dir):
            print("Observational data directory at {} is empty.".format(dest_dir))
        if gfdl.running_on_PPAN():
            print("\tGCPing data from {}.".format(source_dir))
            # giving -cd to GCP, so will create dirs
            gfdl.gcp_wrapper(source_dir, dest_dir, timeout=timeout, dry_run=dry_run)
        else:
            print("\tSymlinking obs data dir to {}.".format(source_dir))
            dest_parent = os.path.dirname(dest_dir)
            if os.path.exists(dest_dir):
                assert os.path.isdir(dest_dir)
                os.rmdir(dest_dir)
            elif not os.path.exists(dest_parent):
                os.makedirs(dest_parent)
            util.run_command(
                ['ln', '-fs', source_dir, dest_dir], 
                dry_run=dry_run
            )


if __name__ == '__main__':
    mdtf.version_check()
    # get dir of currently executing script: 
    cwd = os.path.dirname(os.path.realpath(__file__)) 
    code_root, src_dir = os.path.split(cwd)
    mdtf = GFDLMDTFFramework(code_root, os.path.join(src_dir, 'defaults_gfdl.json'))
    print("\n======= Starting {}".format(__file__))
    mdtf.main_loop()
    print("Exiting normally from {}".format(__file__))
