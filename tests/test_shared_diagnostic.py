import os
import sys
import unittest
import mock # define mock os.environ so we don't mess up real env vars
from src.shared_diagnostic import Diagnostic

# TODO: refactor Diagnostic's __init__: pain to have to mock it out

class TestDiagnostic(unittest.TestCase):

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {'settings':{},'varlist':[]})
    def test_read_pod_settings_file(self, mock_safe_load, mock_open, mock_exists):
        # normal operation
        pod = Diagnostic('A')
        pod_set = pod.config
        self.assertEqual(pod_set['settings']['pod_name'], 'A')
        self.assertEqual(pod_set['settings']['pod_dir'], '/HOME/diagnostics/A')
        self.assertEqual(pod_set['settings']['conda_env'], '_MDTF-diagnostics')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('src.shared_diagnostic.util.read_yaml', return_value = {
        'settings':{'conda_env':'B'},'varlist':[]})
    def test_read_pod_settings_file_conda_env(self, mock_safe_load, mock_open, mock_exists):
        # fill in conda environment
        pod = Diagnostic('A')
        pod_set = pod.config
        self.assertEqual(pod_set['settings']['conda_env'], '_MDTF-diagnostics-B')

    # ---------------------------------------------------  

    os_environ_parse_pod_varlist = {'pr_var':'PRECT'}

    @mock.patch.dict('os.environ', os_environ_parse_pod_varlist)
    def test_parse_pod_varlist(self):
        with mock.patch.object(Diagnostic, '__init__', lambda x, y: None):
            # normal operation
            varlist = [{
                'var_name': 'pr_var', 'freq':'mon', 'requirement':'required'
            }]
            pod = Diagnostic('A')
            pod._parse_pod_varlist(varlist)
            self.assertEqual(varlist[0]['name_in_model'], 'PRECT')
            self.assertEqual(varlist[0]['required'], True)

    @mock.patch.dict('os.environ', os_environ_parse_pod_varlist)
    def test_parse_pod_varlist_defaults(self):
        with mock.patch.object(Diagnostic, '__init__', lambda x, y: None):
            # fill in defaults
            varlist = [{
                'var_name': 'pr_var', 'freq':'mon', 'alternates':'foo'
            }]
            pod = Diagnostic('A')
            pod._parse_pod_varlist(varlist)
            self.assertEqual(varlist[0]['required'], False)
            self.assertEqual(varlist[0]['alternates'], ['foo'])

    @mock.patch.dict('os.environ', os_environ_parse_pod_varlist)
    def test_parse_pod_varlist_freq(self):
        with mock.patch.object(Diagnostic, '__init__', lambda x, y: None):
            # AssertionError on bad freq
            varlist = [{
                'var_name': 'pr_var', 'freq':'not_a_frequency'
            }]
            pod = Diagnostic('A')
            self.assertRaises(AssertionError, pod._parse_pod_varlist, varlist)

    # ---------------------------------------------------

    os_environ_set_pod_env_vars = {
        'DIAG_HOME':'/HOME',
        'OBS_ROOT_DIR':'/A',
        'variab_dir':'/B'
        }
    @mock.patch.dict('os.environ', os_environ_set_pod_env_vars)
    @mock.patch('os.path.exists', return_value = True)
    def test_set_pod_env_vars_paths(self, mock_exists):
        with mock.patch.object(Diagnostic, '__init__', lambda x, y: None):
            # check definition of pod paths
            pod = Diagnostic('A')
            env = pod._set_pod_env_vars({'pod_name':'C'}, {})
            self.assertEqual(os.environ['POD_HOME'], '/HOME/diagnostics/C')
            self.assertEqual(env['POD_HOME'], '/HOME/diagnostics/C')
            self.assertEqual(os.environ['OBS_DATA'], '/A/C')
            self.assertEqual(env['OBS_DATA'], '/A/C')
            self.assertEqual(os.environ['WK_DIR'], '/B/C')
            self.assertEqual(env['WK_DIR'], '/B/C')

    @mock.patch.dict('os.environ', os_environ_set_pod_env_vars)
    @mock.patch('os.path.exists', return_value = True)
    def test_set_pod_env_vars_vars(self, mock_exists):
        with mock.patch.object(Diagnostic, '__init__', lambda x, y: None):
            # check definition of additional env vars
            pod = Diagnostic('A')
            env = pod._set_pod_env_vars({'pod_name':'C', 'pod_env_vars':{'D':'E'}}, {})
            self.assertEqual(os.environ['D'], 'E')
            self.assertEqual(env['D'], 'E')

    # ---------------------------------------------------      

    @mock.patch.dict('os.environ', {'variab_dir':'A'})
    @mock.patch('os.path.exists', return_value = False)
    @mock.patch('os.makedirs')
    def test_setup_pod_directories_mkdir(self, mock_makedirs, mock_exists): 
        with mock.patch.object(Diagnostic, '__init__', lambda x, y: None): 
            # create output dirs if not present    
            pod = Diagnostic('A')   
            pod._setup_pod_directories('B')
            mock_makedirs.assert_has_calls([
                mock.call('A/B/'+ s) for s in [
                    '','model','model/PS','model/netCDF','obs','obs/PS','obs/netCDF'
                ]
            ], any_order = True)

    @mock.patch.dict('os.environ', {'variab_dir':'A'})
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('os.makedirs')
    def test_setup_pod_directories_no_mkdir(self, mock_makedirs, mock_exists):
        with mock.patch.object(Diagnostic, '__init__', lambda x, y: None):  
            # don't create output dirs if already present       
            pod = Diagnostic('A')    
            pod._setup_pod_directories('B')
            mock_makedirs.assert_not_called()  

    # ---------------------------------------------------

    @mock.patch.dict('os.environ', {
        'DIAG_HOME':'/HOME',
        'variab_dir':'/B',
        'CASENAME':'C'
        })
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('shutil.copy2')
    @mock.patch('os.system')
    @mock.patch('os.remove')
    def test_make_pod_html(self, mock_remove, mock_system, mock_copy2, mock_exists):
        with mock.patch.object(Diagnostic, '__init__', lambda x, y: None):  
            pod = Diagnostic('A')   
            pod._make_pod_html('A','D')
            mock_copy2.assert_has_calls([
                mock.call('/HOME/diagnostics/A/A.html', '/B/A'),
                mock.call('/B/A/tmp.html', '/B/A/A.html')
            ])
            mock_system.assert_has_calls([
                mock.call('cat /B/A/A.html | sed -e s/casename/C/g > /B/A/tmp.html')
            ])

    # ---------------------------------------------------

    @mock.patch.dict('os.environ', {
        'variab_dir':'A', 'convert_flags':'-C', 'convert_output_fmt':'png'})
    @mock.patch('glob.glob', return_value = ['A/model/PS/B.ps'])
    @mock.patch('os.system')
    def test_convert_pod_figures(self, mock_system, mock_glob):
        with mock.patch.object(Diagnostic, '__init__', lambda x, y: None):  
            # assert we munged filenames correctly
            pod = Diagnostic('A')   
            pod._convert_pod_figures('B')
            mock_system.assert_has_calls([
                mock.call('convert -C A/model/PS/B.ps A/model/B.png')
            ])

    # ---------------------------------------------------

    def test_cleanup_pod_files(self):
        pass

if __name__ == '__main__':
    unittest.main()