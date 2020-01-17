import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.shared_diagnostic import Diagnostic
from src.data_manager import DataManager

# patch atexit to prevent PathManager initialization errors from triggering
# when tests exit
@mock.patch('src.data_manager.atexit.register')
@mock.patch.multiple(DataManager, __abstractmethods__=set())
class TestDataManagerSetup(unittest.TestCase):
    # pylint: disable=abstract-class-instantiated
    @mock.patch('src.util.read_json', 
        return_value = {
            'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
            })
    def setUp(self, mock_read_json):
        # set up translation dictionary without calls to filesystem
        _ = util.VariableTranslator(unittest_flag = True)
        _ = util.PathManager(unittest_flag = True)

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

    def test_netcdf_inheritance(self, mock_register):
        case = DataManager(self.default_case)
        self.assertRaises(NotImplementedError, case.nc_cat_chunks, [], [])

    def test_setup_model_paths(self, mock_register):
        pass

    def test_set_model_env_vars(self, mock_register):
        # set env vars for model
        case = DataManager(self.default_case)
        case.convention = 'not_CF'
        dummy = {'envvars':{}}
        case._set_model_env_vars(dummy)
        self.assertEqual(os.environ['pr_var'], 'PRECT')
        self.assertEqual(os.environ['prc_var'], 'PRECC')

    def test_set_model_env_vars_no_model(self, mock_register):
        # exit if can't find model
        case = DataManager(self.default_case)
        case.convention = 'nonexistent'
        dummy = {'envvars':{}}
        self.assertRaises(AssertionError, case._set_model_env_vars, dummy)

    def test_setup_html(self, mock_register):
        pass

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pod_cf_cf(self, mock_exists, mock_read_json, mock_register):
        case = DataManager(self.default_case)
        pod = Diagnostic('C')
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'pr_var')

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pod_cf_custom(self, mock_exists, mock_read_json, mock_register):
        case = DataManager(self.default_case)
        case.convention = 'not_CF'
        pod = Diagnostic('C')
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'PRECT')

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = default_pod_not_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pod_custom_cf(self, mock_exists, mock_read_json, mock_register):
        case = DataManager(self.default_case)
        pod = Diagnostic('C')
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'pr_var')

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = default_pod_not_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pod_custom_custom(self, mock_exists, mock_read_json, mock_register):
        case = DataManager(self.default_case)
        case.convention = 'not_CF'
        pod = Diagnostic('C')
        case.pods = [pod]
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'PRECT')

    # @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
    #     'settings':{'conda_env':'B'},'varlist':[]})
    # def test_parse_pod_settings_conda_env(self, mock_read_json):
    #     # fill in conda environment 
    #     pod = Diagnostic('A')
    #     self.assertEqual(pod.conda_env, '_MDTF-diagnostics-B')


class TestDataManagerFetchData(unittest.TestCase):    
    @mock.patch('src.util.read_json', 
        return_value = {
            'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
            })
    def setUp(self, mock_read_json):
        # set up translation dictionary without calls to filesystem
        _ = util.VariableTranslator(unittest_flag = True)
        _ = util.PathManager(unittest_flag = True)

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


if __name__ == '__main__':
    unittest.main()