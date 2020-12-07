import os
import sys
import unittest
if os.name == 'posix' and sys.version_info[0] < 3:
    try:
        import subprocess32 as subprocess
    except ImportError:
        import subprocess
    else:
        import subprocess
from tests import shared_test_utils as shared
import src.gfdl as gfdl
import src.datelabel as dt
from src.mdtf import MDTFFramework

DOING_TRAVIS = (os.environ.get('TRAVIS', False) == 'true')
DOING_MDTF_DATA_TESTS = ('--data_tests' in sys.argv)
DOING_SETUP = DOING_MDTF_DATA_TESTS and not DOING_TRAVIS
# All this is a workaround because tests are programmatically generated at 
# import time, but the tests are skipped at runtime. We're skipping tests 
# because we're not in an environment where we have the data to set them up,
# so we just throw everything in an if-block to ensure they don't get generated
# if they're going to be skipped later.

# if DOING_SETUP:
#     config = shared.get_configuration('', check_input = True)
#     out_path = config['paths']['OUTPUT_DIR']

#     case_list = shared.get_test_data_configuration()

#     # write temp configuration, one for each POD  
#     temp_config = config.copy()
#     temp_config['pod_list'] = []
#     temp_config['settings']['make_variab_tar'] = False
#     temp_config['settings']['test_mode'] = True

#     pod_configs = shared.configure_pods(case_list, config_to_insert=temp_config)
#     for pod in case_list['pods']:
#         write_json(pod_configs[pod], os.path.join(out_path, pod+'_temp.json'))

@unittest.skipIf('MODULESHOME' not in os.environ,
    "Skipping GFDL tests because not running on a system with environment modules.")
@unittest.skipIf(DOING_TRAVIS,
    "Skipping GFDL tests because running in Travis CI environment")
@unittest.skipUnless(DOING_MDTF_DATA_TESTS,
    "Skipping GFDL tests because not running data-intensive test suite.")
class TestModuleManager(unittest.TestCase):

    test_mod_name = 'latexdiff/1.2.0' # least likely to cause side effects?

    def setUp(self):
        _ = gfdl.ModuleManager()

    def tearDown(self):
        # call _reset method clearing ModuleManager for unit testing, 
        # otherwise the second, third, .. tests will use the instance created 
        # in the first test instead of being properly initialized
        temp = gfdl.ModuleManager()
        temp.revert_state()
        temp._reset()

    def test_module_envvars(self):
        self.assertIn('MODULESHOME', os.environ)
        self.assertIn('MODULE_VERSION', os.environ)
        self.assertIn('LOADEDMODULES', os.environ)
        self.assertEqual(
            '/usr/local/Modules/'+os.environ['MODULE_VERSION'],
            os.environ['MODULESHOME']
        )

    def test_module_avail(self):
        cmd = '{}/bin/modulecmd'.format(os.environ['MODULESHOME'])
        for mod in gfdl._current_module_versions.values():
            # module list writes to stderr, because all module user output does
            list1 = subprocess.check_output([cmd, 'python', 'avail', '-t', mod], 
                stderr=subprocess.STDOUT).splitlines()
            list1 = [s for s in list1 if not s.endswith(':')]
            self.assertNotEqual(list1, [],
                msg='No module {}'.format(mod))

    def test_module_list(self):
        cmd = '{}/bin/modulecmd'.format(os.environ['MODULESHOME'])
        # module list writes to stderr, because all module user output does
        list1 = subprocess.check_output([cmd, 'python', 'list', '-t'], 
            stderr=subprocess.STDOUT).splitlines()
        del list1[0]
        list1 = set([s.replace('(default)','') for s in list1])
        modMgr = gfdl.ModuleManager()
        list2 = set(modMgr._list())
        self.assertEqual(list1, list2)

    def test_module_load(self):
        modMgr = gfdl.ModuleManager()
        modMgr.load(self.test_mod_name)
        mod_list = modMgr._list()
        self.assertIn(self.test_mod_name, mod_list)

    def test_module_unload(self):
        modMgr = gfdl.ModuleManager()
        modMgr.load(self.test_mod_name)
        mod_list = modMgr._list()
        self.assertIn(self.test_mod_name, mod_list)
        modMgr.unload(self.test_mod_name)
        mod_list = modMgr._list()
        self.assertNotIn(self.test_mod_name, mod_list)


