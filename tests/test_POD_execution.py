import os
import sys
import unittest
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except (ImportError, ModuleNotFoundError):
        import subprocess
    else:
        import subprocess
import yaml

DOING_TRAVIS = (os.environ.get('TRAVIS', False) == 'true')
DOING_MDTF_DATA_TESTS = ('--data_tests' in sys.argv)

# configure paths from config.yml; currently no option to override this
cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
md5_path = os.path.join(cwd,'md5')
with open(os.path.join(cwd,'..','config.yml'), 'r') as file_object:
    config = yaml.safe_load(file_object)
temp_config = config.copy()
temp_config['pod_list'] = []
temp_config['settings']['make_variab_tar'] = False
# temp_config['settings']['test_mode'] = True

obs_path = os.path.realpath(config['paths']['OBS_ROOT_DIR'])
model_path = os.path.realpath(config['paths']['MODEL_ROOT_DIR'])
out_path = os.path.realpath(config['paths']['OUTPUT_DIR'])

# find PODs that are present on current system
pods = next(os.walk('var_code'))[1]
pods.remove('html')
pods.remove('util')
if ('MDTF_diagnostics.egg-info') in pods:
    pods.remove('MDTF_diagnostics.egg-info')

# set up configuration, one for each POD
with open(os.path.join(cwd,'pod_test_configs.yml'), 'r') as file_object:
    cases = yaml.safe_load(file_object) 
pod_configs = {}
found_pods = []
for case_list in cases['case_list']:
    temp_case = case_list.copy()
    for pod in case_list['pod_list']:
        if pod in pods:
            found_pods.append(pod)
            pod_configs[pod] = temp_config.copy()
            pod_configs[pod]['case_list'] = [temp_case]
            pod_configs[pod]['case_list'][0]['pod_list'] = [pod]

            temp_config_file = os.path.join(out_path, pod+'_temp.yml')
            with open(temp_config_file,'w') as file_object:
                yaml.dump(pod_configs[pod], file_object)

# Python 3 has subTest; in 2.7 to avoid introducing other dependencies we use
# the advanced construction presented in https://stackoverflow.com/a/20870875 
# to programmatically generate tests

class TestSequenceMeta(type):
    def __new__(mcs, name, bases, test_dict):
        def generate_test(pod_name):
            def test(self):
                temp_config_file = os.path.join(out_path, pod_name+'_temp.yml')
                self.assertEqual(0, subprocess.check_call(
                    ['python', 'mdtf.py', temp_config_file]
                ))
                # should do better cleanup here
            return test       

        for pod in found_pods:
            test_name = "test_pod_%s" % pod
            test_dict[test_name] = generate_test(pod)
        return type.__new__(mcs, name, bases, test_dict)

@unittest.skipIf(DOING_TRAVIS,
    "Skipping POD execution tests because running in Travis CI environment")
@unittest.skipUnless(DOING_MDTF_DATA_TESTS,
    "Skipping POD execution tests because not running data-intensive test suite.")
class TestPODExecution(unittest.TestCase):
    __metaclass__ = TestSequenceMeta

if __name__ == '__main__':
    unittest.main()