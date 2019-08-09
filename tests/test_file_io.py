import os
import sys
import collections
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src as util

class TestFileIO(unittest.TestCase):
    os_environ_parse_pod_varlist = {'pr_var':'PRECT'}

    @mock.patch.dict('os.environ', os_environ_parse_pod_varlist)
    def test_parse_pod_varlist(self):
        # normal operation
        varlist = [{
            'var_name': 'pr_var', 'freq':'mon', 'requirement':'required'
        }]
        util.parse_pod_varlist(varlist)
        self.assertEqual(varlist[0]['name_in_model'], 'PRECT')
        self.assertEqual(varlist[0]['required'], True)

    @mock.patch.dict('os.environ', os_environ_parse_pod_varlist)
    def test_parse_pod_varlist_defaults(self):
        # fill in defaults
        varlist = [{
            'var_name': 'pr_var', 'freq':'mon', 'alternates':'foo'
        }]
        util.parse_pod_varlist(varlist)
        self.assertEqual(varlist[0]['required'], False)
        self.assertEqual(varlist[0]['alternates'], ['foo'])

    @mock.patch.dict('os.environ', os_environ_parse_pod_varlist)
    def test_parse_pod_varlist_freq(self):
        # AssertionError on bad freq
        varlist = [{
            'var_name': 'pr_var', 'freq':'not_a_frequency'
        }]
        self.assertRaises(AssertionError, util.parse_pod_varlist, varlist)

# ---------------------------------------------------

    def test_read_mdtf_config_file(self):
        pass

# ---------------------------------------------------        
 
    config_test = {
        'case_list':[{'A':'B'}],
        'paths':{'C':'/D'},
        'settings':{'E':'F'}
    }
    # do this because 1st argument to set_mdtf_env_vars is object containing
    # parsed command-line arguments, accessed via its attributes
    MockArgs = collections.namedtuple('MockArgs', ['C', 'E'])

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    def test_set_mdtf_env_vars_config_paths(self):
        # set paths from config file
        args = TestFileIO.MockArgs(None, None)
        config = self.config_test.copy()
        util.set_mdtf_env_vars(args, config)
        self.assertEqual(config['envvars']['C'], '/D')
        self.assertEqual(os.environ['C'], '/D')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    def test_set_mdtf_env_vars_config_settings(self):
        # set settings from config file
        args = TestFileIO.MockArgs(None, None)
        config = self.config_test.copy()
        util.set_mdtf_env_vars(args, config)
        self.assertEqual(config['envvars']['A'], 'B')
        self.assertEqual(os.environ['A'], 'B')
        self.assertEqual(config['envvars']['E'], 'F')
        self.assertEqual(os.environ['E'], 'F')        

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    def test_set_mdtf_env_vars_config_rgb(self):
        # set path to /RGB from os.environ
        args = TestFileIO.MockArgs(None, None)
        config = self.config_test.copy()
        util.set_mdtf_env_vars(args, config)
        self.assertEqual(config['envvars']['RGB'], '/HOME/src/rgb')
        self.assertEqual(os.environ['RGB'], '/HOME/src/rgb')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    def test_set_mdtf_env_vars_config_cmdline(self):
        # override config file with command line arguments
        args = TestFileIO.MockArgs('/X', 'Y')
        self.assertEqual(args.C, '/X')
        self.assertEqual(args.E, 'Y')
        config = self.config_test.copy()
        util.set_mdtf_env_vars(args, config)
        self.assertEqual(config['envvars']['C'], '/X')
        self.assertEqual(os.environ['C'], '/X')
        self.assertEqual(config['envvars']['E'], 'Y')
        self.assertEqual(os.environ['E'], 'Y')  

# ---------------------------------------------------  

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('yaml.safe_load', return_value = {'settings':{},'varlist':[]})
    def test_read_pod_settings_file(self, mock_safe_load, mock_open, mock_exists):
        # normal operation
        pod_set = util.read_pod_settings_file('A')
        self.assertEqual(pod_set['settings']['pod_name'], 'A')
        self.assertEqual(pod_set['settings']['pod_dir'], '/HOME/diagnostics/A')
        self.assertEqual(pod_set['settings']['conda_env'], '_MDTF-diagnostics')

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('yaml.safe_load', return_value = {
        'settings':{'conda_env':'B'},'varlist':[]})
    def test_read_pod_settings_file_conda_env(self, mock_safe_load, mock_open, mock_exists):
        # fill in conda environment
        pod_set = util.read_pod_settings_file('A')
        self.assertEqual(pod_set['settings']['conda_env'], '_MDTF-diagnostics-B')

