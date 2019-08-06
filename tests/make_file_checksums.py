#!/usr/bin/env python
import os
import sys
import argparse
import textwrap
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

def checksum_function(file_path):
    IMAGE_FILES = ['.eps','.ps','.png','.gif','.jpg','.jpeg']

    print os.path.split(file_path)[1]
    ext = os.path.splitext(file_path)[1]
    if ext in IMAGE_FILES:
        # use ImageMagick 'identify' command which ignores file creation time 
        # metadata in image header file and only hashes actual image data.
        # See https://stackoverflow.com/a/41706704
        checksum = subprocess.check_output('identify -format "%#" '+file_path, shell=True)
        checksum = checksum.split('\n')[0]
    else:
        # fallback method: system md5
        checksum = subprocess.check_output('md5sum '+file_path, shell=True)
        checksum = checksum.split(' ')[0]
    return checksum

def checksum_files_in_subtree(dir, exclude_exts=[]):
    start_cwd = os.getcwd()
    checksum_dict = {}
    os.chdir(dir)
    # -not -path excludes hidden files from listing
    files = subprocess.check_output('find . -type f -not -path "*/\.*"', shell=True)
    files = files.split('\n')
    # f[2:] removes the "./" at the beginning of each entry
    files = [f[2:] for f in files if 
        f != '' and (os.path.splitext(f)[1] not in exclude_exts)]
    for f in files:
        checksum_dict[f] = checksum_function(os.path.join(dir, f))
    os.chdir(start_cwd)
    return checksum_dict

def checksum_in_subtree_1(rootdir, exclude_exts=[]):
    # descend into subdirectories, then flatten file hierarchy
    checksum_dict = {}
    dirs1 = next(os.walk(rootdir))[1]
    for d1 in dirs1:
        checksum_dict[d1] = checksum_files_in_subtree(os.path.join(rootdir, d1), exclude_exts)
    return checksum_dict

def checksum_in_subtree_2(rootdir, exclude_exts=[]):
    # same except we descend 2 levels deep and then flatten
    checksum_dict = {}
    dirs1 = next(os.walk(rootdir))[1]
    for d1 in dirs1:
        checksum_dict[d1] = {}
        dirs2 = next(os.walk(os.path.join(rootdir, d1)))[1]
        for d2 in dirs2:
            checksum_dict[d1][d2] = checksum_files_in_subtree(
                os.path.join(rootdir, d1, d2), exclude_exts)
    return checksum_dict

# wrap these so we can import them in the test functions
def make_input_data_dict(path):
    return checksum_in_subtree_1(path)

def make_output_data_dict(path):
    return checksum_in_subtree_2(path, ['.tar','.tar_old','.log','.yml'])

if __name__ == '__main__':
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

    md5_path = os.path.join(os.environ['DIAG_HOME'],'tests','checksums')
    header = """
        # This file was produced by make_file_checksums.py and is used by the
        # test_*_checksums.py unit tests. Don't modify it by hand!
        #
        """

    print 'Hashing input observational data'
    checksum_dict = make_input_data_dict(os.environ['OBS_ROOT_DIR'])
    with open(os.path.join(md5_path, 'checksum_obs_data.yml'), 'w') as file_obj:
        file_obj.write(textwrap.dedent(header))
        yaml.dump(checksum_dict, file_obj)

    print 'Hashing input model data'
    checksum_dict = make_input_data_dict(os.environ['MODEL_ROOT_DIR'])
    with open(os.path.join(md5_path, 'checksum_model_data.yml'), 'w') as file_obj:
        file_obj.write(textwrap.dedent(header))
        yaml.dump(checksum_dict, file_obj)

    print 'Hashing output data'
    checksum_dict = make_output_data_dict(os.environ['OUTPUT_DIR'])
    with open(os.path.join(md5_path, 'checksum_output.yml'), 'w') as file_obj:
        file_obj.write(textwrap.dedent(header))
        yaml.dump(checksum_dict, file_obj)