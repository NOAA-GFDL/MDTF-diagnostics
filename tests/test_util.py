import os
import unittest
from collections import namedtuple
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.data_manager import DataManager
from src.shared_diagnostic import Diagnostic


class TestUtil(unittest.TestCase):

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

    @mock.patch('src.util.read_yaml', 
        return_value = {'convention_name':'A','var_names':{'B':'D'}})
    def test_read_model_varnames(self, mock_read_yaml):
        # normal operation - convert string to list
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.fromCF('A','B'), 'D')
        temp._reset()

    @mock.patch('src.util.read_yaml', 
        return_value = {'convention_name':['A','C'],'var_names':{'B':'D'}})
    def test_read_model_varnames_multiple(self, mock_read_yaml):
        # create multiple entries when multiple models specified
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.fromCF('A','B'), 'D')
        self.assertEqual(temp.fromCF('C','B'), 'D')
        temp._reset()

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


class TestVariableTranslator(unittest.TestCase):

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator(unittest_flag=True)
        temp._reset()

    # ---------------------------------------------------
    default_translation = {
        'convention_name':'not_CF',
        'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
        }

    @mock.patch('src.util.read_yaml', return_value = default_translation)
    def test_variabletranslator(self, mock_read_yaml):
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.toCF('not_CF', 'PRECT'), 'pr_var')
        self.assertEqual(temp.fromCF('not_CF', 'pr_var'), 'PRECT')

    @mock.patch('src.util.read_yaml', return_value = default_translation)
    def test_variabletranslator_cf(self, mock_read_yaml):
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.toCF('CF', 'pr_var'), 'pr_var')
        self.assertEqual(temp.fromCF('CF', 'pr_var'), 'pr_var')

    @mock.patch('src.util.read_yaml', return_value = default_translation)
    def test_variabletranslator_no_key(self, mock_read_yaml):
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertRaises(AssertionError, temp.toCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.toCF, 'not_CF', 'nonexistent_var')
        self.assertRaises(AssertionError, temp.fromCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.fromCF, 'not_CF', 'nonexistent_var')


class TestPathManager(unittest.TestCase):

    def tearDown(self):
        # call _reset method deleting clearing PathManager for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
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
        paths = util.PathManager(unittest_flag = True) 

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
    def test_pathmgr_model(self):
        paths = util.PathManager(unittest_flag = True)
        case = DataManager(self.default_case)
        d = paths.modelPaths(case)
        self.assertEqual(d['MODEL_DATA_DIR'], 'TEST_MODEL_DATA_ROOT/A')
        self.assertEqual(d['MODEL_WK_DIR'], 'TEST_WORKING_DIR/MDTF_A_1900_2100')

    @mock.patch.dict('os.environ', default_os_environ)
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_pathmgr_pod(self, mock_exists, mock_read_yaml):
        paths = util.PathManager(unittest_flag = True)
        pod = Diagnostic('A')
        pod.MODEL_WK_DIR = 'B'
        d = paths.podPaths(pod)
        self.assertEqual(d['POD_CODE_DIR'], 'TEST_CODE_ROOT/diagnostics/A')
        self.assertEqual(d['POD_OBS_DATA'], 'TEST_OBS_DATA_ROOT/A')
        self.assertEqual(d['POD_WK_DIR'], 'B/A')

    @mock.patch.dict('os.environ', default_os_environ)
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_pathmgr_pod_nomodel(self, mock_exists, mock_read_yaml):
        paths = util.PathManager(unittest_flag = True)
        pod = Diagnostic('A')
        d = paths.podPaths(pod)
        self.assertEqual(d['POD_CODE_DIR'], 'TEST_CODE_ROOT/diagnostics/A')
        self.assertNotIn('POD_WK_DIR', d)


class TestMDTFArgParsing(unittest.TestCase):

    def setUp(self):
        temp = util.PathManager(unittest_flag = True)
        self.config_test = {
            'case_list':[{'A':'B'}],
            'paths':{'C':'/D'},
            'settings':{'E':'F', 'verbose':0}
        }

    def tearDown(self):
        # call _reset method deleting clearing PathManager for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.PathManager(unittest_flag = True)
        temp._reset()

    def test_parse_mdtf_args_config(self):
        # set paths from config file
        args = {}
        config = self.config_test.copy()
        config = util.parse_mdtf_args(None, args, config)
        self.assertEqual(config['paths']['C'], '/D')
        self.assertEqual(config['settings']['E'], 'F')

    def test_parse_mdtf_args_config_cmdline(self):
        # override config file with command line arguments
        args = {'C':'/X', 'E':'Y'}
        config = self.config_test.copy()
        config = util.parse_mdtf_args(None, args, config)
        self.assertEqual(config['paths']['C'], '/X')
        self.assertEqual(config['settings']['E'], 'Y')

    @mock.patch.dict('os.environ', {})
    @mock.patch('src.util.check_required_dirs')
    def test_set_mdtf_env_vars_config_settings(self, mock_check_required_dirs):
        # set settings from config file
        config = self.config_test.copy()
        util.set_mdtf_env_vars(config)
        self.assertEqual(config['envvars']['E'], 'F')
        self.assertEqual(os.environ['E'], 'F')        

    @mock.patch.dict('os.environ', {})
    @mock.patch('src.util.check_required_dirs')
    def test_sset_mdtf_env_vars_config_rgb(self, mock_check_required_dirs):
        # set path to /RGB from os.environ
        config = self.config_test.copy()
        util.set_mdtf_env_vars(config)
        self.assertEqual(config['envvars']['RGB'], 'TEST_CODE_ROOT/src/rgb')
        self.assertEqual(os.environ['RGB'], 'TEST_CODE_ROOT/src/rgb')

