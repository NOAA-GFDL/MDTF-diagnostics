import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.shared_diagnostic import Diagnostic
from src.data_manager import DataManager, DataSet

class TestDataSet(unittest.TestCase):
    def test_dataset_basic(self):
        test = DataSet(name='A', B='C')
        self.assertEqual(test.name, 'A')
        self.assertEqual(test.B, 'C')
        with self.assertRaises(AttributeError):
            temp = test.D
        test.B = 'D'
        self.assertEqual(test.B, 'D')

    def test_dataset_copy(self):
        test = DataSet(name='A', B='C')
        test2 = test.rename_copy(new_name = 'A2')
        self.assertEqual(test.name, 'A')
        self.assertEqual(test2.name, 'A2')
        self.assertEqual(test2.B, 'C')
        test2.B = 'D'
        self.assertEqual(test.B, 'C')
        self.assertEqual(test2.B, 'D')

    def test_dataset_hash(self):
        test = DataSet(name='A', B='C')
        test2 = test
        test3 = test.copy()
        test4 = test.rename_copy(new_name = 'not_the_same')
        test5 = DataSet(name='A', B='C')
        self.assertEqual(test, test2)
        self.assertEqual(test, test3)
        self.assertNotEqual(test, test4)
        self.assertEqual(test, test5)
        set_test = set([test, test2, test3, test4, test5])
        self.assertEqual(len(set_test), 2)
        self.assertIn(test, set_test)
        self.assertIn(test4, set_test)

class TestDataManagerSetup(unittest.TestCase):
    
    @mock.patch('src.util.read_yaml', 
        return_value = {
            'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
            })
    def setUp(self, mock_read_yaml):
        # set up translation dictionary without calls to filesystem
        temp = util.VariableTranslator(unittest_flag = True)
        temp = util.PathManager(unittest_flag = True)

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator(unittest_flag = True)
        temp._reset()
        temp = util.PathManager(unittest_flag = True)
        temp._reset()

    # ---------------------------------------------------

    default_case = {
        'CASENAME': 'A', 'model': 'B', 'FIRSTYR': 1900, 'LASTYR': 2100,
        'pod_list': []
    }
    default_pod_CF = {
        'settings':{}, 
        'varlist':[{'var_name': 'pr_var', 'freq':'mon'}]
        }
    default_pod_not_CF = {
        'settings': {'variable_convention':'not_CF'}, 
        'varlist': [{'var_name': 'PRECT', 'freq':'mon'}]
        }

    def test_setup_model_paths(self):
        pass

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    def test_set_model_env_vars(self):
        # set env vars for model
        case = DataManager(self.default_case)
        case.convention = 'not_CF'
        dummy = {'envvars':{}}
        case._set_model_env_vars(dummy)
        self.assertEqual(os.environ['pr_var'], 'PRECT')
        self.assertEqual(os.environ['prc_var'], 'PRECC')

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    def test_set_model_env_vars_no_model(self):
        # exit if can't find model
        case = DataManager(self.default_case)
        case.convention = 'nonexistent'
        dummy = {'envvars':{}}
        self.assertRaises(AssertionError, case._set_model_env_vars, dummy)

    def test_setup_html(self):
        pass

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pod_cf_cf(self, mock_exists, mock_read_yaml):
        case = DataManager(self.default_case)
        pod = Diagnostic('C')
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'pr_var')

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pod_cf_custom(self, mock_exists, mock_read_yaml):
        case = DataManager(self.default_case)
        case.convention = 'not_CF'
        pod = Diagnostic('C')
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'PRECT')

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = default_pod_not_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pod_custom_cf(self, mock_exists, mock_read_yaml):
        case = DataManager(self.default_case)
        pod = Diagnostic('C')
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'pr_var')

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = default_pod_not_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pod_custom_custom(self, mock_exists, mock_read_yaml):
        case = DataManager(self.default_case)
        case.convention = 'not_CF'
        pod = Diagnostic('C')
        case.pods = [pod]
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'PRECT')

    # @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
    #     'settings':{'conda_env':'B'},'varlist':[]})
    # def test_parse_pod_settings_conda_env(self, mock_read_yaml):
    #     # fill in conda environment 
    #     pod = Diagnostic('A')
    #     self.assertEqual(pod.conda_env, '_MDTF-diagnostics-B')


class TestDataManagerFetchData(unittest.TestCase):    
    @mock.patch('src.util.read_yaml', 
        return_value = {
            'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
            })
    def setUp(self, mock_read_yaml):
        # set up translation dictionary without calls to filesystem
        temp = util.VariableTranslator(unittest_flag = True)
        temp = util.PathManager(unittest_flag = True)

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator(unittest_flag = True)
        temp._reset()
        temp = util.PathManager(unittest_flag = True)
        temp._reset()

    # ---------------------------------------------------
    default_case = {
        'CASENAME': 'A', 'model': 'B', 'FIRSTYR': 1900, 'LASTYR': 2100,
        'pod_list': []
    }

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('os.path.isfile', return_value = True)
    def test_check_for_varlist_files_found(self, mock_isfile):
        # case file is found
        test_var = {'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon'}
        case = DataManager(self.default_case)
        f = case._check_for_varlist_files([DataSet(**test_var)])
        self.assertEqual(f['found_files'], ['TEST_MODEL_DATA_ROOT/A/mon/A.PRECT.mon.nc'])
        self.assertEqual(f['missing_files'], [])

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('os.path.isfile', return_value = False)
    def test_check_for_varlist_files_not_found(self, mock_isfile):
        # case file is required and not found
        test_var = {'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon', 'required': True}
        case = DataManager(self.default_case)
        f = case._check_for_varlist_files([DataSet(**test_var)])
        self.assertEqual(f['found_files'], [])
        self.assertEqual(f['missing_files'], ['TEST_MODEL_DATA_ROOT/A/mon/A.PRECT.mon.nc'])

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('os.path.isfile', side_effect = [False, True])
    def test_check_for_varlist_files_optional(self, mock_isfile):
        # case file is optional and not found
        test_var = {'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon', 'required': False}
        case = DataManager(self.default_case)
        f = case._check_for_varlist_files([DataSet(**test_var)])
        self.assertEqual(f['found_files'], [])
        self.assertEqual(f['missing_files'], [])

    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('os.path.isfile', side_effect = [False, True])
    def test_check_for_varlist_files_alternate(self, mock_isfile):
        # case alternate variable is specified and found
        test_var = {'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon', 'required': True, 'alternates':['PRECC']}
        case = DataManager(self.default_case)
        f = case._check_for_varlist_files([DataSet(**test_var)])
        # name_in_model translation now done in DataManager._setup_pod
        self.assertEqual(f['found_files'], ['TEST_MODEL_DATA_ROOT/A/mon/A.PRECC.mon.nc'])
        self.assertEqual(f['missing_files'], [])


if __name__ == '__main__':
    unittest.main()