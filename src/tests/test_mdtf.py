import os
import unittest
import unittest.mock as mock # define mock os.environ so we don't mess up real env vars
from src.core import MDTFFramework
import src.util as util

@unittest.skip("TODO: Test needs to be rewritten following v3 beta 3 release")
class TestMDTFArgParsing(unittest.TestCase):
    def setUp(self):
        _ = configs.PathManager(unittest = True)
        self.config_test = {
            'case_list':[{'A':'B'}],
            'paths':{'C':'/D'},
            'settings':{'E':'F', 'verbose':0}
        }

    def tearDown(self):
        # call _reset method deleting clearing PathManager for unit testing,
        # otherwise the second, third, .. tests will use the instance created
        # in the first test instead of being properly initialized
        temp = configs.PathManager(unittest = True)
        temp._reset()

    def test_parse_mdtf_args_config(self):
        # set paths from config file
        args = {}
        config = self.config_test.copy()
        config = MDTFFramework.parse_mdtf_args(args, config)
        self.assertEqual(config['paths']['C'], '/D')
        self.assertEqual(config['settings']['E'], 'F')

    def test_parse_mdtf_args_config_cmdline(self):
        # override config file with command line arguments
        args = {'C':'/X', 'E':'Y'}
        config = self.config_test.copy()
        config = MDTFFramework.parse_mdtf_args(args, config)
        self.assertEqual(config['paths']['C'], '/X')
        self.assertEqual(config['settings']['E'], 'Y')

    @mock.patch('src.util.check_dir')
    def test_set_mdtf_env_vars_config_settings(self, mock_check_dirs):
        # NB env vars now only written to OS by pod's setup (not here)
        # set settings from config file
        mdtf = MDTFFramework.__new__(MDTFFramework)
        mdtf.config = self.config_test.copy()
        mdtf.set_mdtf_env_vars()
        self.assertEqual(mdtf.config['envvars']['E'], 'F')

    @mock.patch('src.util.check_dir')
    def test_sset_mdtf_env_vars_config_rgb(self, mock_check_dirs):
        # NB env vars now only written to OS by pod's setup (not here)
        # set path to /RGB from os.environ
        mdtf = MDTFFramework.__new__(MDTFFramework)
        mdtf.config = self.config_test.copy()
        mdtf.set_mdtf_env_vars()
        self.assertEqual(mdtf.config['envvars']['RGB'], 'TEST_CODE_ROOT/src/rgb')

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()
