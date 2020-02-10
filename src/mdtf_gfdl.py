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
    def __init__(self, code_root, defaults_rel_path):
        self.set_tempdir()
        super(GFDLMDTFFramework, self).__init__(code_root, defaults_rel_path)

    @staticmethod
    def set_tempdir():
        """Setting tempfile.tempdir causes all temp directories returned by 
        util_mdtf.PathManager to be in that location.
        If we're running on PPAN, recommended practice is to use $TMPDIR
        for scratch work. 
        If we're not, assume we're on a workstation. gcp won't copy to the 
        usual /tmp, so put temp files in a directory on /net2.
        """
        if 'TMPDIR' in os.environ:
            tempfile.tempdir = os.environ['TMPDIR']
        elif os.path.isdir('/net2'):
            tempfile.tempdir = os.path.join('/net2', os.environ['USER'], 'tmp')
            if not os.path.isdir(tempfile.tempdir):
                os.makedirs(tempfile.tempdir)
        else:
            print("Using default tempdir on this system")
        os.environ['MDTF_GFDL_TMPDIR'] = tempfile.gettempdir()

    def parse_mdtf_args(self, cli_obj):
        super(GFDLMDTFFramework, self).parse_mdtf_args(cli_obj)
        self.fetch_obs_data()
        if self.config['settings'].get('frepp', False):
            # set up cooperative mode -- hack to pass config settings
            gfdl.GfdlDiagnostic._config = self.config
            self.config['settings']['diagnostic'] = 'Gfdl'

    # add gfdl to search path for DataMgr, EnvMgr
    _dispatch_search = [data_manager, environment_manager, shared_diagnostic, gfdl]

    def set_case_pod_list(self, case_dict):
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
        dry_run = self.config['settings'].get('dry_run', False)
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
            gfdl.gcp_wrapper(source_dir, dest_dir, dry_run=dry_run)
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
