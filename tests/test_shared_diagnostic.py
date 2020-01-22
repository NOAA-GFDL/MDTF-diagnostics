import os
import sys
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.data_manager import DataSet
from src.datelabel import DateFrequency
from src.shared_diagnostic import Diagnostic, PodRequirementFailure

class TestDiagnosticInit(unittest.TestCase):
    # pylint: disable=maybe-no-member
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
        temp = util.PathManager(unittest_flag = True)
        temp._reset()
        temp = util.VariableTranslator(unittest_flag = True)
        temp._reset()

    # ---------------------------------------------------  

    @mock.patch('src.shared_diagnostic.util.read_json', 
        return_value = {'settings':{'required_programs':'B'},'varlist':[]})
    def test_parse_pod_settings(self, mock_read_json):
        # normal operation
        pod = Diagnostic('A')
        self.assertEqual(pod.name, 'A')
        self.assertEqual(pod.POD_CODE_DIR, 'TEST_CODE_ROOT/diagnostics/A')
        self.assertEqual(pod.required_programs, ['B'])

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{},'varlist':[{
                'var_name': 'pr_var', 'freq':'mon', 'requirement':'required'
            }]
        })
    def test_parse_pod_varlist(self, mock_read_json):
        # normal operation
        pod = Diagnostic('A')
        self.assertEqual(pod.varlist[0]['required'], True)

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{},'varlist':[{
                'var_name': 'pr_var', 'freq':'mon', 'alternates':'foo'
            }]
        })
    def test_parse_pod_varlist_defaults(self, mock_read_json):
        # fill in defaults
        test_ds = DataSet({
                'name':'foo', 'freq':'mon', 
                'CF_name':'foo', 'required': True,
                'original_name':'pr_var', 'alternates':[]
                })
        pod = Diagnostic('A')
        self.assertEqual(pod.varlist[0]['required'], True)
        self.assertEqual(len(pod.varlist[0]['alternates']), 1)
        # self.assertDictEqual(pod.varlist[0]['alternates'][0].__dict__, test_ds.__dict__)

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{},'varlist':[{
                'var_name': 'pr_var', 'freq':'not_a_frequency'
            }]
        })
    def test_parse_pod_varlist_freq(self, mock_read_json):
        self.assertRaises(AssertionError, Diagnostic, 'A')

@mock.patch('src.shared_diagnostic.util.read_json', return_value = {
    'settings':{}, 'varlist':[]
    })
