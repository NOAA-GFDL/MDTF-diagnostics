#!/usr/bin/env python

import os
import tempfile
import data_manager
import environment_manager
import gfdl
import util
import mdtf

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

def fetch_obs_data(obs_data_source, config):
    dry_run = util.get_from_config('dry_run', config, default=False)
    
    obs_data_source = os.path.realpath(obs_data_source)
    dest_dir = config['paths']['OBS_DATA_ROOT']
    if obs_data_source == dest_dir:
        return
    if not os.path.exists(dest_dir) or not os.listdir(dest_dir):
        print "Observational data directory at {} is empty.".format(dest_dir)
    if gfdl.running_on_PPAN():
        print "\tGCPing data from {}.".format(obs_data_source)
        # giving -cd to GCP, so will create dirs
        gfdl.gcp_wrapper(obs_data_source, dest_dir, dry_run=dry_run)
    else:
        print "\tSymlinking obs data dir to {}.".format(obs_data_source)
        dest_parent = os.path.dirname(dest_dir)
        if os.path.exists(dest_dir):
            assert os.path.isdir(dest_dir)
            os.rmdir(dest_dir)
        elif not os.path.exists(dest_parent):
            os.makedirs(dest_parent)
        util.run_command(
            ['ln', '-fs', obs_data_source, dest_dir], 
            dry_run=dry_run
        )

def main():
    print "\n======= Starting "+__file__
    cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
    code_root = os.path.dirname(cwd) # parent dir of that
    set_tempdir()

    cmdline_parser = mdtf.argparse_wrapper(code_root)
    # add GFDL-specific arguments
    cmdline_parser.add_argument("--frepp", 
        action="store_true", # so default to False
        help="Set flag to take configuration info from env vars set by frepp.")
    cmdline_parser.add_argument("--ignore-component", 
        action="store_true", # so default to False
        help="Set flag to ignore model component passed by frepp and search entire /pp/ directory.")
    # reset default config file
    for action in cmdline_parser._actions:
        if action.dest == 'config_file':
            action.default = os.path.join(code_root, 'src', 'gfdl_mdtf_settings.json')

    cmdline_args = mdtf.filter_argparse(cmdline_parser)
    #print cmdline_args
    default_args = util.read_json(cmdline_args['config_file'])
    obs_data_source = default_args['paths']['OBS_DATA_ROOT']
    config = mdtf.parse_mdtf_args(cmdline_args, default_args)
    print 'SETTINGS:\n', util.pretty_print_json(config) #debug

    fetch_obs_data(obs_data_source, config)

    util.PathManager(config['paths']) # initialize
    mdtf.set_mdtf_env_vars(config)
    DataMgr = mdtf.manual_dispatch(
        config['settings']['data_manager'], 'DataManager', 
        [data_manager, gfdl]
    )
    EnvironmentMgr = mdtf.manual_dispatch(
        config['settings']['environment_manager'], 'EnvironmentManager', 
        [environment_manager, gfdl]
    )
    mdtf.main_case_loop(config, DataMgr, EnvironmentMgr)
    print "Exiting normally from ",__file__

if __name__ == '__main__':
    main()
