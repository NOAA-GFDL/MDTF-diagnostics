#!/usr/bin/env python
import os
import sys
import argparse
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except (ImportError, ModuleNotFoundError):
        import subprocess
    else:
        import subprocess
import yaml
cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
sys.path.insert(0, os.path.realpath(os.path.join(cwd, '..', 'var_code')))
import util

parser = argparse.ArgumentParser()
parser.add_argument('config_file', nargs='?', type=str, 
                    default=os.path.realpath(os.path.join(cwd, '..','config.yml')),
                    help="Configuration file.")
args = parser.parse_args()

try:
    config = util.read_mdtf_config_file(args.config_file)
except Exception as error:
    print error
    exit()
util.set_mdtf_env_vars(args, config)
util.check_required_dirs(
   already_exist =["MODEL_ROOT_DIR","OBS_ROOT_DIR"], 
   create_if_nec = ["OUTPUT_DIR"])

md5_path = os.path.join(os.environ['DIAG_HOME'],'tests','md5')

print 'Hashing input observational data'
os.chdir(os.environ['OBS_ROOT_DIR'])
subprocess.call(
    "find . -type f -not -path '*/\.*' -print0 | xargs -0 md5sum > " \
        + os.path.join(md5_path,'obs_data.md5'),
    shell = True
)

print 'Hashing input model data'
os.chdir(os.environ['MODEL_ROOT_DIR'])
subprocess.call(
    "find . -type f -not -path '*/\.*' -print0 | xargs -0 md5sum > " \
        + os.path.join(md5_path,'model.md5'),
    shell = True
)

print 'Hashing output netCDF data'
os.chdir(os.environ['OUTPUT_DIR'])
subprocess.call(
    "find . -type f -name '*.nc' -print0 | xargs -0 md5sum > " \
        + os.path.join(md5_path,'output_nc.md5'),
    shell = True
)

print 'Hashing output figures'
ext = config['settings']['convert_output_fmt']
os.chdir(os.environ['OUTPUT_DIR'])
subprocess.call(
    "find . -type f -name '*." + ext + "' -print0 | xargs -0 md5sum > " \
        + os.path.join(md5_path,'output_'+ext+'.md5'),
    shell = True
)