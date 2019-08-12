import os
import sys
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.shared_diagnostic import Diagnostic

class TestDiagnosticInit(unittest.TestCase):

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_diagnostic.util.read_yaml', 
        return_value = {'settings':{},'varlist':[]})
    def test_parse_pod_settings(self, mock_read_yaml):
        # normal operation
        pod = Diagnostic('A')
        self.assertEqual(pod.name, 'A')
        self.assertEqual(pod.dir, '/HOME/diagnostics/A')
        self.assertEqual(pod.conda_env, '_MDTF-diagnostics')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{'conda_env':'B'},'varlist':[]})
    def test_parse_pod_settings_conda_env(self, mock_read_yaml):
        # fill in conda environment
        pod = Diagnostic('A')
        self.assertEqual(pod.conda_env, '_MDTF-diagnostics-B')

    # ---------------------------------------------------  

    os_environ_parse_pod_varlist = {'DIAG_HOME':'/HOME', 'pr_var':'PRECT'}

    @mock.patch.dict('os.environ', os_environ_parse_pod_varlist)
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{},'varlist':[{
                'var_name': 'pr_var', 'freq':'mon', 'requirement':'required'
            }]
        })
    def test_parse_pod_varlist(self, mock_read_yaml):
        # normal operation
        pod = Diagnostic('A')
        self.assertEqual(pod.varlist[0]['name_in_model'], 'PRECT')
        self.assertEqual(pod.varlist[0]['required'], True)

    @mock.patch.dict('os.environ', os_environ_parse_pod_varlist)
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{},'varlist':[{
                'var_name': 'pr_var', 'freq':'mon', 'alternates':'foo'
            }]
        })
    def test_parse_pod_varlist_defaults(self, mock_read_yaml):
        # fill in defaults
        pod = Diagnostic('A')
        self.assertEqual(pod.varlist[0]['required'], False)
        self.assertEqual(pod.varlist[0]['alternates'], ['foo'])

    @mock.patch.dict('os.environ', os_environ_parse_pod_varlist)
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{},'varlist':[{
                'var_name': 'pr_var', 'freq':'not_a_frequency'
            }]
        })
    def test_parse_pod_varlist_freq(self, mock_read_yaml):
        self.assertRaises(AssertionError, Diagnostic, 'A')

