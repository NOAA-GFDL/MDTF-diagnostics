import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.shared_diagnostic import Diagnostic
from src.data_manager import DataManager

class TestDataManagerSetup(unittest.TestCase):
    
    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('glob.glob', return_value = [''])
    @mock.patch('src.util.read_yaml', 
        return_value = {'model_name':'B',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}})
    def setUp(self, mock_read_yaml, mock_glob):
        # set up translation dictionary without calls to filesystem
        temp = util.VariableTranslator()

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator()
        temp._reset()

    # ---------------------------------------------------

    def test_setup_model_paths(self):
        pass

    @mock.patch.dict('os.environ', {})
    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    def test_set_model_env_vars(self):
        # set env vars for model
        case = DataManager({'CASENAME': 'A', 'model': 'B'})
        case._set_model_env_vars()
        self.assertEqual(os.environ['pr_var'], 'PRECT')
        self.assertEqual(os.environ['prc_var'], 'PRECC')

    @mock.patch.dict('os.environ', {})
    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    def test_set_model_env_vars_no_model(self):
        # exit if can't find model
        case = DataManager({'CASENAME': 'A', 'model': 'nonexistent'})
        self.assertRaises(AssertionError, case._set_model_env_vars)

    def test_setup_html(self):
        pass

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{}, 'varlist':[{'var_name': 'pr_var','freq':'mon', 'required': True}]
        })
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pods_cf(self, mock_exists, mock_read_yaml):
        case = DataManager({'CASENAME': 'A', 'model': 'CF'})
        pod = Diagnostic('C')
        case.pods = [pod]
        case._setup_pods()
        self.assertEqual(pod.model, 'CF')
        self.assertEqual(pod.varlist[0]['name_in_model'], 'pr_var')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch.multiple(DataManager, __abstractmethods__=set())
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{}, 'varlist':[{'var_name': 'pr_var','freq':'mon', 'required': True}]
        })
    @mock.patch('os.path.exists', return_value = True)
    def test_setup_pods_custom(self, mock_exists, mock_read_yaml):
        case = DataManager({'CASENAME': 'A', 'model': 'B'})
        pod = Diagnostic('C')
        case.pods = [pod]
        case._setup_pods()
        self.assertEqual(pod.model, 'B')
        self.assertEqual(pod.varlist[0]['name_in_model'], 'PRECT')

    # @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    # @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
    #     'settings':{'conda_env':'B'},'varlist':[]})
    # def test_parse_pod_settings_conda_env(self, mock_read_yaml):
    #     # fill in conda environment 
    #     pod = Diagnostic('A')
    #     self.assertEqual(pod.conda_env, '_MDTF-diagnostics-B')


    # self.assertEqual(pod.varlist[0]['name_in_model'], 'PRECT')

if __name__ == '__main__':
    unittest.main()