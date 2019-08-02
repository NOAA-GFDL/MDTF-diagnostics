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
obs_path = os.path.realpath(config['paths']['OBS_ROOT_DIR'])
model_path = os.path.realpath(config['paths']['MODEL_ROOT_DIR'])

# find PODs and model data that are present on current system
pods = next(os.walk('var_code'))[1]
pods.remove('html')
pods.remove('util')
if ('MDTF_diagnostics.egg-info') in pods:
    pods.remove('MDTF_diagnostics.egg-info')
models = next(os.walk(model_path))[1]

# Python 3 has subTest; in 2.7 to avoid introducing other dependencies we use
# the advanced construction presented in https://stackoverflow.com/a/20870875 
# to programmatically generate tests

class TestSequenceMeta(type):
    def __new__(mcs, name, bases, test_dict):
        def generate_test(pod_name, md5_name, path):
            def test(self):
                os.chdir(path)
                self.assertEqual(0, subprocess.check_call(
                    "grep '" + pod_name + "' " \
                        + os.path.join(md5_path, md5_name+'.md5') \
                        + " | md5sum -c --quiet",
                    shell=True
                ))
            return test       

        for pod in pods:
            test_name = "test_file_md5_%s" % pod
            test_dict[test_name] = generate_test(pod, 'obs_data', obs_path)

        for model in models:
            test_name = "test_file_md5_%s" % model
            test_dict[test_name] = generate_test(model, 'model', model_path)
        return type.__new__(mcs, name, bases, test_dict)

@unittest.skipIf(('TRAVIS' in os.environ) and (os.environ['TRAVIS']=='true'),
    "Skipping input file md5 tests because running in Travis CI environment")
class TestFileMD5(unittest.TestCase):
    __metaclass__ = TestSequenceMeta

if __name__ == '__main__':
    unittest.main()

