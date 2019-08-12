import os
import sys
import collections
import unittest
import mock # define mock os.environ so we don't mess up real env vars
from src.shared_runner import DiagnosticRunner

class TestDiagnosticRunner(unittest.TestCase):
    config_test = {
        'case_list':[{'A':'B'}],
        'paths':{'C':'/D'},
        'settings':{'E':'F', 'verbose':0}
    }
    # do this because 1st argument to set_mdtf_env_vars is object containing
    # parsed command-line arguments, accessed via its attributes
    MockArgs = collections.namedtuple('MockArgs', ['C', 'E'])

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_runner.util.check_required_dirs')
    def test_set_mdtf_env_vars_config_paths(self, mock_check_required_dirs):
        # set paths from config file
        args = TestDiagnosticRunner.MockArgs(None, None)
        config = self.config_test.copy()
        runner = DiagnosticRunner(args, config)
        self.assertEqual(config['envvars']['C'], '/D')
        self.assertEqual(os.environ['C'], '/D')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_runner.util.check_required_dirs')
    def test_set_mdtf_env_vars_config_settings(self, mock_check_required_dirs):
        # set settings from config file
        args = TestDiagnosticRunner.MockArgs(None, None)
        config = self.config_test.copy()
        runner = DiagnosticRunner(args, config)
        self.assertEqual(config['envvars']['A'], 'B')
        self.assertEqual(os.environ['A'], 'B')
        self.assertEqual(config['envvars']['E'], 'F')
        self.assertEqual(os.environ['E'], 'F')        

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_runner.util.check_required_dirs')
    def test_set_mdtf_env_vars_config_rgb(self, mock_check_required_dirs):
        # set path to /RGB from os.environ
        args = TestDiagnosticRunner.MockArgs(None, None)
        config = self.config_test.copy()
        runner = DiagnosticRunner(args, config)
        self.assertEqual(config['envvars']['RGB'], '/HOME/src/rgb')
        self.assertEqual(os.environ['RGB'], '/HOME/src/rgb')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_runner.util.check_required_dirs')
    def test_set_mdtf_env_vars_config_cmdline(self, mock_check_required_dirs):
        # override config file with command line arguments
        args = TestDiagnosticRunner.MockArgs('/X', 'Y')
        self.assertEqual(args.C, '/X')
        self.assertEqual(args.E, 'Y')
        config = self.config_test.copy()
        runner = DiagnosticRunner(args, config)
        self.assertEqual(config['envvars']['C'], '/X')
        self.assertEqual(os.environ['C'], '/X')
        self.assertEqual(config['envvars']['E'], 'Y')
        self.assertEqual(os.environ['E'], 'Y')  

    # ---------------------------------------------------  

    def test_backup_config_file(self):
        pass

    def test_make_tar_file(self):
        pass

if __name__ == '__main__':
    unittest.main()