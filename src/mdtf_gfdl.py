import os
import data_manager
import environment_manager
import gfdl
import util
import mdtf

def manual_dispatch(class_name):
    # search GFDL module namespace as well
    for mod in [data_manager, environment_manager, gfdl]:
        try:
            return getattr(mod, class_name)
        except:
            continue
    print "No class named {}.".format(class_name)
    raise Exception('no_class')

def main():
    print "==== Starting "+__file__
    cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
    code_root = os.path.realpath(os.path.join(cwd, '..')) # parent dir of that
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
            action.default = os.path.join(code_root, 'src', 'config_gfdl.yml'),
        else:
            raise AssertionError('config_file setting not found.') 

    cmdline_args = mdtf.filter_argparse(cmdline_parser)
    print cmdline_args
    default_args = util.read_yaml(cmdline_args['config_file'])
    config = mdtf.parse_mdtf_args(cmdline_args, default_args)
    print config #debug

    util.PathManager(config['paths']) # initialize
    mdtf.set_mdtf_env_vars(config)
    DataMgr = manual_dispatch(
        config['settings']['data_manager'].title()+'DataManager'
    )
    EnvironmentMgr = manual_dispatch(
        config['settings']['environment_manager'].title()+'EnvironmentManager'
    )
    mdtf.main_case_loop(config, DataMgr, EnvironmentMgr)
    print "Exiting normally from ",__file__

if __name__ == '__main__':
    main()