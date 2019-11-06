import os
import unittest
from collections import namedtuple
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.data_manager import DataManager
from src.shared_diagnostic import Diagnostic
from subprocess import CalledProcessError

class TestBasicClasses(unittest.TestCase):
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

    def test_multimap_inverse(self):
        # test inverse map
        temp = util.MultiMap({'a':1, 'b':2})
        temp_inv = temp.inverse()
        self.assertIn(1, temp_inv)
        self.assertEqual(temp_inv[2], set(['b']))

    def test_multimap_setitem(self):
        # test key addition and handling of duplicate values
        temp = util.MultiMap({'a':1, 'b':2})
        temp['c'] = 1           
        temp_inv = temp.inverse()
        self.assertIn(1, temp_inv)
        self.assertItemsEqual(temp_inv[1], set(['a','c']))
        temp['b'] = 3
        temp_inv = temp.inverse()
        self.assertNotIn(2, temp_inv)

    def test_multimap_delitem(self):
        # test item deletion
        temp = util.MultiMap({'a':1, 'b':2})
        del temp['b']
        temp_inv = temp.inverse()
        self.assertNotIn(2, temp_inv)

    def test_multimap_add(self):
        temp = util.MultiMap({'a':1, 'b':2, 'c':1})
        temp['a'].add(3)
        temp_inv = temp.inverse()
        self.assertIn(3, temp_inv)
        self.assertItemsEqual(temp_inv[3], set(['a']))
        temp['a'].add(2)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertItemsEqual(temp_inv[2], set(['a','b']))

    def test_multimap_add_new(self):
        temp = util.MultiMap({'a':1, 'b':2, 'c':1})
        temp['x'].add(2)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertItemsEqual(temp_inv[2], set(['b','x']))

    def test_multimap_remove(self):
        temp = util.MultiMap({'a':1, 'b':2, 'c':1})
        temp['c'].add(2)
        temp['c'].remove(1)
        temp_inv = temp.inverse()
        self.assertIn(2, temp_inv)
        self.assertItemsEqual(temp_inv[2], set(['b','c']))
        self.assertIn(1, temp_inv)
        self.assertItemsEqual(temp_inv[1], set(['a']))

    def test_namespace_basic(self):
        test = util.Namespace(name='A', B='C')
        self.assertEqual(test.name, 'A')
        self.assertEqual(test.B, 'C')
        with self.assertRaises(AttributeError):
            _ = test.D
        test.B = 'D'
        self.assertEqual(test.B, 'D')

    def test_namespace_dict_ops(self):
        test = util.Namespace(name='A', B='C')
        self.assertIn('B', test)
        self.assertNotIn('D', test)

    def test_namespace_tofrom_dict(self):
        test = util.Namespace(name='A', B='C')
        test2 = test.toDict()
        self.assertEqual(test2['name'], 'A')
        self.assertEqual(test2['B'], 'C')
        test3 = util.Namespace.fromDict(test2)
        self.assertEqual(test3.name, 'A')
        self.assertEqual(test3.B, 'C')

    def test_namespace_copy(self):
        test = util.Namespace(name='A', B='C')
        test2 = test.copy()
        self.assertEqual(test2.name, 'A')
        self.assertEqual(test2.B, 'C')
        test2.B = 'D'
        self.assertEqual(test.B, 'C')
        self.assertEqual(test2.B, 'D')

    def test_namespace_hash(self):
        test = util.Namespace(name='A', B='C')
        test2 = test
        test3 = test.copy()
        test4 = test.copy()
        test4.name = 'not_the_same'
        test5 = util.Namespace(name='A', B='C')
        self.assertEqual(test, test2)
        self.assertEqual(test, test3)
        self.assertNotEqual(test, test4)
        self.assertEqual(test, test5)
        set_test = set([test, test2, test3, test4, test5])
        self.assertEqual(len(set_test), 2)
        self.assertIn(test, set_test)
        self.assertIn(test4, set_test)

class TestDataSet(unittest.TestCase):
    pass