class TestDiagnosticSetUp(unittest.TestCase):
    # pylint: disable=maybe-no-member
    @mock.patch('src.util.read_json', 
        return_value = {'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}})
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

    @mock.patch('os.path.exists', return_value = True)
    def test_set_pod_env_vars_paths(self, mock_exists, mock_read_json):
        # check definition of pod paths
        pod = Diagnostic('C')
        pod.POD_WK_DIR = 'A'
        pod._set_pod_env_vars()
        self.assertEqual(os.environ['POD_HOME'], 'TEST_CODE_ROOT/diagnostics/C')
        self.assertEqual(pod.pod_env_vars['POD_HOME'], 'TEST_CODE_ROOT/diagnostics/C')
        self.assertEqual(os.environ['OBS_DATA'], 'TEST_OBS_DATA_ROOT/C')
        self.assertEqual(pod.pod_env_vars['OBS_DATA'], 'TEST_OBS_DATA_ROOT/C')
        self.assertEqual(os.environ['WK_DIR'], 'A')
        self.assertEqual(pod.pod_env_vars['WK_DIR'], 'A')  

    @mock.patch('src.util.check_required_dirs')
    @mock.patch('os.path.exists', return_value = False)
    @mock.patch('os.makedirs')
    def test_setup_pod_directories_mkdir(self, mock_makedirs, mock_exists, \
        mock_check_required_dirs, mock_read_json): 
        # create output dirs if not present    
        pod = Diagnostic('B')
        pod.POD_WK_DIR = 'A/B'
        pod._setup_pod_directories()
        mock_makedirs.assert_has_calls([
            mock.call('A/B/'+ s) for s in [
                '','model','model/PS','model/netCDF','obs','obs/PS','obs/netCDF'
            ]
        ], any_order = True)

    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('os.makedirs')
    def test_setup_pod_directories_no_mkdir(self, mock_makedirs, mock_exists, \
        mock_read_json):
        # don't create output dirs if already present       
        pod = Diagnostic('B')
        pod.POD_WK_DIR = 'A'
        pod._setup_pod_directories()
        mock_makedirs.assert_not_called()     

    @mock.patch('os.path.exists', return_value = True) 
    def test_check_pod_driver_no_driver_1(self, mock_exists, mock_read_json):
        # fill in driver from pod name
        programs = util.get_available_programs()
        pod = Diagnostic('A')  
        pod._check_pod_driver()
        ext = os.path.splitext(pod.driver)[1][1:]
        self.assertTrue(ext in programs)
        self.assertEqual(pod.program, programs[ext])

    @mock.patch('os.path.exists', return_value = False)
    def test_check_pod_driver_no_driver_2(self, mock_exists, mock_read_json):
        # assertion fails if no driver found
        pod = Diagnostic('A')  
        self.assertRaises(PodRequirementFailure, pod._check_pod_driver)

class TestDiagnosticCheckVarlist(unittest.TestCase):
    # pylint: disable=maybe-no-member
    @mock.patch('src.util.read_json', 
        return_value = {'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}})
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

    def _populate_pod__local_data(self, pod):
        # reproduce logic in DataManager._setup_pod rather than invoke it here
        paths = util.PathManager(unittest_flag = True)
        translate = util.VariableTranslator(unittest_flag = True)
        case_name = 'A'

        ds_list = []
        for var in pod.varlist:
            ds_list.append(DataSet.from_pod_varlist(
                pod.convention, var, {'DateFreqMixin': DateFrequency}))
        pod.varlist = ds_list

        for var in pod.iter_vars_and_alts():
            var.name_in_model = translate.fromCF('not_CF', var.CF_name)
            freq = var.date_freq.format_local()
            var._local_data = os.path.join(
                paths.MODEL_DATA_ROOT, case_name, freq,
                "{}.{}.{}.nc".format(
                    case_name, var.name_in_model, freq)
            )

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{}, 'varlist':[
            {'var_name': 'pr_var', 'freq':'mon'}
        ]})
    @mock.patch('os.path.isfile', return_value = True)
    def test_check_for_varlist_files_found(self, mock_isfile, mock_read_json):
        # case file is found
        pod = Diagnostic('A') 
        self._populate_pod__local_data(pod)
        (found, missing) = pod._check_for_varlist_files(pod.varlist)
        self.assertEqual(found, ['TEST_MODEL_DATA_ROOT/A/mon/A.PRECT.mon.nc'])
        self.assertEqual(missing, [])

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{}, 'varlist':[
            {'var_name': 'pr_var', 'freq':'mon', 'required': True}
        ]})        
    @mock.patch('os.path.isfile', return_value = False)
    def test_check_for_varlist_files_not_found(self, mock_isfile, mock_read_json):
        # case file is required and not found
        pod = Diagnostic('A') 
        self._populate_pod__local_data(pod)
        (found, missing) = pod._check_for_varlist_files(pod.varlist)
        self.assertEqual(found, [])
        self.assertEqual(missing, ['TEST_MODEL_DATA_ROOT/A/mon/A.PRECT.mon.nc'])

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{}, 'varlist':[
            {'var_name': 'pr_var', 'freq':'mon', 'required': False}
        ]})   
    @mock.patch('os.path.isfile', side_effect = [False, True])
    def test_check_for_varlist_files_optional(self, mock_isfile, mock_read_json):
        # case file is optional and not found
        pod = Diagnostic('A') 
        self._populate_pod__local_data(pod)
        (found, missing) = pod._check_for_varlist_files(pod.varlist)
        self.assertEqual(found, [])
        self.assertEqual(missing, [])

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{}, 'varlist':[
            {'var_name': 'pr_var', 'freq':'mon', 
            'required': True, 'alternates':['prc_var']}
        ]})   
    @mock.patch('os.path.isfile', side_effect = [False, True])
    def test_check_for_varlist_files_alternate(self, mock_isfile, mock_read_json):
        # case alternate variable is specified and found
        pod = Diagnostic('A') 
        self._populate_pod__local_data(pod)
        (found, missing) = pod._check_for_varlist_files(pod.varlist)
        # name_in_model translation now done in DataManager._setup_pod
        self.assertEqual(found, ['TEST_MODEL_DATA_ROOT/A/mon/A.PRECC.mon.nc'])
        self.assertEqual(missing, [])