class TestFreppArgParsing(unittest.TestCase):
    config_test = {
        'case_list':[{'CASENAME':'B'}],
        'paths':{'OUTPUT_DIR':'/D'},
        'settings':{'E':'F', 'verbose':0, 'make_variab_tar': False}
    }
    frepp_stub = """
        set in_data_dir = /foo2/bar2
        set out_dir = /foo/bar
        set descriptor = baz.r1i1p1f1
        set yr1 = 1977
        set yr2 = 1981
        set make_variab_tar = 1
    """

    def test_parse_frepp_stub_regex(self):
        frepp_stub = """
            set foo1 = bar
            set foo2 = /complicated/path_name/1-2.3
            set foo3 = "./relative path/with spaces.txt"
            set foo4 = 1
            set foo5 = # comment
            set foo6 = not a #comment
        """
        d = gfdl.parse_frepp_stub(frepp_stub)
        self.assertEqual(d['foo1'], 'bar')
        self.assertEqual(d['foo2'], '/complicated/path_name/1-2.3')
        self.assertEqual(d['foo3'], '"./relative path/with spaces.txt"')
        self.assertEqual(d['foo4'], '1')
        self.assertNotIn('foo5', d)
        self.assertEqual(d['foo6'], 'not a #comment')

    def test_parse_frepp_stub_substitution(self):
        d = gfdl.parse_frepp_stub(self.frepp_stub)
        self.assertNotIn('in_data_dir', d)
        self.assertEqual(d['OUTPUT_DIR'], '/foo/bar')
        self.assertEqual(d['CASENAME'], 'baz.r1i1p1f1')
        self.assertNotIn('yr1', d)
        self.assertEqual(d['FIRSTYR'], 1977)
        self.assertEqual(d['make_variab_tar'], True)

    def test_parse_frepp_stub_mode(self):
        d = gfdl.parse_frepp_stub(self.frepp_stub)
        self.assertEqual(d['frepp'], True)

    @unittest.skip("")
    def test_parse_mdtf_args_frepp_overwrite(self):
        # overwrite defaults
        d = gfdl.parse_frepp_stub(self.frepp_stub)
        args = {'frepp': True}
        mdtf = MDTFFramework.__new__(MDTFFramework)
        config = self.config_test.copy()
        config = MDTFFramework.parse_mdtf_args([d, args], config)
        self.assertEqual(config['paths']['OUTPUT_DIR'], '/foo/bar')
        self.assertEqual(config['settings']['make_variab_tar'], True)
        self.assertEqual(config['settings']['E'], 'F')

    @unittest.skip("")
    def test_parse_mdtf_args_frepp_overwrite_both(self):
        # overwrite defaults and command-line
        d = gfdl.parse_frepp_stub(self.frepp_stub)
        args = {'frepp': True, 'OUTPUT_DIR':'/X', 'E':'Y'}
        mdtf = MDTFFramework.__new__(MDTFFramework)
        config = self.config_test.copy()
        config = MDTFFramework.parse_mdtf_args([d, args], config)
        self.assertEqual(config['paths']['OUTPUT_DIR'], '/foo/bar')
        self.assertEqual(config['settings']['make_variab_tar'], True)
        self.assertEqual(config['settings']['E'], 'Y')

    @unittest.skip("")
    def test_parse_mdtf_args_frepp_caselist(self):
        # overwrite defaults and command-line
        d = gfdl.parse_frepp_stub(self.frepp_stub)
        args = {'frepp': True}        
        mdtf = MDTFFramework.__new__(MDTFFramework)
        config = self.config_test.copy()
        config = MDTFFramework.parse_mdtf_args([d, args], config)
        self.assertEqual(len(config['case_list']), 1)
        self.assertEqual(config['case_list'][0]['CASENAME'], 'baz.r1i1p1f1')
        self.assertEqual(config['case_list'][0]['model'], 'CMIP_GFDL')
        self.assertEqual(config['case_list'][0]['variable_convention'], 'CMIP_GFDL')
        self.assertEqual(config['case_list'][0]['FIRSTYR'], 1977)
        self.assertEqual(config['case_list'][0]['LASTYR'], 1981)

# quick and dirty way to mock out init, since we only want to test one
# method
class _DummyGfdlppDataManager(gfdl.GfdlppDataManager):
    def __init__(self, component=None, data_freq=None, chunk_freq=None):
        self.root_dir = '/pp/'
        self.DateFreq = dt.DateFrequency
        self.component = component
        self.data_freq = data_freq
        self.chunk_freq = chunk_freq

class TestPPPathParsing(unittest.TestCase):
    def test_ts_parse(self):
        dm = _DummyGfdlppDataManager()
        dir_ = 'atmos_cmip/ts/daily/5yr'
        file_ = 'atmos_cmip.20100101-20141231.rsdscsdiff.nc'
        ds = dm.parse_relative_path(dir_, file_)
        self.assertEqual(ds.component, 'atmos_cmip')
        self.assertEqual(ds.date_freq, dt.DateFrequency('day'))
        self.assertEqual(ds.chunk_freq, dt.DateFrequency(5, 'yr'))
        self.assertEqual(ds.start_date, dt.Date(2010,1,1))
        self.assertEqual(ds.end_date, dt.Date(2014,12,31))
        self.assertEqual(ds.name_in_model, 'rsdscsdiff')
        self.assertEqual(ds._remote_data, '/pp/atmos_cmip/ts/daily/5yr/atmos_cmip.20100101-20141231.rsdscsdiff.nc')
        self.assertEqual(ds.date_range, dt.DateRange('20100101-20141231'))

    def test_static_parse(self):
        dm = _DummyGfdlppDataManager()
        dir_ = 'ocean_monthly'
        file_ = 'ocean_monthly.static.nc'
        ds = dm.parse_relative_path(dir_, file_)
        self.assertEqual(ds.component, 'ocean_monthly')
        self.assertEqual(ds.date_freq, dt.DateFrequency('fx'))
        self.assertEqual(ds.chunk_freq, dt.DateFrequency('fx'))
        self.assertEqual(ds.start_date, dt.FXDateMin)
        self.assertEqual(ds.end_date, dt.FXDateMax)
        self.assertEqual(ds.name_in_model, None)
        self.assertEqual(ds._remote_data, '/pp/ocean_monthly/ocean_monthly.static.nc')
        self.assertEqual(ds.date_range, dt.FXDateRange)


if __name__ == '__main__':
    unittest.main()
