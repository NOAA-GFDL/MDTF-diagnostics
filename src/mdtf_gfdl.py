#!/usr/bin/env python

import os
import tempfile
import data_manager
import environment_manager
import gfdl
import util
from mdtf import MDTFFramework

class GFDLMDTFFramework(MDTFFramework):
    def __init__(self):
        self.set_tempdir()
        super(GFDLMDTFFramework, self).__init__()


    @staticmethod
    def set_tempdir():
        """Setting tempfile.tempdir causes all temp directories returned by 
        util.PathManager to be in that location.
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
            print "Using default tempdir on this system"
        os.environ['MDTF_GFDL_TMPDIR'] = tempfile.gettempdir()

    def argparse_setup(self):
        """Add GFDL-specific command-line options to those set in mdtf.py.
        """
        super(GFDLMDTFFramework, self).argparse_setup()
        self.parser.add_argument("--frepp", 
            action="store_true", # so default to False
            help="Set flag to take configuration info from env vars set by frepp.")
        self.parser.add_argument("--ignore-component", 
            action="store_true", # so default to False
            help="Set flag to ignore model component passed by frepp and search entire /pp/ directory.")
        # reset default config file
        for action in self.parser._actions:
            if action.dest == 'config_file':
                action.default = os.path.join(self.code_root, 'src', 
                    'gfdl_mdtf_settings.json')

    @classmethod
    def parse_mdtf_args(cls, user_args_list, default_args, rel_paths_root=''):
        default_args['paths']['OBS_DATA_SOURCE'] = util.resolve_path(
            default_args['paths']['OBS_DATA_ROOT'],
            rel_paths_root)
        return super(GFDLMDTFFramework, cls).parse_mdtf_args(
            user_args_list, default_args, rel_paths_root)

    def _post_config_init(self):
        self.fetch_obs_data()
        super(GFDLMDTFFramework, self)._post_config_init()
        if self.config['settings']['frepp']:
            # set up cooperative mode -- hack to pass config settings
            gfdl.GfdlDiagnostic._config = self.config
            self.Diagnostic = gfdl.GfdlDiagnostic

    # add gfdl to search path for DataMgr, EnvMgr
    _dispatch_search = [data_manager, environment_manager, gfdl]

    def set_case_pod_list(self, case_dict):
        requested_pods = super(GFDLMDTFFramework, self).set_case_pod_list(case_dict)
        if not self.config['settings']['frepp']:
            # try to run everything if not in frepp cooperative mode
            return requested_pods 
        else:
            # only attempt PODs other instances haven't already done
            paths = util.PathManager()
            case_outdir = paths.modelPaths(case_dict)['MODEL_OUT_DIR']
            return [p for p in requested_pods if not \
                os.path.isdir(os.path.join(case_outdir, p))
            ]

    def fetch_obs_data(self):
        dry_run = util.get_from_config('dry_run', self.config, default=False)
        
        source_dir = self.config['paths']['OBS_DATA_SOURCE']
        dest_dir = self.config['paths']['OBS_DATA_ROOT']
        if source_dir == dest_dir:
            return
        if not os.path.exists(dest_dir) or not os.listdir(dest_dir):
            print "Observational data directory at {} is empty.".format(dest_dir)
        if gfdl.running_on_PPAN():
            print "\tGCPing data from {}.".format(source_dir)
            # giving -cd to GCP, so will create dirs
            gfdl.gcp_wrapper(source_dir, dest_dir, dry_run=dry_run)
        else:
            print "\tSymlinking obs data dir to {}.".format(source_dir)
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
    print "\n======= Starting "+__file__
    mdtf = GFDLMDTFFramework()
    mdtf.main_loop()
    print "Exiting normally from ",__file__
