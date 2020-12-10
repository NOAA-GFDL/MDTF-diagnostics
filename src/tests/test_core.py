import os
import unittest
from collections import namedtuple
import itertools
import unittest.mock as mock # define mock os.environ so we don't mess up real env vars
import src.configs as configs
from src.data_manager import DataManager
from src.diagnostic import Diagnostic
from subprocess import CalledProcessError
from src.tests.shared_test_utils import setUp_ConfigManager, tearDown_ConfigManager


class TestVariableTranslator(unittest.TestCase):
    def setUp(self):
        # set up translation dictionary without calls to filesystem
        setUp_ConfigManager()

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        tearDown_ConfigManager()

    @mock.patch('src.configs.util.read_json', return_value = {
        'convention_name':'not_CF',
        'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
    })
    def test_variabletranslator(self, mock_read_json):
        temp = configs.VariableTranslator(unittest = True)
        self.assertEqual(temp.toCF('not_CF', 'PRECT'), 'pr_var')
        self.assertEqual(temp.fromCF('not_CF', 'pr_var'), 'PRECT')

    @mock.patch('src.configs.util.read_json', return_value = {
        'convention_name':'not_CF',
        'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
    })
    def test_variabletranslator_cf(self, mock_read_json):
        temp = configs.VariableTranslator(unittest = True)
        self.assertEqual(temp.toCF('CF', 'pr_var'), 'pr_var')
        self.assertEqual(temp.fromCF('CF', 'pr_var'), 'pr_var')

    @mock.patch('src.configs.util.read_json', return_value = {
        'convention_name':'not_CF',
        'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
    })
    def test_variabletranslator_no_key(self, mock_read_json):
        temp = configs.VariableTranslator(unittest = True)
        self.assertRaises(AssertionError, temp.toCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.toCF, 'not_CF', 'nonexistent_var')
        self.assertRaises(AssertionError, temp.fromCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.fromCF, 'not_CF', 'nonexistent_var')

class TestVariableTranslatorReadFiles(unittest.TestCase):
    def setUp(self):
        # set up translation dictionary without calls to filesystem
        setUp_ConfigManager()

    def tearDown(self):
        tearDown_ConfigManager()

    @mock.patch('src.configs.util.read_json', return_value = {
        'convention_name':'A','var_names':{'B':'D'}
    })
    def test_read_model_varnames(self, mock_read_json):
        # normal operation - convert string to list
        temp = configs.VariableTranslator(unittest = True)
        self.assertEqual(temp.fromCF('A','B'), 'D')
        temp._reset()

    @mock.patch('src.configs.util.read_json', return_value = {
        'convention_name':['A','C'],'var_names':{'B':'D'}
    })
    def test_read_model_varnames_multiple(self, mock_read_json):
        # create multiple entries when multiple models specified
        temp = configs.VariableTranslator(unittest = True)
        self.assertEqual(temp.fromCF('A','B'), 'D')
        self.assertEqual(temp.fromCF('C','B'), 'D')
        temp._reset()

class TestPathManager(unittest.TestCase):
    # pylint: disable=maybe-no-member
    def setUp(self):
        # set up translation dictionary without calls to filesystem
        setUp_ConfigManager(paths = {
            'CODE_ROOT':'A', 'OBS_DATA_ROOT':'B', 'MODEL_DATA_ROOT':'C',
            'WORKING_DIR':'D', 'OUTPUT_DIR':'E'
        })

    def tearDown(self):
        tearDown_ConfigManager()

    # ------------------------------------------------

    @unittest.skip("")
    def test_pathmgr_global(self):
        config = configs.ConfigManager()
        self.assertEqual(config.paths.CODE_ROOT, 'A')
        self.assertEqual(config.paths.OUTPUT_DIR, 'E')

    @unittest.skip("")
    def test_pathmgr_global_asserterror(self):
        d = {
            'OBS_DATA_ROOT':'B', 'MODEL_DATA_ROOT':'C',
            'WORKING_DIR':'D', 'OUTPUT_DIR':'E'
        }
        config = configs.ConfigManager()
        self.assertRaises(AssertionError, config.paths.parse, d, list(d.keys()))
        # initialize successfully so that tear_down doesn't break
        #_ = configs.PathManager(unittest = True) 

    def test_pathmgr_global_testmode(self):
        config = configs.ConfigManager()
        self.assertEqual(config.paths.CODE_ROOT, 'TEST_CODE_ROOT')
        self.assertEqual(config.paths.OUTPUT_DIR, 'TEST_OUTPUT_DIR')


@mock.patch.multiple(DataManager, __abstractmethods__=set())
class TestPathManagerPodCase(unittest.TestCase):
    def setUp(self):
        # set up translation dictionary without calls to filesystem
        setUp_ConfigManager(
            config=self.case_dict, 
            paths={
                'CODE_ROOT':'A', 'OBS_DATA_ROOT':'B', 'MODEL_DATA_ROOT':'C',
                'WORKING_DIR':'D', 'OUTPUT_DIR':'E'
            },
            pods={ 'AA':{
                'settings':{}, 
                'varlist':[{'var_name': 'pr_var', 'freq':'mon'}]
                }
            })

    case_dict = {
        'CASENAME': 'A', 'model': 'B', 'FIRSTYR': 1900, 'LASTYR': 2100,
        'pod_list': ['AA']
    }

    def tearDown(self):
        tearDown_ConfigManager()

    def test_pathmgr_model(self):
        config = configs.ConfigManager()
        case = DataManager(self.case_dict)
        d = config.paths.model_paths(case)
        self.assertEqual(d['MODEL_DATA_DIR'], 'TEST_MODEL_DATA_ROOT/A')
        self.assertEqual(d['MODEL_WK_DIR'], 'TEST_WORKING_DIR/MDTF_A_1900_2100')

    def test_pathmgr_pod(self):
        config = configs.ConfigManager()
        case = DataManager(self.case_dict)
        pod = Diagnostic('AA')
        d = config.paths.pod_paths(pod, case)
        self.assertEqual(d['POD_CODE_DIR'], 'TEST_CODE_ROOT/diagnostics/AA')
        self.assertEqual(d['POD_OBS_DATA'], 'TEST_OBS_DATA_ROOT/AA')
        self.assertEqual(d['POD_WK_DIR'], 'TEST_WORKING_DIR/MDTF_A_1900_2100/AA')



# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()
