import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util


class TestUtil(unittest.TestCase):

    def test_read_mdtf_config_file(self):
        pass

    def test_get_available_programs(self):
        pass

    def test_makefilepath(self):
        pass

# ---------------------------------------------------
    
    def test_setenv_overwrite(self):
        with mock.patch.dict('os.environ', {'TEST_OVERWRITE': 'A'}):
            test_d = {'TEST_OVERWRITE': 'A'}
            util.setenv('TEST_OVERWRITE','B', test_d, overwrite = False)
            self.assertEqual(test_d['TEST_OVERWRITE'], 'A')
            self.assertEqual(os.environ['TEST_OVERWRITE'], 'A')

    def test_setenv_str(self):
        with mock.patch.dict('os.environ', {}):
            test_d = {}
            util.setenv('TEST_STR','B', test_d)
            self.assertEqual(test_d['TEST_STR'], 'B')
            self.assertEqual(os.environ['TEST_STR'], 'B')

    def test_setenv_int(self):
        with mock.patch.dict('os.environ', {}):
            test_d = {}        
            util.setenv('TEST_INT',2019, test_d)
            self.assertEqual(test_d['TEST_INT'], 2019)
            self.assertEqual(os.environ['TEST_INT'], '2019')

    def test_setenv_bool(self):
        with mock.patch.dict('os.environ', {}):
            test_d = {}
            util.setenv('TEST_TRUE',True, test_d)
            self.assertEqual(test_d['TEST_TRUE'], True)
            self.assertEqual(os.environ['TEST_TRUE'], '1')

            util.setenv('TEST_FALSE',False, test_d)
            self.assertEqual(test_d['TEST_FALSE'], False)
            self.assertEqual(os.environ['TEST_FALSE'], '0')

# ---------------------------------------------------

    def test_translate_varname(self):
        with mock.patch.dict('os.environ', {'pr_var': 'PRECT'}):
            self.assertEqual(util.translate_varname('pr_var'), 'PRECT')
            self.assertEqual(util.translate_varname('nonexistent_var'), 'nonexistent_var')

# ---------------------------------------------------

    os_environ_check_required_envvar = {'A':'B', 'C':'D'}

    def test_check_required_envvar_found(self):
        # exit function normally if all variables found
        with mock.patch.dict('os.environ', self.os_environ_check_required_envvar):
            try:
                util.check_required_envvar('A', 'C')
            except SystemExit:
                self.fail()

    def test_check_required_envvar_not_found(self):
        # try to exit() if any variables not found
        with mock.patch.dict('os.environ', self.os_environ_check_required_envvar):
            self.assertRaises(SystemExit, util.check_required_envvar, 'A', 'E')

# ---------------------------------------------------

    def test_check_required_dirs_found(self):
        # exit function normally if all directories found
        with mock.patch('os.path.exists', return_value = True):
            with mock.patch('os.makedirs') as mock_makedirs:    
                try:
                    util.check_required_dirs(['DIR1'], [])
                    util.check_required_dirs([], ['DIR2'])
                except SystemExit:
                    self.fail()
                mock_makedirs.assert_not_called()
 
    def test_check_required_dirs_not_found(self):
        # try to exit() if any directories not found
        with mock.patch('os.path.exists', return_value = False):
            with mock.patch('os.makedirs') as mock_makedirs:    
                self.assertRaises(SystemExit, util.check_required_dirs, ['DIR1XXX'], [])
                mock_makedirs.assert_not_called()

    def test_check_required_dirs_not_found_created(self):      
        # don't exit() and call os.makedirs if in create_if_nec
        with mock.patch('os.path.exists', return_value = False):
            with mock.patch('os.makedirs') as mock_makedirs:              
                try:
                    util.check_required_dirs([], ['DIR2'])
                except SystemExit:
                    self.fail()
                mock_makedirs.assert_called_once_with('DIR2')

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()