# ---------------------------------------------------  

    os_environ_set_pod_env_vars = {
        'DIAG_HOME':'/HOME',
        'OBS_ROOT_DIR':'/A',
        'variab_dir':'/B'
        }
    @mock.patch.dict('os.environ', os_environ_set_pod_env_vars)
    @mock.patch('os.path.exists', return_value = True)
    def test_set_pod_env_vars_paths(self, mock_exists):
        # check definition of pod paths
        env = util.set_pod_env_vars({'pod_name':'C'}, {})
        self.assertEqual(os.environ['POD_HOME'], '/HOME/diagnostics/C')
        self.assertEqual(env['POD_HOME'], '/HOME/diagnostics/C')
        self.assertEqual(os.environ['OBS_DATA'], '/A/C')
        self.assertEqual(env['OBS_DATA'], '/A/C')
        self.assertEqual(os.environ['WK_DIR'], '/B/C')
        self.assertEqual(env['WK_DIR'], '/B/C')

    @mock.patch.dict('os.environ', os_environ_set_pod_env_vars)
    @mock.patch('os.path.exists', return_value = True)
    def test_set_pod_env_vars_vars(self, mock_exists):
        # check definition of additional env vars
        env = util.set_pod_env_vars({'pod_name':'C', 'pod_env_vars':{'D':'E'}}, {})
        self.assertEqual(os.environ['D'], 'E')
        self.assertEqual(env['D'], 'E')

# ---------------------------------------------------  

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('glob.glob', return_value = [''])
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('yaml.safe_load', 
        return_value = {'model_name':'A','var_names':['B']})
    def test_read_model_varnames(self, mock_safe_load, mock_open, mock_glob):
        # normal operation - convert string to list
        self.assertEqual(util.read_model_varnames()['A'], ['B'])

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('glob.glob', return_value = [''])
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('yaml.safe_load', 
        return_value = {'model_name':['A','C'],'var_names':['B']})
    def test_read_model_varnames_multiple(self, mock_safe_load, mock_open, mock_glob):
        # create multiple entries when multiple models specified
        self.assertEqual(util.read_model_varnames()['A'], ['B'])
        self.assertEqual(util.read_model_varnames()['C'], ['B'])

# ---------------------------------------------------

    model_dict_set_model_env_vars = {
        'A':{'B':'C', 'D':5}
    }
    @mock.patch.dict('os.environ', {})
    def test_set_model_env_vars(self):
        # set env vars for model
        util.set_model_env_vars('A', self.model_dict_set_model_env_vars)
        self.assertEqual(os.environ['B'], 'C')
        self.assertEqual(os.environ['D'], '5')

    @mock.patch.dict('os.environ', {})
    def test_set_model_env_vars_no_model(self):
        # exit if can't find model
        self.assertRaises(SystemExit, util.set_model_env_vars, 
            'nonexistent', self.model_dict_set_model_env_vars)

# ---------------------------------------------------

    @mock.patch.dict('os.environ', {'variab_dir':'A'})
    @mock.patch('os.path.exists', return_value = False)
    @mock.patch('os.makedirs')
    def test_setup_pod_directories_mkdir(self, mock_makedirs, mock_exists):  
        # create output dirs if not present       
        util.setup_pod_directories('B')
        mock_makedirs.assert_has_calls([
            mock.call('A/B/'+ s) for s in [
                '','model','model/PS','model/netCDF','obs','obs/PS','obs/netCDF'
            ]
        ], any_order = True)

    @mock.patch.dict('os.environ', {'variab_dir':'A'})
    @mock.patch('os.path.exists', return_value = True)
    @mock.patch('os.makedirs')
    def test_setup_pod_directories_no_mkdir(self, mock_makedirs, mock_exists):  
        # don't create output dirs if already present          
        util.setup_pod_directories('B')
        mock_makedirs.assert_not_called()  

# ---------------------------------------------------

    @mock.patch.dict('os.environ', {
        'variab_dir':'A', 'convert_flags':'-C', 'convert_output_fmt':'png'})
    @mock.patch('glob.glob', return_value = ['A/model/PS/B.ps'])
    @mock.patch('os.system')
    def test_convert_pod_figures(self, mock_system, mock_glob):
        # assert we munged filenames correctly
        util.convert_pod_figures('B')
        mock_system.assert_has_calls([
            mock.call('convert -C A/model/PS/B.ps A/model/B.png')
        ])

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
        util.make_pod_html('A','D')
        mock_copy2.assert_has_calls([
            mock.call('/HOME/diagnostics/A/A.html', '/B/A'),
            mock.call('/B/A/tmp.html', '/B/A/A.html')
        ])
        mock_system.assert_has_calls([
            mock.call('cat /B/A/A.html | sed -e s/casename/C/g > /B/A/tmp.html')
        ])

# ---------------------------------------------------

    def test_cleanup_pod_files(self):
        pass

if __name__ == '__main__':
    unittest.main()