class TestDiagnosticSetUpCustomSettings(unittest.TestCase):
    # pylint: disable=maybe-no-member
    @mock.patch('src.util.read_json', 
        return_value = {'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}})
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

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{'pod_env_vars':{'D':'E'}}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    def test_set_pod_env_vars_vars(self, mock_exists, mock_read_json):
            # check definition of additional env vars
        pod = Diagnostic('C')
        pod.POD_WK_DIR = 'A'
        pod._set_pod_env_vars()
        self.assertEqual(os.environ['D'], 'E')
        self.assertEqual(pod.pod_env_vars['D'], 'E')

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{'driver':'C.ncl'}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    def test_check_pod_driver_program(self, mock_exists, mock_read_json):
        # fill in absolute path and fill in program from driver's extension
        pod = Diagnostic('A')  
        pod._check_pod_driver()
        self.assertEqual(pod.driver, 'TEST_CODE_ROOT/diagnostics/A/C.ncl')
        self.assertEqual(pod.program, 'ncl')

    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{'driver':'C.foo'}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    def test_check_pod_driver_no_program_1(self, mock_exists, mock_read_json):
        # assertion fail if can't recognize driver's extension
        pod = Diagnostic('A') 
        self.assertRaises(PodRequirementFailure, pod._check_pod_driver)

class TestDiagnosticTearDown(unittest.TestCase):
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
        temp = util.PathManager(unittest_flag = True)
        temp._reset()
        temp = util.VariableTranslator(unittest_flag = True)
        temp._reset()

    # expected to fail because error will be raised about missing TEMP_HTML
    # attribute, which is set when PODs are initialized by data_manager
    @unittest.expectedFailure
    @mock.patch.dict('os.environ', {'CASENAME':'C'})
    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('shutil.copy2')
    @mock.patch('os.system')
    @mock.patch('os.remove')
    @mock.patch('src.util.append_html_template')
    def test_make_pod_html(self, mock_append_html_template, mock_remove, \
        mock_system, mock_copy2, mock_exists, mock_read_json): 
        pod = Diagnostic('A')
        pod.MODEL_WK_DIR = '/B'
        pod.POD_WK_DIR = '/B/A'
        pod._make_pod_html()
        mock_copy2.assert_has_calls([
            mock.call('TEST_CODE_ROOT/diagnostics/A/A.html', '/B/A'),
            mock.call('/B/A/tmp.html', '/B/A/A.html')
        ])
        mock_system.assert_has_calls([
            mock.call('cat /B/A/A.html | sed -e s/casename/C/g > /B/A/tmp.html')
        ])

    # ---------------------------------------------------

    @mock.patch.dict('os.environ', {
        'convert_flags':'-C', 'convert_output_fmt':'png'
        })
    @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
        'settings':{}, 'varlist':[]
        })
    @mock.patch('glob.glob', return_value = ['A/model/PS/B.ps'])
    @mock.patch('os.system')
    def test_convert_pod_figures(self, mock_system, mock_glob, mock_read_json):
        # assert we munged filenames correctly
        pod = Diagnostic('B') 
        pod.POD_WK_DIR = 'A'  
        pod._convert_pod_figures()
        mock_system.assert_has_calls([
            mock.call('convert -C A/model/PS/B.ps A/model/B.png')
        ])

    # ---------------------------------------------------

    def test_cleanup_pod_files(self):
        pass

if __name__ == '__main__':
    unittest.main()