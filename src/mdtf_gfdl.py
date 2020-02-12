#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
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
        ### call parent class method
        super(GFDLMDTFFramework, self).parse_mdtf_args(cli_obj)

        # copy obs data from site install
        self.fetch_obs_data()
        # set up cooperative mode -- hack to pass config settings
        if self.config['settings'].get('frepp', False):
            gfdl.GfdlDiagnostic._config = self.config
            self.config['settings']['diagnostic'] = 'Gfdl'

    def parse_env_vars(self, cli_obj):
        # set temp directory according to where we're running
        if gfdl.running_on_PPAN():
            gfdl_tmp_dir = cli_obj.config.get('GFDL_PPAN_TEMP', '$TMPDIR')
        else:
            gfdl_tmp_dir = cli_obj.config.get('GFDL_WS_TEMP', '$TMPDIR')
        gfdl_tmp_dir = mdtf._mdtf_resolve_path(gfdl_tmp_dir, cli_obj)
        if not os.path.isdir(gfdl_tmp_dir):
            gfdl.make_remote_dir(gfdl_tmp_dir)
        tempfile.tempdir = gfdl_tmp_dir
        os.environ['MDTF_GFDL_TMPDIR'] = gfdl_tmp_dir

        ### call parent class method
        super(GFDLMDTFFramework, self).parse_env_vars(cli_obj)

    def parse_paths(self, cli_obj):
        self.paths = dict()
        for key, val in cli_obj.iteritems_cli('PATHS'):
            val2 = self._mdtf_resolve_path(val, cli_obj)
            # print('\tDEBUG: {},{},{}'.format(key, val, val2))
            self.paths[key] = val2

        # clean out WORKING_DIR if we're not keeping temp files
        if not cli_obj.config.get('keep_temp', False):
            shutil.rmtree(self.paths['WORKING_DIR'])
        util_mdtf.check_required_dirs(
            already_exist = [
                self.paths['CODE_ROOT'], self.paths['OBS_DATA_REMOTE']
            ], 
            create_if_nec = [
                self.paths['MODEL_DATA_ROOT'], self.paths['WORKING_DIR'],
                self.paths['OBS_DATA_ROOT']
        ])
        # Use GCP to create OUTPUT_DIR on a volume that may be read-only
        if not os.path.exists(self.paths['OUTPUT_DIR']):
            gfdl.make_remote_dir(
                self.paths['OUTPUT_DIR'], self.timeout, self.dry_run
            )

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

    def fetch_obs_data(self):
        dest_dir = self.paths['OBS_DATA_ROOT']
        source_dir = self.paths['OBS_DATA_REMOTE']
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
                source_dir, dest_dir, timeout=self.timeout, dry_run=self.dry_run
            )
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
                dry_run=self.dry_run
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
