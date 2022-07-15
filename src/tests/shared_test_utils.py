import os
import sys
import collections
import dataclasses
import subprocess
from src.util import read_json, NameSpace, to_iter
from src import core, cli

@dataclasses.dataclass
class DummyMDTFFramework(object):
    code_root: str = ""
    pod_list: list = dataclasses.field(default_factory=list)
    case_list: list = dataclasses.field(default_factory=list)
    cases: list = dataclasses.field(default_factory=list)
    global_env_vars: dict = dataclasses.field(default_factory=dict)


def setUp_config_singletons(config=None, paths=None, pods=None, unittest=True):
    cwd = os.path.dirname(os.path.realpath(__file__))
    code_root = os.path.dirname(os.path.dirname(cwd))
    cli_obj = cli.MDTFTopLevelArgParser(
        code_root,
        skip_defaults=True,
        argv= f"-f {os.path.join(cwd, 'dummy_config.json')}"
    )
    cli_obj.config = vars(cli_obj.parse_args())
    if config:
        cli_obj.config.update(config)

    PodDataTuple = collections.namedtuple(
        'PodDataTuple', 'sorted_lists pod_data realm_data'
    )
    dummy_pod_data = PodDataTuple(
        pod_data=pods, realm_data=dict(), sorted_lists={'pods': [], 'realms':[]}
    )

    _ = core.ConfigManager(cli_obj, dummy_pod_data, unittest=unittest)
    pm = core.PathManager(cli_obj, unittest=unittest)
    pm.CODE_ROOT = code_root
    if paths:
        pm.update(paths)
    translate = core.VariableTranslator(code_root, unittest=unittest)
    translate.read_conventions(code_root, unittest=unittest)
    _ = core.TempDirManager(None, unittest=unittest)

def tearDown_config_singletons():
    # clear Singletons
    try:
        temp = core.ConfigManager(unittest=True)
        temp._reset()
    except Exception:
        pass
    try:
        temp = core.PathManager(unittest=True)
        temp._reset()
    except Exception:
        pass
    try:
        temp = core.VariableTranslator(unittest=True)
        temp._reset()
    except Exception:
        pass
    try:
        temp = core.TempDirManager(unittest=True)
        temp._reset()
    except Exception:
        pass

# -------------------------------------------------------------

def get_configuration(config_file='', check_input=False, check_output=False):
    # Redundant with code in util; need to fix this
    cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
    code_root = os.path.realpath(os.path.join(cwd, '..')) # parent dir of that
    if config_file == '':
        config_file = os.path.join(cwd,'..','src','mdtf_settings.json') # default
    config = read_json(config_file)
    config = parse_mdtf_args(None, config, rel_paths_root=code_root)
    config['paths']['md5_path'] = os.path.join(cwd,'checksums')

    # config['paths']['OBS_ROOT_DIR'] = os.path.realpath(config['paths']['OBS_ROOT_DIR'])
    # config['paths']['MODEL_ROOT_DIR'] = os.path.realpath(config['paths']['MODEL_ROOT_DIR'])
    # config['paths']['OUTPUT_DIR'] = os.path.realpath(config['paths']['OUTPUT_DIR'])


    # assert os.path.isdir(config['paths']['md5_path'])
    # if check_input:
    #     assert os.path.isdir(config['paths']['OBS_ROOT_DIR'])
    #     assert os.path.isdir(config['paths']['MODEL_ROOT_DIR'])
    # if check_output:
    #     assert os.path.isdir(config['paths']['OUTPUT_DIR'])
    return config

def get_test_data_configuration():
    cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
    case_list = read_json(os.path.join(cwd,'pod_test_configs.json'))
    models = []
    pods = []
    for i, case in enumerate(case_list['case_list']):
        case_list['case_list'][i]['dir'] = 'MDTF_{}_{}_{}'.format(
            case['CASENAME'], case['FIRSTYR'], case['LASTYR'])
        models.append(case['CASENAME'])
        pods.extend(case['pod_list'])
    case_list['pods'] = pods
    case_list['models'] = models
    return case_list

def configure_pods(case_list, config_to_insert=[]):
    # set up configuration, one for each POD
    cases_by_pod = {}
    for case in case_list['case_list']:
        temp_case = case.copy()
        for pod in case['pod_list']:
            if config_to_insert != []:
                cases_by_pod[pod] = config_to_insert.copy()
            cases_by_pod[pod]['case_list'] = [temp_case]
            cases_by_pod[pod]['case_list'][0]['pod_list'] = [pod]
    return cases_by_pod

def checksum_function(file_path):
    IMAGE_FILES = ['.eps','.ps','.png','.gif','.jpg','.jpeg']

    print(os.path.split(file_path)[1])
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
    # '-not -path ..' excludes hidden files from listing
    files = subprocess.check_output('find . -type f -not -path "*/\.*"', shell=True)
    files = files.split('\n')
    # f[2:] removes the "./" at the beginning of each entry
    files = [f[2:] for f in files if
        f != '' and (os.path.splitext(f)[1] not in exclude_exts)]
    for f in files:
        checksum_dict[f] = checksum_function(os.path.join(dir, f))
    os.chdir(start_cwd)
    return checksum_dict

def generate_checksum_test(name, path, reference_dict, include_exts=[]):
    def test(self):
        self.assertIn(name, reference_dict)
        if name not in reference_dict:
            self.skipTest('Skipping rest of test: {} not found.'.format(name))
        test_dict = checksum_files_in_subtree(os.path.join(path, name))
        for key in reference_dict[name]:
            ext = os.path.splitext(key)[1]
            if include_exts == [] or (ext in include_exts):
                self.assertIn(key, test_dict,
                    'Failure: {} not found in {}'.format(
                        key, os.path.join(path, name)))
                self.assertEqual(test_dict[key], reference_dict[name][key],
                    'Failure: Hash of {} differs from reference.'.format(
                        os.path.join(path, name, key)))
    return test

