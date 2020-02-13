import os
import unittest
from collections import namedtuple
import itertools
import mock # define mock os.environ so we don't mess up real env vars
import src.util_mdtf as util
from src.data_manager import DataManager
from src.shared_diagnostic import Diagnostic
from subprocess import CalledProcessError

class TestUtil(unittest.TestCase):
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
        self.assertRaises(OSError, util.check_required_dirs, ['DIR1XXX'], [])
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

    @mock.patch('os.path.exists', return_value=False)
    def test_bump_version_noexist(self, mock_exists):
        for f in [
            'AAA', 'AAA.v1', 'D/C/B/AAA', 'D/C/B/AAAA/', 'D/C/B/AAA.v23', 
            'D/C/B/AAAA.v23/', 'A.foo', 'A.v23.foo', 'A.v23.bar.v45.foo',
            'D/C/A.foo', 'D/C/A.v23.foo', 'D/C/A.v23.bar.v45.foo'
        ]:
            f2, _ = util.bump_version(f)
            self.assertEqual(f, f2)

    @mock.patch('os.path.exists', return_value=False)
    def test_bump_version_getver(self, mock_exists):
        for f in [
            'AAA.v42', 'D/C/B/AAA.v42', 'D/C.v7/B/AAAA.v42/', 'A.v42.foo', 
            'A.v23.bar.v42.foo', 'D/C/A.v42.foo', 'D/C/A.v23.bar.v42.foo'
        ]:
            _, ver = util.bump_version(f)
            self.assertEqual(ver, 42)

    @mock.patch('os.path.exists', return_value=False)
    def test_bump_version_delver(self, mock_exists):
        for f in [
            ('AAA','AAA'), ('AAA.v1','AAA'), ('D/C/B/AA','D/C/B/AA'), 
            ('D/C.v1/B/AA/','D/C.v1/B/AA/'), ('D/C/B/AA.v23','D/C/B/AA'),
            ('D/C3/B.v8/AA.v23/','D/C3/B.v8/AA/'), ('A.foo','A.foo'), 
            ('A.v23.foo','A.foo'), ('A.v23.bar.v45.foo','A.v23.bar.foo'),
            ('D/C/A.foo','D/C/A.foo'), ('D/C.v1/A234.v3.foo','D/C.v1/A234.foo'),
            ('D/C/A.v23.bar.v45.foo','D/C/A.v23.bar.foo')
        ]:
            f1, ver = util.bump_version(f[0], new_v=0)
            self.assertEqual(f1, f[1])
            self.assertEqual(ver, 0)

    @mock.patch('os.path.exists', return_value=False)
    def test_bump_version_setver(self, mock_exists):
        for f in [
            ('AAA','AAA.v42'), ('AAA.v1','AAA.v42'), ('D/C/B/AA','D/C/B/AA.v42'), 
            ('D/C.v1/B/AA/','D/C.v1/B/AA.v42/'), ('D/C/B/AA.v23','D/C/B/AA.v42'),
            ('D/C3/B.v8/AA.v23/','D/C3/B.v8/AA.v42/'), ('A.foo','A.v42.foo'), 
            ('A.v23.foo','A.v42.foo'), ('A.v23.bar.v45.foo','A.v23.bar.v42.foo'),
            ('D/C/A.foo','D/C/A.v42.foo'), ('D/C.v1/A.v23.foo','D/C.v1/A.v42.foo'),
            ('D/C/A.v23.bar.v45.foo','D/C/A.v23.bar.v42.foo')
        ]:
            f1, ver = util.bump_version(f[0], new_v=42)
            self.assertEqual(f1, f[1])
            self.assertEqual(ver, 42)

    @mock.patch('os.path.exists', side_effect=itertools.cycle([True,False]))
    def test_bump_version_dirs(self, mock_exists):
        for f in [
            ('AAA','AAA.v1',1), ('AAA.v1','AAA.v2',2), ('D/C/B/AA','D/C/B/AA.v1',1), 
            ('D/C.v1/B/AA/','D/C.v1/B/AA.v1/',1), ('D/C/B/AA.v23','D/C/B/AA.v24',24),
            ('D/C3/B.v8/AA.v9/','D/C3/B.v8/AA.v10/',10)
        ]:
            f1, ver = util.bump_version(f[0])
            self.assertEqual(f1, f[1])
            self.assertEqual(ver, f[2])

    @mock.patch('os.path.exists', side_effect=itertools.cycle([True,False]))
    def test_bump_version_files(self, mock_exists):
        for f in [
            ('A.foo','A.v1.foo',1), ('A.v23.foo','A.v24.foo',24), 
            ('A.v23.bar.v45.foo','A.v23.bar.v46.foo',46),
            ('D/C/A.foo','D/C/A.v1.foo',1), 
            ('D/C.v1/A.v99.foo','D/C.v1/A.v100.foo', 100),
            ('D/C/A.v23.bar.v78.foo','D/C/A.v23.bar.v79.foo', 79)
        ]:
            f1, ver = util.bump_version(f[0])
            self.assertEqual(f1, f[1])
            self.assertEqual(ver, f[2])


