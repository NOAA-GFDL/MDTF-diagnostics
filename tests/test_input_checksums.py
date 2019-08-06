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
from make_file_checksums import checksum_files_in_subtree

DOING_TRAVIS = (os.environ.get('TRAVIS', False) == 'true')
DOING_MDTF_DATA_TESTS = ('--data_tests' in sys.argv)
DOING_SETUP = DOING_MDTF_DATA_TESTS and not DOING_TRAVIS
# All this is a workaround because tests are programmatically generated at 
# import time, but the tests are skipped at runtime. We're skipping tests 
# because we're not in an environment where we have the data to set them up,
# so we just throw everything in an if-block to ensure they don't get generated
# if they're going to be skipped later.

if DOING_SETUP:
    # configure paths from config.yml; currently no option to override this
    cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
    md5_path = os.path.join(cwd,'checksums')
    with open(os.path.join(cwd,'..','config.yml'), 'r') as file_object:
        config = yaml.safe_load(file_object)
    obs_path = os.path.realpath(config['paths']['OBS_ROOT_DIR'])
    model_path = os.path.realpath(config['paths']['MODEL_ROOT_DIR'])

    # find PODs and model data that are present on current system
    pods = next(os.walk(obs_path))[1]
    models = next(os.walk(model_path))[1]

    with open(os.path.join(md5_path, 'checksum_obs_data.yml'), 'r') as file_obj:
        obs_data_checksums = yaml.safe_load(file_obj)
    with open(os.path.join(md5_path, 'checksum_model_data.yml'), 'r') as file_obj:
        model_data_checksums = yaml.safe_load(file_obj)

# Python 3 has subTest; in 2.7 to avoid introducing other dependencies we use
# the advanced construction presented in https://stackoverflow.com/a/20870875 
# to programmatically generate tests

class TestSequenceMeta(type):
    def __new__(mcs, name, bases, test_dict):
        def generate_test(name, path, reference_dict):
            def test(self):
                self.assertIn(name, reference_dict)
                if name not in reference_dict: 
                    self.skipTest('Skipping rest of test: {} not found.'.format(name))
                test_dict = checksum_files_in_subtree(os.path.join(path, name))
                for key in reference_dict[name]:
                    self.assertIn(key, test_dict,
                        'Failure: {} not found in {}'.format(key, os.path.join(path, name)))
                    self.assertEqual(test_dict[key], reference_dict[name][key],
                        'Failure: Hash of {} differs from reference.'.format(os.path.join(path, name, key)))
            return test       

        if DOING_SETUP:
            for pod in pods:
                test_name = "test_input_checksum_"+pod
                test_dict[test_name] = generate_test(pod, obs_path, obs_data_checksums)

            for model in models:
                test_name = "test_input_checksum_"+model
                test_dict[test_name] = generate_test(model, model_path, model_data_checksums)
        return type.__new__(mcs, name, bases, test_dict)

@unittest.skipIf(DOING_TRAVIS,
    "Skipping input file md5 tests because running in Travis CI environment")
@unittest.skipUnless(DOING_MDTF_DATA_TESTS,
    "Skipping input file md5 tests because not running data-intensive test suite.")
class TestInputChecksums(unittest.TestCase):
    __metaclass__ = TestSequenceMeta

if __name__ == '__main__':
    unittest.main()

