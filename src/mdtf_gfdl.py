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
from src import cli, util, util_mdtf, data_manager, environment_manager, \
    diagnostic, mdtf
from src import gfdl, gfdl_util

def main(code_root, cli_rel_path):
    # poor man's subparser: argparse's subparser doesn't handle this
    # use case easily, so just dispatch on first argument
    if len(sys.argv) == 1 or \
        len(sys.argv) == 2 and sys.argv[1].lower().endswith('help'):
        # build CLI, print its help and exit
        cli_obj = cli.FrameworkCLIHandler(code_root, cli_rel_path)
        cli_obj.parser.print_help()
    elif sys.argv[1].lower() == 'info': 
        # "subparser" for command-line info
        cli.InfoCLIHandler(code_root, sys.argv[2:])
    else:
        # not printing help or info, setup CLI normally 
        # move into its own class so that child classes can customize
        # above options without having to rewrite below
        config = gfdl_util.GFDLConfigManager(code_root, cli_rel_path)
        framework = mdtf.MDTFFramework(
            config,
            (gfdl, data_manager, environment_manager, diagnostic)
        )
        print(f"\n======= Starting {__file__}")
        bad_exit = framework.main_loop()
        if bad_exit:
            exit(1)

# should move this out of "src" package, but need to create wrapper shell script
# to set framework conda env.
if __name__ == '__main__':
    # get dir of currently executing script: 
    cwd = os.path.dirname(os.path.realpath(__file__)) 
    code_root, src_dir = os.path.split(cwd)
    defaults_rel_path = os.path.join(src_dir, 'cli_gfdl.jsonc')
    if not os.path.exists(defaults_rel_path):
        # print('Warning: site-specific cli.jsonc not found, using template.')
        defaults_rel_path = os.path.join(src_dir, 'cli_template.jsonc')

    main(code_root, defaults_rel_path)
    exit(0)