class TestVariableTranslator(unittest.TestCase):
    @mock.patch('src.util.read_json', 
        return_value = {
            'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
            })
    def setUp(self, mock_read_json):
        # set up translation dictionary without calls to filesystem
        _ = util.VariableTranslator(unittest_flag = True)

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator(unittest_flag=True)
        temp._reset()

    def test_variabletranslator(self):
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.toCF('not_CF', 'PRECT'), 'pr_var')
        self.assertEqual(temp.fromCF('not_CF', 'pr_var'), 'PRECT')

    def test_variabletranslator_cf(self):
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.toCF('CF', 'pr_var'), 'pr_var')
        self.assertEqual(temp.fromCF('CF', 'pr_var'), 'pr_var')

    def test_variabletranslator_no_key(self):
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertRaises(AssertionError, temp.toCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.toCF, 'not_CF', 'nonexistent_var')
        self.assertRaises(AssertionError, temp.fromCF, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.fromCF, 'not_CF', 'nonexistent_var')

class TestVariableTranslatorReadFiles(unittest.TestCase):
    @mock.patch('src.util.read_json', 
        return_value = {'convention_name':'A','var_names':{'B':'D'}})
    def test_read_model_varnames(self, mock_read_json):
        # normal operation - convert string to list
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.fromCF('A','B'), 'D')
        temp._reset()

    @mock.patch('src.util.read_json', 
        return_value = {'convention_name':['A','C'],'var_names':{'B':'D'}})
    def test_read_model_varnames_multiple(self, mock_read_json):
        # create multiple entries when multiple models specified
        temp = util.VariableTranslator(unittest_flag = True)
        self.assertEqual(temp.fromCF('A','B'), 'D')
        self.assertEqual(temp.fromCF('C','B'), 'D')
        temp._reset()

class TestPathManager(unittest.TestCase):
    # pylint: disable=maybe-no-member
    @mock.patch('src.util.read_json', 
        return_value = {
            'convention_name':'not_CF',
            'var_names':{'pr_var': 'PRECT', 'prc_var':'PRECC'}
            })
    def setUp(self, mock_read_json):
        # set up translation dictionary without calls to filesystem
        _ = util.VariableTranslator(unittest_flag = True)

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = util.VariableTranslator(unittest_flag=True)
        temp._reset()
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
        _ = util.PathManager(unittest_flag = True) 

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
    @mock.patch('src.data_manager.atexit.register')
    def test_pathmgr_model(self, mock_register):
        paths = util.PathManager(unittest_flag = True)
        case = DataManager(self.default_case)
        d = paths.modelPaths(case)
        self.assertEqual(d['MODEL_DATA_DIR'], 'TEST_MODEL_DATA_ROOT/A')
        self.assertEqual(d['MODEL_WK_DIR'], 'TEST_WORKING_DIR/MDTF_A_1900_2100')

    @mock.patch.dict('os.environ', default_os_environ)
    @mock.patch('src.shared_diagnostic.util.read_json', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_pathmgr_pod(self, mock_exists, mock_read_json):
        paths = util.PathManager(unittest_flag = True)
        pod = Diagnostic('A')
        pod.MODEL_WK_DIR = 'B'
        d = paths.podPaths(pod)
        self.assertEqual(d['POD_CODE_DIR'], 'TEST_CODE_ROOT/diagnostics/A')
        self.assertEqual(d['POD_OBS_DATA'], 'TEST_OBS_DATA_ROOT/A')
        self.assertEqual(d['POD_WK_DIR'], 'B/A')

    @mock.patch.dict('os.environ', default_os_environ)
    @mock.patch('src.shared_diagnostic.util.read_json', return_value = default_pod_CF)
    @mock.patch('os.path.exists', return_value = True)
    def test_pathmgr_pod_nomodel(self, mock_exists, mock_read_json):
        paths = util.PathManager(unittest_flag = True)
        pod = Diagnostic('A')
        d = paths.podPaths(pod)
        self.assertEqual(d['POD_CODE_DIR'], 'TEST_CODE_ROOT/diagnostics/A')
        self.assertNotIn('POD_WK_DIR', d)

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()
