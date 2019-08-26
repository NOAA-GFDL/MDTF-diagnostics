import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util


class TestUtil(unittest.TestCase):

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator()
        temp._reset()

    # ---------------------------------------------------

    def test_read_yaml(self):
        pass

    def test_write_yaml(self):
        pass

    def test_get_available_programs(self):
        pass

    def test_makefilepath(self):
        pass

    # ---------------------------------------------------
    
    @mock.patch.dict('os.environ', {'TEST_OVERWRITE': 'A'})
    def test_setenv_overwrite(self):
        test_d = {'TEST_OVERWRITE': 'A'}
        util.setenv('TEST_OVERWRITE','B', test_d, overwrite = False)
        self.assertEqual(test_d['TEST_OVERWRITE'], 'A')
        self.assertEqual(os.environ['TEST_OVERWRITE'], 'A')

    @mock.patch.dict('os.environ', {})
    def test_setenv_str(self):
        test_d = {}
        util.setenv('TEST_STR','B', test_d)
        self.assertEqual(test_d['TEST_STR'], 'B')
        self.assertEqual(os.environ['TEST_STR'], 'B')

    @mock.patch.dict('os.environ', {})
    def test_setenv_int(self):
        test_d = {}        
        util.setenv('TEST_INT',2019, test_d)
        self.assertEqual(test_d['TEST_INT'], 2019)
        self.assertEqual(os.environ['TEST_INT'], '2019')

    @mock.patch.dict('os.environ', {})
    def test_setenv_bool(self):
        test_d = {}
        util.setenv('TEST_TRUE',True, test_d)
        self.assertEqual(test_d['TEST_TRUE'], True)
        self.assertEqual(os.environ['TEST_TRUE'], '1')

        util.setenv('TEST_FALSE',False, test_d)
        self.assertEqual(test_d['TEST_FALSE'], False)
        self.assertEqual(os.environ['TEST_FALSE'], '0')

    # ---------------------------------------------------

    def test_singleton(self):
        # Can only be instantiated once
        class Temp1(util.Singleton):
            def __init__(self):
                self.foo = 0
        temp1 = Temp1()
        temp2 = Temp1()
        temp1.foo = 5
        self.assertEqual(temp2.foo, 5)

    def test_singleton_reset(self):
        # Verify cleanup works
        class Temp2(util.Singleton):
            def __init__(self):
                self.foo = 0
        temp1 = Temp2()
        temp1.foo = 5
        temp1._reset()
        temp2 = Temp2()
        self.assertEqual(temp2.foo, 0)

    def test_bidict_inverse(self):
        # test inverse map
        temp = util.BiDict({'a':1, 'b':2})
        self.assertIn(1, temp.inverse)
        self.assertEqual(temp.inverse[2],['b'])

    def test_bidict_setitem(self):
        # test key addition and handling of duplicate values
        temp = util.BiDict({'a':1, 'b':2})
        temp['c'] = 1           
        self.assertIn(1, temp.inverse)
        self.assertItemsEqual(temp.inverse[1],['a','c'])
        temp['b'] = 3
        self.assertIn(2, temp.inverse)
        self.assertEqual(temp.inverse[2],[])

    def test_bidict_delitem(self):
        # test item deletion
        temp = util.BiDict({'a':1, 'b':2})
        del temp['b']
        self.assertNotIn(2, temp.inverse)

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('glob.glob', return_value = [''])
    @mock.patch('src.util.read_yaml', 
        return_value = {'convention_name':'A','var_names':{'B':'D'}})
    def test_read_model_varnames(self, mock_read_yaml, mock_glob):
        # normal operation - convert string to list
        temp = util.VariableTranslator()
        self.assertEqual(temp.fromCF('A','B'), 'D')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('glob.glob', return_value = [''])
    @mock.patch('src.util.read_yaml', 
        return_value = {'convention_name':['A','C'],'var_names':{'B':'D'}})
    def test_read_model_varnames_multiple(self, mock_read_yaml, mock_glob):
        # create multiple entries when multiple models specified
        temp = util.VariableTranslator()
        self.assertEqual(temp.fromCF('A','B'), 'D')
        self.assertEqual(temp.fromCF('C','B'), 'D')

    def test_variabletranslator(self):
        # bypass __init__ method:
        temp = util.VariableTranslator.__new__(util.VariableTranslator) 
        temp.field_dict = {}
        temp.field_dict['A'] = util.BiDict({'pr_var': 'PRECT'})
        self.assertEqual(temp.toCF('A', 'PRECT'), 'pr_var')
        self.assertEqual(temp.fromCF('A', 'pr_var'), 'PRECT')

    def test_variabletranslator_cf(self):
        # bypass __init__ method:
        temp = util.VariableTranslator.__new__(util.VariableTranslator) 
        temp.field_dict = {}
        temp.field_dict['A'] = util.BiDict({'pr_var': 'PRECT'})
        self.assertEqual(temp.toCF('CF', 'pr_var'), 'pr_var')
        self.assertEqual(temp.fromCF('CF', 'pr_var'), 'pr_var')

    def test_variabletranslator_no_key(self):
        # bypass __init__ method:
        temp = util.VariableTranslator.__new__(util.VariableTranslator) 
        temp.field_dict = {}
        temp.field_dict['A'] = util.BiDict({'pr_var': 'PRECT'})
        self.assertRaises(AssertionError, temp.toCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.toCF, 'A', 'nonexistent_var')
        self.assertRaises(AssertionError, temp.fromCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.fromCF, 'A', 'nonexistent_var')

    # ---------------------------------------------------

    os_environ_check_required_envvar = {'A':'B', 'C':'D'}

    @mock.patch.dict('os.environ', os_environ_check_required_envvar)
    def test_check_required_envvar_found(self):
        # exit function normally if all variables found
        try:
            util.check_required_envvar('A', 'C')
        except SystemExit:
            self.fail()

    @mock.patch.dict('os.environ', os_environ_check_required_envvar)
    def test_check_required_envvar_not_found(self):
        # try to exit() if any variables not found
        self.assertRaises(SystemExit, util.check_required_envvar, 'A', 'E')

    # ---------------------------------------------------

    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('os.makedirs')
    def test_check_required_dirs_found(self, mock_makedirs, mock_exists):
        # exit function normally if all directories found 
        try:
            util.check_required_dirs(['DIR1'], [])
            util.check_required_dirs([], ['DIR2'])
        except SystemExit:
            self.fail()
        mock_makedirs.assert_not_called()
 
    @mock.patch('os.path.exists', return_value = False)
    @mock.patch('os.makedirs')
    def test_check_required_dirs_not_found(self, mock_makedirs, mock_exists):
        # try to exit() if any directories not found
        self.assertRaises(SystemExit, util.check_required_dirs, ['DIR1XXX'], [])
        mock_makedirs.assert_not_called()

    @mock.patch('os.path.exists', return_value = False)
    @mock.patch('os.makedirs')
    def test_check_required_dirs_not_found_created(self, mock_makedirs, mock_exists):      
        # don't exit() and call os.makedirs if in create_if_nec          
        try:
            util.check_required_dirs([], ['DIR2'])
        except SystemExit:
            self.fail()
        mock_makedirs.assert_called_once_with('DIR2')

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()