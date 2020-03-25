import os
import sys
import unittest
from src.util import read_json
import shared_test_utils as shared

DOING_TRAVIS = (os.environ.get('TRAVIS', False) == 'true')
DOING_MDTF_DATA_TESTS = ('--data_tests' in sys.argv)
DOING_SETUP = DOING_MDTF_DATA_TESTS and not DOING_TRAVIS
# All this is a workaround because tests are programmatically generated at 
# import time, but the tests are skipped at runtime. We're skipping tests 
# because we're not in an environment where we have the data to set them up,
# so we just throw everything in an if-block to ensure they don't get generated
# if they're going to be skipped later.

if DOING_SETUP:
    config = shared.get_configuration('', check_input=True)
    md5_path = config['paths']['md5_path']
    obs_path = config['paths']['OBS_DATA_ROOT']
    model_path = config['paths']['MODEL_DATA_ROOT']

    case_list = shared.get_test_data_configuration()

    obs_data_checksums = read_json(os.path.join(md5_path, 'checksum_obs_data.json'))
    model_data_checksums = read_json(os.path.join(md5_path, 'checksum_model_data.json'))

# Python 3 has subTest; in 2.7 to avoid introducing other dependencies we use
# the advanced construction presented in https://stackoverflow.com/a/20870875 
# to programmatically generate tests

class TestSequenceMeta(type):
    def __new__(mcs, name, bases, test_dict):     
        if DOING_SETUP:
            for pod in case_list['pods']:
                test_name = "test_input_checksum_"+pod
                test_dict[test_name] = shared.generate_checksum_test(
                    pod, obs_path, obs_data_checksums)

            for model in case_list['models']:
                test_name = "test_input_checksum_"+model
                test_dict[test_name] = shared.generate_checksum_test(
                    model, model_path, model_data_checksums)
        return type.__new__(mcs, name, bases, test_dict)

@unittest.skipIf(DOING_TRAVIS,
    "Skipping input file md5 tests because running in Travis CI environment")
@unittest.skipUnless(DOING_MDTF_DATA_TESTS,
    "Skipping input file md5 tests because not running data-intensive test suite.")
class TestInputChecksums(unittest.TestCase):
    __metaclass__ = TestSequenceMeta

if __name__ == '__main__':
    unittest.main()