class TestDiagnosticSetUp(unittest.TestCase):

    os_environ_set_pod_env_vars = {
        'DIAG_HOME':'/HOME',
        'OBS_ROOT_DIR':'/A',
        'variab_dir':'/B'
        }
    @mock.patch.dict('os.environ', os_environ_set_pod_env_vars)
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    def test_set_pod_env_vars_paths(self, mock_exists, mock_read_yaml):
        # check definition of pod paths
        pod = Diagnostic('C')
        env = pod._set_pod_env_vars()
        self.assertEqual(os.environ['POD_HOME'], '/HOME/diagnostics/C')
        self.assertEqual(env['POD_HOME'], '/HOME/diagnostics/C')
        self.assertEqual(os.environ['OBS_DATA'], '/A/C')
        self.assertEqual(env['OBS_DATA'], '/A/C')
        self.assertEqual(os.environ['WK_DIR'], '/B/C')
        self.assertEqual(env['WK_DIR'], '/B/C')

    @mock.patch.dict('os.environ', os_environ_set_pod_env_vars)
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{'pod_env_vars':{'D':'E'}}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    def test_set_pod_env_vars_vars(self, mock_exists, mock_read_yaml):
            # check definition of additional env vars
        pod = Diagnostic('C')
        env = pod._set_pod_env_vars()
        self.assertEqual(os.environ['D'], 'E')
        self.assertEqual(env['D'], 'E')

    # ---------------------------------------------------      

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME', 'variab_dir':'A'})
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = False)
    @mock.patch('os.makedirs')
    def test_setup_pod_directories_mkdir(self, mock_makedirs, mock_exists, mock_read_yaml): 
        # create output dirs if not present    
        pod = Diagnostic('B')
        pod._setup_pod_directories()
        mock_makedirs.assert_has_calls([
            mock.call('A/B/'+ s) for s in [
                '','model','model/PS','model/netCDF','obs','obs/PS','obs/netCDF'
            ]
        ], any_order = True)

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME', 'variab_dir':'A'})
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('os.makedirs')
    def test_setup_pod_directories_no_mkdir(self, mock_makedirs, mock_exists, mock_read_yaml):
        # don't create output dirs if already present       
        pod = Diagnostic('B')    
        pod._setup_pod_directories()
        mock_makedirs.assert_not_called()  

    # ---------------------------------------------------    

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('distutils.spawn.find_executable', return_value = True) 
    def test_check_pod_driver_no_driver_1(self, mock_find_executable, mock_exists, mock_read_yaml):
        # fill in driver from pod name
        programs = util.get_available_programs()
        pod = Diagnostic('A')  
        pod._check_pod_driver()
        ext = os.path.splitext(pod.driver)[1][1:]
        self.assertTrue(ext in programs)
        self.assertEqual(pod.program, programs[ext])

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = False)
    def test_check_pod_driver_no_driver_2(self, mock_exists, mock_read_yaml):
        # assertion fails if no driver found
        pod = Diagnostic('A')  
        self.assertRaises(AssertionError, pod._check_pod_driver)

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{'driver':'C.ncl'}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('src.shared_diagnostic.find_executable', return_value = True) 
    def test_check_pod_driver_program(self, mock_find_executable, mock_exists, mock_read_yaml):
        # fill in absolute path and fill in program from driver's extension
        pod = Diagnostic('A')  
        pod._check_pod_driver()
        self.assertEqual(pod.driver, '/HOME/diagnostics/A/C.ncl')
        self.assertEqual(pod.program, 'ncl')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{'driver':'C.foo'}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    def test_check_pod_driver_no_program_1(self, mock_exists, mock_read_yaml):
        # assertion fail if can't recognize driver's extension
        pod = Diagnostic('A') 
        self.assertRaises(AssertionError, pod._check_pod_driver)

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{'driver':'C.ncl', 'program':'nonexistent_program'}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    def test_check_pod_driver_no_program_2(self, mock_exists, mock_read_yaml):
        # assertion fail if explicitly specified program not found
        pod = Diagnostic('A') 
        self.assertRaises(AssertionError, pod._check_pod_driver)

    # ---------------------------------------------------

    os_environ_check_for_varlist_files = {
        'DATADIR':'/A', 'CASENAME': 'B', 'prc_var':'PRECC'}

    @mock.patch.dict('os.environ', os_environ_check_for_varlist_files)
    @mock.patch('os.path.isfile', return_value = True)
    def test_check_for_varlist_files_found(self, mock_isfile):
        # case file is found
        test_vars = [{'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon'}]
        pod = Diagnostic.__new__(Diagnostic) # bypass __init__
        f = pod._check_for_varlist_files(test_vars)
        self.assertEqual(f['found_files'], ['/A/mon/B.PRECT.mon.nc'])
        self.assertEqual(f['missing_files'], [])

    @mock.patch.dict('os.environ', os_environ_check_for_varlist_files)
    @mock.patch('os.path.isfile', return_value = False)
    def test_check_for_varlist_files_not_found(self, mock_isfile):
        # case file is required and not found
        test_vars = [{'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon', 'required': True}]
        pod = Diagnostic.__new__(Diagnostic) # bypass __init__
        f = pod._check_for_varlist_files(test_vars)
        self.assertEqual(f['found_files'], [])
        self.assertEqual(f['missing_files'], ['/A/mon/B.PRECT.mon.nc'])

    @mock.patch.dict('os.environ', os_environ_check_for_varlist_files)
    @mock.patch('os.path.isfile', side_effect = [False, True])
    def test_check_for_varlist_files_optional(self, mock_isfile):
        # case file is optional and not found
        test_vars = [{'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon', 'required': False}]
        pod = Diagnostic.__new__(Diagnostic) # bypass __init__ 
        f = pod._check_for_varlist_files(test_vars)
        self.assertEqual(f['found_files'], [])
        self.assertEqual(f['missing_files'], [])

    @mock.patch.dict('os.environ', os_environ_check_for_varlist_files)
    @mock.patch('os.path.isfile', side_effect = [False, True])
    def test_check_for_varlist_files_alternate(self, mock_isfile):
        # case alternate variable is specified and found
        test_vars = [{'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon', 'required': True, 'alternates':['prc_var']}]
        pod = Diagnostic.__new__(Diagnostic) # bypass __init__ 
        f = pod._check_for_varlist_files(test_vars)
        self.assertEqual(f['found_files'], ['/A/mon/B.PRECC.mon.nc'])
        self.assertEqual(f['missing_files'], [])

class TestDiagnosticTearDown(unittest.TestCase):

    @mock.patch.dict('os.environ', {
        'DIAG_HOME':'/HOME',
        'variab_dir':'/B',
        'CASENAME':'C'
        })
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{}, 'varlist':[]
        })
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('shutil.copy2')
    @mock.patch('os.system')
    @mock.patch('os.remove')
    def test_make_pod_html(self, mock_remove, mock_system, mock_copy2, mock_exists, mock_read_yaml): 
        pod = Diagnostic('A')   
        pod._make_pod_html()
        mock_copy2.assert_has_calls([
            mock.call('/HOME/diagnostics/A/A.html', '/B/A'),
            mock.call('/B/A/tmp.html', '/B/A/A.html')
        ])
        mock_system.assert_has_calls([
            mock.call('cat /B/A/A.html | sed -e s/casename/C/g > /B/A/tmp.html')
        ])

    # ---------------------------------------------------

    @mock.patch.dict('os.environ', {
        'DIAG_HOME':'/HOME', 'variab_dir':'A', 
        'convert_flags':'-C', 'convert_output_fmt':'png'
        })
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{}, 'varlist':[]
        })
    @mock.patch('glob.glob', return_value = ['A/model/PS/B.ps'])
    @mock.patch('os.system')
    def test_convert_pod_figures(self, mock_system, mock_glob, mock_read_yaml):
        # assert we munged filenames correctly
        pod = Diagnostic('B')   
        pod._convert_pod_figures()
        mock_system.assert_has_calls([
            mock.call('convert -C A/model/PS/B.ps A/model/B.png')
        ])

    # ---------------------------------------------------

    def test_cleanup_pod_files(self):
        pass

if __name__ == '__main__':
    unittest.main()