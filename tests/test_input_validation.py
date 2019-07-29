import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import var_code.util as util

class TestInputValidation(unittest.TestCase):
    def test_check_required_envvar_found(self):
        # exit function normally if all variables found
        with mock.patch.dict('os.environ', {'A':'B', 'C':'D'}):
            try:
                util.check_required_envvar('A', 'C')
            except SystemExit:
                self.fail()

    def test_check_required_envvar_not_found(self):
        # try to exit() if any variables not found
        with mock.patch.dict('os.environ', {'A':'B', 'C':'D'}):
            self.assertRaises(SystemExit, util.check_required_envvar, 'A', 'E')


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

    def test_check_for_varlist_files(self):
        # TBD
        pass

    def test_check_pod_driver(self):
        # TBD
        pass

if __name__ == '__main__':
    unittest.main()