class TestFreppArgParsing(unittest.TestCase):

    def setUp(self):
        self.config_test = {
            'case_list':[{'CASENAME':'B'}],
            'paths':{'MODEL_DATA_ROOT':'/D'},
            'settings':{'E':'F', 'verbose':0, 'make_variab_tar': False}
        }
        self.frepp_stub = """
            set in_data_dir = /foo/bar
            set descriptor = baz.r1i1p1f1
            set yr1 = 1977
            set yr2 = 1981
            set make_variab_tar = 1
        """

    def test_parse_frepp_stub_regex(self):
        frepp_stub = """
            set foo1 = bar
            set foo2 = /complicated/path_name/1-2.3
            set foo3 = "./relative path/with spaces.txt"
            set foo4 = 1
            set foo5 = # comment
            set foo6 = not a #comment
        """
        d = util.parse_frepp_stub(frepp_stub)
        self.assertEqual(d['foo1'], 'bar')
        self.assertEqual(d['foo2'], '/complicated/path_name/1-2.3')
        self.assertEqual(d['foo3'], '"./relative path/with spaces.txt"')
        self.assertEqual(d['foo4'], '1')
        self.assertNotIn('foo5', d)
        self.assertEqual(d['foo6'], 'not a #comment')

    def test_parse_frepp_stub_substitution(self):
        frepp_stub = self.frepp_stub # make a copy to be safe
        d = util.parse_frepp_stub(frepp_stub)
        self.assertNotIn('in_data_dir', d)
        self.assertEqual(d['MODEL_DATA_ROOT'], '/foo/bar')
        self.assertEqual(d['CASENAME'], 'baz.r1i1p1f1')
        self.assertNotIn('yr1', d)
        self.assertEqual(d['FIRSTYR'], 1977)
        self.assertEqual(d['make_variab_tar'], True)

    def test_parse_frepp_stub_mode(self):
        frepp_stub = self.frepp_stub # make a copy to be safe
        d = util.parse_frepp_stub(frepp_stub)
        self.assertEqual(d['frepp_mode'], True)
        frepp_stub = """
            set yr1 = 1981
            set make_variab_tar = 1
        """
        d = util.parse_frepp_stub(frepp_stub)
        self.assertEqual(d['frepp_mode'], False)

    def test_parse_mdtf_args_frepp_overwrite(self):
        # overwrite defaults
        frepp_stub = self.frepp_stub # make a copy to be safe
        d = util.parse_frepp_stub(frepp_stub)
        args = {}
        config = self.config_test.copy()
        config = util.parse_mdtf_args(d, args, config)
        self.assertEqual(config['paths']['MODEL_DATA_ROOT'], '/foo/bar')
        self.assertEqual(config['settings']['make_variab_tar'], True)
        self.assertEqual(config['settings']['E'], 'F')

    def test_parse_mdtf_args_frepp_overwrite_both(self):
        # overwrite defaults and command-line
        frepp_stub = self.frepp_stub # make a copy to be safe
        d = util.parse_frepp_stub(frepp_stub)
        args = {'MODEL_DATA_ROOT':'/X', 'E':'Y'}
        config = self.config_test.copy()
        config = util.parse_mdtf_args(d, args, config)
        self.assertEqual(config['paths']['MODEL_DATA_ROOT'], '/foo/bar')
        self.assertEqual(config['settings']['make_variab_tar'], True)
        self.assertEqual(config['settings']['E'], 'Y')

    def test_parse_mdtf_args_frepp_caselist(self):
        # overwrite defaults and command-line
        frepp_stub = self.frepp_stub # make a copy to be safe
        d = util.parse_frepp_stub(frepp_stub)
        args = {}
        config = self.config_test.copy()
        config = util.parse_mdtf_args(d, args, config)
        self.assertEqual(len(config['case_list']), 1)
        self.assertEqual(config['case_list'][0]['CASENAME'], 'baz.r1i1p1f1')
        self.assertEqual(config['case_list'][0]['model'], 'CMIP')
        self.assertEqual(config['case_list'][0]['variable_convention'], 'CMIP')
        self.assertEqual(config['case_list'][0]['FIRSTYR'], 1977)
        self.assertEqual(config['case_list'][0]['LASTYR'], 1981)

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()