class TestUtil(unittest.TestCase):

    def test_read_json(self):
        pass

    def test_write_json(self):
        pass

    def test_get_available_programs(self):
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

    os_environ_check_required_envvar = {'A':'B', 'C':'D'}

    @mock.patch.dict('os.environ', os_environ_check_required_envvar)
    def test_check_required_envvar_found(self):
        # exit function normally if all variables found
        try:
            util.check_required_envvar('A', 'C')
        except SystemExit:
            self.fail()

    # @mock.patch.dict('os.environ', os_environ_check_required_envvar)
    # def test_check_required_envvar_not_found(self):
    #     # try to exit() if any variables not found
    #     print '\nXXXX', os.environ['A'],  os.environ['E'], '\n'
    #     self.assertRaises(SystemExit, util.check_required_envvar, 'A', 'E')

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
        self.assertRaises(OSError, util.check_required_dirs, ['DIR1XXX'], [])
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

class TestVariableTranslator(unittest.TestCase):
    @mock.patch('src.util.read_json', 
        return_value = {
            'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
            })
    def setUp(self, mock_read_json):
        # set up translation dictionary without calls to filesystem
        _ = util.VariableTranslator(unittest_flag = True)

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator(unittest_flag=True)
        temp._reset()

    def test_variabletranslator(self):
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.toCF('not_CF', 'PRECT'), 'pr_var')
        self.assertEqual(temp.fromCF('not_CF', 'pr_var'), 'PRECT')

    def test_variabletranslator_cf(self):
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.toCF('CF', 'pr_var'), 'pr_var')
        self.assertEqual(temp.fromCF('CF', 'pr_var'), 'pr_var')

    def test_variabletranslator_no_key(self):
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertRaises(AssertionError, temp.toCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.toCF, 'not_CF', 'nonexistent_var')
        self.assertRaises(AssertionError, temp.fromCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.fromCF, 'not_CF', 'nonexistent_var')

class TestVariableTranslatorReadFiles(unittest.TestCase):
    @mock.patch('src.util.read_json', 
        return_value = {'convention_name':'A','var_names':{'B':'D'}})
    def test_read_model_varnames(self, mock_read_json):
        # normal operation - convert string to list
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.fromCF('A','B'), 'D')
        temp._reset()

    @mock.patch('src.util.read_json', 
        return_value = {'convention_name':['A','C'],'var_names':{'B':'D'}})
    def test_read_model_varnames_multiple(self, mock_read_json):
        # create multiple entries when multiple models specified
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.fromCF('A','B'), 'D')
        self.assertEqual(temp.fromCF('C','B'), 'D')
        temp._reset()

