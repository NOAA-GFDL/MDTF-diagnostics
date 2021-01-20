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
from src.util import read_json
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
    config = shared.get_configuration('', check_output=True)
    md5_path = config['paths']['md5_path']
    out_path = config['paths']['OUTPUT_DIR']

    case_list = shared.get_test_data_configuration()

    output_checksums = read_json(os.path.join(md5_path, 'checksum_output.json'))

# Python 3 has subTest; in 2.7 to avoid introducing other dependencies we use
# the advanced construction presented in https://stackoverflow.com/a/20870875 
# to programmatically generate tests   

class PNGTestSequenceMeta(type):
    def __new__(mcs, name, bases, test_dict):
        if DOING_SETUP:
            for case in case_list['case_list']:
                case_path = os.path.join(out_path, case['dir'])
                for pod in case['pod_list']:
                    test_name = "test_output_png_md5_"+pod
                    test_dict[test_name] = shared.generate_checksum_test(
                        pod, case_path, output_checksums[case['dir']], ['.png'])
        return type.__new__(mcs, name, bases, test_dict)

@unittest.skipIf(DOING_TRAVIS,
    "Skipping output file md5 tests because running in Travis CI environment")
@unittest.skipUnless(DOING_MDTF_DATA_TESTS,
    "Skipping output file md5 tests because not running data-intensive test suite.")
class TestOutputPNGMD5(unittest.TestCase):
    __metaclass__ = PNGTestSequenceMeta


class NCTestSequenceMeta(type):
    def __new__(mcs, name, bases, test_dict):
        if DOING_SETUP:
            for case in case_list['case_list']:
                case_path = os.path.join(out_path, case['dir'])
                for pod in case['pod_list']:
                    test_name = "test_output_png_md5_"+pod
                    test_dict[test_name] = shared.generate_checksum_test(
                        pod, case_path, output_checksums[case['dir']], ['.nc'])
        return type.__new__(mcs, name, bases, test_dict)

@unittest.expectedFailure # netcdfs won't be bitwise reproducible
@unittest.skipIf(DOING_TRAVIS,
    "Skipping output file md5 tests because running in Travis CI environment")
@unittest.skipUnless(DOING_MDTF_DATA_TESTS,
    "Skipping output file md5 tests because not running data-intensive test suite.")
class TestOutputNCMD5(unittest.TestCase):
    __metaclass__ = NCTestSequenceMeta

if __name__ == '__main__':
    unittest.main()

