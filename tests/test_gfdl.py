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
from src.util import write_yaml, run_commands
import shared_test_utils as shared
import src.gfdl as gfdl

DOING_TRAVIS = (os.environ.get('TRAVIS', False) == 'true')
DOING_MDTF_DATA_TESTS = ('--data_tests' in sys.argv)
DOING_SETUP = DOING_MDTF_DATA_TESTS and not DOING_TRAVIS
# All this is a workaround because tests are programmatically generated at 
# import time, but the tests are skipped at runtime. We're skipping tests 
# because we're not in an environment where we have the data to set them up,
# so we just throw everything in an if-block to ensure they don't get generated
# if they're going to be skipped later.

# if DOING_SETUP:
#     config = shared.get_configuration('', check_input = True)
#     out_path = config['paths']['OUTPUT_DIR']

#     case_list = shared.get_test_data_configuration()

#     # write temp configuration, one for each POD  
#     temp_config = config.copy()
#     temp_config['pod_list'] = []
#     temp_config['settings']['make_variab_tar'] = False
#     temp_config['settings']['test_mode'] = True

#     pod_configs = shared.configure_pods(case_list, config_to_insert=temp_config)
#     for pod in case_list['pods']:
#         write_yaml(pod_configs[pod], os.path.join(out_path, pod+'_temp.yml'))

@unittest.skipIf(DOING_TRAVIS,
    "Skipping POD execution tests because running in Travis CI environment")
@unittest.skipUnless(DOING_MDTF_DATA_TESTS,
    "Skipping POD execution tests because not running data-intensive test suite.")
class TestModuleManager(unittest.TestCase):

    test_mod_name = 'latexdiff/1.2.0' # least likely to cause side effects?

    def setUp(self):
        temp = gfdl.ModuleManager()

    def tearDown(self):
        # call _reset method clearing ModuleManager for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = gfdl.ModuleManager()
        temp.revert_state()
        temp._reset()

    def test_module_envvars(self):
        self.assertIn('MODULESHOME', os.environ)
        self.assertIn('MODULE_VERSION', os.environ)
        self.assertIn('LOADEDMODULES', os.environ)
        self.assertEqual(
            '/usr/local/Modules/'+os.environ['MODULE_VERSION'],
            os.environ['MODULESHOME']
        )

    def test_module_list(self):
        cmd = '{}/bin/modulecmd'.format(os.environ['MODULESHOME'])
        # module list writes to stderr, because all module user output does
        list1 = subprocess.check_output([cmd, 'python', 'list', '-t'], 
            stderr=subprocess.STDOUT).splitlines()
        del list1[0]
        list1 = set([s.replace('(default)','') for s in list1])
        modMgr = gfdl.ModuleManager()
        list2 = set(modMgr.list())
        self.assertEqual(list1, list2)

    def test_module_load(self):
        modMgr = gfdl.ModuleManager()
        modMgr.load(self.test_mod_name)
        mod_list = modMgr.list()
        self.assertIn(self.test_mod_name, mod_list)

    def test_module_unload(self):
        modMgr = gfdl.ModuleManager()
        modMgr.load(self.test_mod_name)
        mod_list = modMgr.list()
        self.assertIn(self.test_mod_name, mod_list)
        modMgr.unload(self.test_mod_name)
        mod_list = modMgr.list()
        self.assertNotIn(self.test_mod_name, mod_list)



if __name__ == '__main__':
    unittest.main()