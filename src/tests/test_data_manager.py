import os
import unittest
import unittest.mock as mock  # define mock os.environ so we don't mess up real env vars
import src.util as util
from src import translation, data_sources, pod_setup


# from src.data_manager import DataManager
# from src.tests.shared_test_utils import setUp_ConfigManager, tearDown_ConfigManager

@unittest.skip("TODO: Test needs to be rewritten following v3 beta 3 release")
# @mock.patch.multiple(DataManager, __abstractmethods__=set())
class TestDataManagerSetup(unittest.TestCase):
    # pylint: disable=abstract-class-instantiated
    default_case = {
        'CASENAME': 'A', 'model': 'B', 'FIRSTYR': 1900, 'LASTYR': 2100,
        'pod_list': ['C']
    }
    default_pod_CF = {
        'settings': {},
        'varlist': [{'var_name': 'pr_var', 'freq': 'mon'}]
    }
    dummy_paths = {
        'CODE_ROOT': 'A', 'OBS_DATA_ROOT': 'B', 'MODEL_DATA_ROOT': 'C',
        'WORKING_DIR': 'D', 'OUTPUT_DIR': 'E'
    }
    dummy_var_translate = {
        'convention_name': 'not_CF',
        'var_names': {'pr_var': 'PRECT', 'prc_var': 'PRECC'}
    }

    @mock.patch('src.configs.util.read_json', return_value=dummy_var_translate)
    def setUp(self, mock_read_json):

        _ = translation.VariableTranslator(unittest=True)

    def tearDown(self):
        tearDown_ConfigManager()

    # ---------------------------------------------------

    def test_setup_model_paths(self):
        pass

    # expect failure because variable name env vars set by POD now
    @unittest.expectedFailure
    def test_set_model_env_vars(self):
        # set env vars for model
        case = data_sources.data_source[case_dict.convention.upper() + "DataSource"](case_name,
                                                                                                 case_dict,
                                                                                                 model_paths,
                                                                                                 parent=None)
        case.convention = 'not_CF'
        dummy = {'envvars': {}}
        case._set_model_env_vars(dummy)
        self.assertEqual(os.environ['pr_var'], 'PRECT')
        self.assertEqual(os.environ['prc_var'], 'PRECC')

    @mock.patch('src.util.check_dir')
    def test_set_model_env_vars_no_model(self, mock_check_dirs):
        # exit if can't find model
        case = DataManager(self.default_case)
        case.convention = 'nonexistent'
        self.assertRaises(AssertionError, case.setup)

    def test_setup_html(self):
        pass

    def test_setup_pod_cf_cf(self):
        case = data_sources.data_source[case_dict.convention.upper() + "DataSource"](case_name,
                                                                                                 case_dict,
                                                                                                 model_paths,
                                                                                                 parent=None)
        pod = Diagnostic('C')
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'pr_var')

    def test_setup_pod_cf_custom(self):
        case = DataManager(self.default_case)
        case.convention = 'not_CF'
        pod = Diagnostic('C')
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'PRECT')


@unittest.skip("TODO: Test needs to be rewritten following v3 beta 3 release")
# @mock.patch.multiple(DataManager, __abstractmethods__=set())
class TestDataManagerSetupNonCFPod(unittest.TestCase):
    # pylint: disable=abstract-class-instantiated

    default_case = {
        'CASENAME': 'A', 'model': 'B', 'FIRSTYR': 1900, 'LASTYR': 2100,
        'pod_list': ['C']
    }
    default_pod_not_CF = {
        'settings': {'variable_convention': 'not_CF'},
        'varlist': [{'var_name': 'PRECT', 'freq': 'mon'}]
    }
    dummy_paths = {
        'CODE_ROOT': 'A', 'OBS_DATA_ROOT': 'B', 'MODEL_DATA_ROOT': 'C',
        'WORKING_DIR': 'D', 'OUTPUT_DIR': 'E'
    }
    dummy_var_translate = {
        'convention_name': 'not_CF',
        'var_names': {'pr_var': 'PRECT', 'prc_var': 'PRECC'}
    }

    @mock.patch('src.configs.util.read_json', return_value=dummy_var_translate)
    def setUp(self, mock_read_json):
        setUp_ConfigManager(
            config=self.default_case,
            paths=self.dummy_paths,
            pods={'C': self.default_pod_not_CF}
        )
        _ = configs.VariableTranslator(unittest=True)

    def tearDown(self):
        tearDown_ConfigManager()

    def test_setup_pod_custom_cf(self):
        case = DataManager(self.default_case)
        pod = Diagnostic('C')
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'pr_var')

    def test_setup_pod_custom_custom(self):
        case = DataManager(self.default_case)
        case.convention = 'not_CF'
        pod = Diagnostic('C')
        case.pods = [pod]
        case._setup_pod(pod)
        self.assertEqual(pod.varlist[0].CF_name, 'pr_var')
        self.assertEqual(pod.varlist[0].name_in_model, 'PRECT')

    @unittest.skip("")
    @mock.patch('src.diagnostic.util.read_json', return_value={
        'settings': {'conda_env': 'B'}, 'varlist': []})
    def test_parse_pod_settings_conda_env(self, mock_read_json):
        # fill in conda environment
        pod = Diagnostic('A')
        self.assertEqual(pod.conda_env, '_MDTF-diagnostics-B')


@unittest.skip("TODO: Test needs to be rewritten following v3 beta 3 release")
class TestDataManagerFetchData(unittest.TestCase):
    @mock.patch('src.util.read_json',
                return_value={
                    'convention_name': 'not_CF',
                    'var_names': {'pr_var': 'PRECT', 'prc_var': 'PRECC'}
                })
    def setUp(self, mock_read_json):
        # set up translation dictionary without calls to filesystem
        _ = util.VariableTranslator(unittest=True)
        _ = util.PathManager(unittest=True)

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing,
        # otherwise the second, third, .. tests will use the instance created
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator(unittest=True)
        temp._reset()
        temp = util.PathManager(unittest=True)
        temp._reset()

    # ---------------------------------------------------
    default_case = {
        'CASENAME': 'A', 'model': 'B', 'FIRSTYR': 1900, 'LASTYR': 2100,
        'pod_list': []
    }


if __name__ == '__main__':
    unittest.main()
