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

# configure paths from config.yml; currently no option to override this
cwd = os.path.dirname(os.path.realpath(__file__)) # gets dir of currently executing script
md5_path = os.path.join(cwd,'md5')
with open(os.path.join(cwd,'..','config.yml'), 'r') as file_object:
    config = yaml.safe_load(file_object)
output_path = os.path.realpath(config['paths']['OUTPUT_DIR'])

# find PODs and model data that are present on current system
pods = next(os.walk('var_code'))[1]
pods.remove('html')
pods.remove('util')
if ('MDTF_diagnostics.egg-info') in pods:
    pods.remove('MDTF_diagnostics.egg-info')

# Python 3 has subTest; in 2.7 to avoid introducing other dependencies we use
# the advanced construction presented in https://stackoverflow.com/a/20870875 
# to programmatically generate tests

def generate_test(pod_name, md5_name):
    def test(self):
        os.chdir(output_path)
        self.assertEqual(0, subprocess.check_call(
            "grep '" + pod_name + "' " \
                + os.path.join(md5_path, md5_name+'.md5') \
                + " | md5sum -c --quiet",
            shell=True
        ))
    return test 

class PNGTestSequenceMeta(type):
    def __new__(mcs, name, bases, test_dict):
        for pod in pods:
            test_name = "test_output_png_md5_"+pod
            test_dict[test_name] = generate_test(pod, 'output_png')
        return type.__new__(mcs, name, bases, test_dict)

@unittest.skipIf(('TRAVIS' in os.environ) and (os.environ['TRAVIS']=='true'),
    "Skipping output file md5 tests because running in Travis CI environment")
class TestOutputPNGMD5(unittest.TestCase):
    __metaclass__ = PNGTestSequenceMeta


class NCTestSequenceMeta(type):
    def __new__(mcs, name, bases, test_dict):
        for pod in pods:
            test_name = "test_output_nc_md5_"+pod
            test_dict[test_name] = generate_test(pod, 'output_nc')
        return type.__new__(mcs, name, bases, test_dict)

@unittest.expectedFailure # netcdfs won't be bitwise reproducible
@unittest.skipIf(('TRAVIS' in os.environ) and (os.environ['TRAVIS']=='true'),
    "Skipping output file md5 tests because running in Travis CI environment")
class TestOutputNCMD5(unittest.TestCase):
    __metaclass__ = NCTestSequenceMeta

if __name__ == '__main__':
    unittest.main()