class TestPathManager(unittest.TestCase):
    # pylint: disable=maybe-no-member
    @mock.patch('src.util.read_json', 
        return_value = {
            'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
            })
    def setUp(self, mock_read_json):
        # set up translation dictionary without calls to filesystem
        _ = util.VariableTranslator(unittest_flag = True)

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator(unittest_flag=True)
        temp._reset()
        temp = util.PathManager()
        temp._reset()

    # ------------------------------------------------

    def test_pathmgr_global(self):
        d = {
            'CODE_ROOT':'A', 'OBS_DATA_ROOT':'B', 'MODEL_DATA_ROOT':'C',
            'WORKING_DIR':'D', 'OUTPUT_DIR':'E'
        }
        paths = util.PathManager(d)
        self.assertEqual(paths.CODE_ROOT, 'A')
        self.assertEqual(paths.OUTPUT_DIR, 'E')

    def test_pathmgr_global_asserterror(self):

        d = {
            'OBS_DATA_ROOT':'B', 'MODEL_DATA_ROOT':'C',
            'WORKING_DIR':'D', 'OUTPUT_DIR':'E'
        }
        self.assertRaises(AssertionError, util.PathManager, d)
        # initialize successfully so that tearDown doesn't break
        _ = util.PathManager(unittest_flag = True) 

    def test_pathmgr_global_testmode(self):
        paths = util.PathManager(unittest_flag = True)
        self.assertEqual(paths.CODE_ROOT, 'TEST_CODE_ROOT')
        self.assertEqual(paths.OUTPUT_DIR, 'TEST_OUTPUT_DIR')

    default_os_environ = {'DIAG_HOME':'/HOME'}
    default_case = {
        'CASENAME': 'A', 'model': 'B', 'FIRSTYR': 1900, 'LASTYR': 2100,
        'pod_list': []
    }
    default_pod_CF = {
        'settings':{}, 
        'varlist':[{'var_name': 'pr_var', 'freq':'mon'}]
        }

    @mock.patch.dict('os.environ', default_os_environ)
    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('src.data_manager.atexit.register')
    def test_pathmgr_model(self, mock_register):
        paths = util.PathManager(unittest_flag = True)
        case = DataManager(self.default_case)
        d = paths.modelPaths(case)
        self.assertEqual(d['MODEL_DATA_DIR'], 'TEST_MODEL_DATA_ROOT/A')
        self.assertEqual(d['MODEL_WK_DIR'], 'TEST_WORKING_DIR/MDTF_A_1900_2100')

    @mock.patch.dict('os.environ', default_os_environ)
    @mock.patch('src.shared_diagnostic.util.read_json', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_pathmgr_pod(self, mock_exists, mock_read_json):
        paths = util.PathManager(unittest_flag = True)
        pod = Diagnostic('A')
        pod.MODEL_WK_DIR = 'B'
        d = paths.podPaths(pod)
        self.assertEqual(d['POD_CODE_DIR'], 'TEST_CODE_ROOT/diagnostics/A')
        self.assertEqual(d['POD_OBS_DATA'], 'TEST_OBS_DATA_ROOT/A')
        self.assertEqual(d['POD_WK_DIR'], 'B/A')

    @mock.patch.dict('os.environ', default_os_environ)
    @mock.patch('src.shared_diagnostic.util.read_json', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_pathmgr_pod_nomodel(self, mock_exists, mock_read_json):
        paths = util.PathManager(unittest_flag = True)
        pod = Diagnostic('A')
        d = paths.podPaths(pod)
        self.assertEqual(d['POD_CODE_DIR'], 'TEST_CODE_ROOT/diagnostics/A')
        self.assertNotIn('POD_WK_DIR', d)

# ---------------------------------------------------
class TestSubprocessInteraction(unittest.TestCase):
    def test_run_shell_commands_stdout1(self):
        input = 'echo "foo"'
        out = util.run_shell_commands(input)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], 'foo')

    def test_run_shell_commands_stdout2(self):
        input = ['echo "foo"', 'echo "bar"']
        out = util.run_shell_commands(input)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], 'foo')
        self.assertEqual(out[1], 'bar')
        
    def test_run_shell_commands_exitcode(self):
        input = ['echo "foo"', 'false']
        with self.assertRaises(Exception):
            # I couldn't get this to catch CalledProcessError specifically,
            # maybe because it takes args?
            util.run_shell_commands(input)

    def test_run_shell_commands_envvars(self):
        input = ['echo $FOO', 'export FOO="baz"', 'echo $FOO']
        out = util.run_shell_commands(input, env={'FOO':'bar'})
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], 'bar')
        self.assertEqual(out[1], 'baz')

    def test_poll_command_shell_true(self):
        rc = util.poll_command('echo "foo"', shell=True)
        self.assertEqual(rc, 0)

    def test_poll_command_shell_false(self):
        rc = util.poll_command(['echo', 'foo'], shell=False)
        self.assertEqual(rc, 0)
    
    def test_poll_command_error(self):
        rc = util.poll_command(['false'], shell=False)
        self.assertEqual(rc, 1)

    def test_run_command_stdout1(self):
        out = util.run_command(['echo', '"foo"'])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], '"foo"')

    def test_run_command_exitcode(self):
        input = ['exit', '1']
        with self.assertRaises(Exception):
            # I couldn't get this to catch CalledProcessError specifically,
            # maybe because it takes args?
            util.run_command(input)

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()
