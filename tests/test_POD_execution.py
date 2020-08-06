import os
import sys
import unittest
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
    else:
        import subprocess
from src.util import write_json
from tests import shared_test_utils as shared

DOING_TRAVIS = (os.environ.get('TRAVIS', False) == 'true')
DOING_MDTF_DATA_TESTS = ('--data_tests' in sys.argv)
DOING_SETUP = DOING_MDTF_DATA_TESTS and not DOING_TRAVIS
# All this is a workaround because tests are programmatically generated at 
# import time, but the tests are skipped at runtime. We're skipping tests 
# because we're not in an environment where we have the data to set them up,
# so we just throw everything in an if-block to ensure they don't get generated
# if they're going to be skipped later.

if DOING_SETUP:
    config = shared.get_configuration('', check_input = True)
    out_path = config['paths']['OUTPUT_DIR']

    case_list = shared.get_test_data_configuration()

    # write temp configuration, one for each POD  
    temp_config = config.copy()
    temp_config['pod_list'] = []
    temp_config['settings']['make_variab_tar'] = False
    temp_config['settings']['test_mode'] = True

    pod_configs = shared.configure_pods(case_list, config_to_insert=temp_config)
    for pod in case_list['pods']:
        write_json(pod_configs[pod], os.path.join(out_path, pod+'_temp.json'))


# Python 3 has subTest; in 2.7 to avoid introducing other dependencies we use
# the advanced construction presented in https://stackoverflow.com/a/20870875 
# to programmatically generate tests

class TestSequenceMeta(type):
    def __new__(mcs, name, bases, test_dict):
        def generate_test(pod_name):
            def test(self):
                temp_config_file = os.path.join(out_path, pod_name+'_temp.json')
                self.assertEqual(0, subprocess.check_call(
                    ['python', 'src/mdtf.py', temp_config_file]
                ))
                # should do better cleanup here
            return test       

        if DOING_SETUP:
            for pod in case_list['pods']:
                test_name = "test_pod_" + pod
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