import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import var_code.util as util


class TestUtil(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()