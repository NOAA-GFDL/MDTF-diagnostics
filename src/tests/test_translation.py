import os
import unittest
from src.tests.shared_test_utils import setUp_config_singletons, tearDown_config_singletons
from src import data_sources, translation, varlist_util, pod_setup, util


class TestVariableTranslator(unittest.TestCase):
    def setUp(self):
        # set up translation dictionary without calls to filesystem
        setUp_config_singletons()

    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing,
        # otherwise the second, third, .. tests will use the instance created
        # in the first test instead of being properly initialized
        tearDown_config_singletons()

    _dummy_coords_d = {
        "PLACEHOLDER_X_COORD": {"axis": "X", "standard_name": "longitude", "units": "degrees_east"},
        "PLACEHOLDER_Y_COORD": {"axis": "Y", "standard_name": "latitude", "units": "degrees_north"},
        "PLACEHOLDER_Z_COORD": {
            "standard_name": "air_pressure",
            "units": "hPa",
            "positive": "down",
            "axis": "Z"
        },
        "PLACEHOLDER_T_COORD": {"axis": "T", "standard_name": "time", "units": "days"}
    }

    def test_variabletranslator(self):
        temp = translation.VariableTranslator()
        temp.add_convention({
            'name': 'not_CF', 'coords': self._dummy_coords_d,
            'variables': {
                'PRECT': {"standard_name": "pr_var", "units": "1", "ndim": 3},
                'PRECC': {"standard_name": "prc_var", "units": "1", "ndim": 3}
            }
        },
            "")
        self.assertEqual(temp.to_CF_name('not_CF', 'PRECT'), 'pr_var')
        self.assertEqual(temp.from_CF_name('not_CF', 'pr_var', 'atmos'), 'PRECT')

    def test_variabletranslator_no_key(self):
        temp = translation.VariableTranslator()
        temp.add_convention({
            'name': 'not_CF', 'coords': self._dummy_coords_d,
            'variables': {
                'PRECT': {"standard_name": "pr_var", "units": "1", "ndim": 3},
                'PRECC': {"standard_name": "prc_var", "units": "1", "ndim": 3}
            }
        },
            "")
        self.assertRaises(KeyError, temp.to_CF_name, 'B', 'PRECT')
        self.assertRaises(KeyError, temp.to_CF_name, 'not_CF', 'nonexistent_var')
        self.assertRaises(KeyError, temp.from_CF_name, 'B', 'PRECT', 'atmos')
        self.assertRaises(KeyError, temp.from_CF_name, 'not_CF', 'nonexistent_var', 'blah')

    def test_variabletranslator_aliases(self):
        # create multiple entries when multiple models specified
        temp = translation.VariableTranslator()
        temp.add_convention({
            'name': 'not_CF', 'coords': self._dummy_coords_d,
            'models': ['A', 'B'],
            'variables': {
                'PRECT': {"standard_name": "pr_var", "units": "1", "ndim": 3},
                'PRECC': {"standard_name": "prc_var", "units": "1", "ndim": 3}
            }
        },
            "")
        self.assertEqual(temp.from_CF_name('not_CF', 'pr_var', 'atmos'), 'PRECT')
        self.assertEqual(temp.from_CF_name('A', 'pr_var', 'atmos'), 'PRECT')
        self.assertEqual(temp.from_CF_name('B', 'pr_var', 'atmos'), 'PRECT')

    def test_variabletranslator_no_translation(self):
        dummy_varlist = {
            "data": {
                "frequency": "day",
                "realm": "atmos"
            },
            "dimensions": {
                "lat": {"standard_name": "latitude"},
                "lon": {"standard_name": "longitude"},
                "time": {"standard_name": "time"}
            },
            "varlist": {
                "rlut": {
                    "standard_name": "toa_outgoing_longwave_flux",
                    "units": "W m-2",
                    "dimensions": ["time", "lat", "lon"]
                }
            }
        }
        varlist = varlist_util.Varlist.from_struct(dummy_varlist)
        ve = varlist.vars[0]
        translate = translation.VariableTranslator().get_convention('None')
        tve = translate.translate(ve)
        self.assertEqual(ve.name, tve.name)
        self.assertEqual(ve.standard_name, tve.standard_name)
        self.assertEqual(ve.T.frequency, tve.T.frequency)
        # make sure copy of attrs was successful
        tve.standard_name = "foo"
        self.assertNotEqual(tve.standard_name, ve.standard_name)

    def test_variabletranslator_bad_modifier(self):
        dummy_varlist_wrong = {
            "data": {
                "frequency": "month"
            },
            "dimensions": {
                "lat": {"standard_name": "latitude"},
                "lon": {"standard_name": "longitude"},
                "time": {"standard_name": "time"}
            },
            "varlist": {
                "tref": {
                    "standard_name": "air temperature",
                    "units": "W m-2",
                    "dimensions": ["time", "lat", "lon"],
                    "modifier": "height"
                }
            }
        }
        dummy_varlist_correct = {
            "data": {
                "frequency": "month"
            },
            "dimensions": {
                "lat": {"standard_name": "latitude"},
                "lon": {"standard_name": "longitude"},
                "time": {"standard_name": "time"}
            },
            "varlist": {
                "tref": {
                    "standard_name": "air temperature",
                    "units": "W m-2",
                    "dimensions": ["time", "lat", "lon"],
                    "modifier": "atmos_height"
                }
            }
        }
        # test that supported modifier atmos_height is correct
        raised = False
        try:
            varlist = varlist_util.Varlist.from_struct(dummy_varlist_correct)
        except Exception as exc:
            print(exc)
            raised = True
        self.assertFalse(raised)
        # test that incorrect modifier height throws an error
        self.assertRaises(ValueError, varlist_util.Varlist.from_struct, dummy_varlist_wrong, parent=None)


class TestVariableTranslatorFiles(unittest.TestCase):
    def tearDown(self):
        # call _reset method deleting clearing Translator for unit testing,
        # otherwise the second, third, .. tests will use the instance created
        # in the first test instead of being properly initialized
        tearDown_config_singletons()

    def test_variabletranslator_load_files(self):
        # run in non-unit-test mode to test loading of config files
        cwd = os.path.dirname(os.path.realpath(__file__))
        code_root = os.path.dirname(os.path.dirname(cwd))
        raised = False
        try:
            translate = translation.VariableTranslator(code_root, unittest=False)
            translate.read_conventions(code_root, unittest=False)
        except Exception as exc:
            print(exc)
            raised = True
        self.assertFalse(raised)
        self.assertIn('CMIP', translate.conventions)
        self.assertIn('ua', translate.conventions['CMIP'].entries)

    def test_variabletranslator_real_data(self):
        # run in non-unit-test mode to test loading of config files
        cwd = os.path.dirname(os.path.realpath(__file__))
        code_root = os.path.dirname(os.path.dirname(cwd))
        translate = translation.VariableTranslator(code_root, unittest=False)
        translate.read_conventions(code_root, unittest=False)
        self.assertEqual(translate.to_CF_name('NCAR', 'PRECT'), "precipitation_rate")
        self.assertEqual(translate.from_CF_name('CMIP', 'toa_outgoing_longwave_flux',
                                                'atmos'), "rlut")


class TestPathManager(unittest.TestCase):
    def setUp(self):
        # set up translation dictionary without calls to filesystem
        setUp_config_singletons(paths={
            'CODE_ROOT': 'A', 'OBS_DATA_ROOT': 'B', 'MODEL_DATA_ROOT': 'C',
            'WORK_DIR': 'D', 'OUTPUT_DIR': 'E'
        })

    def tearDown(self):
        tearDown_config_singletons()

    # ------------------------------------------------

    def test_pathmgr_global(self):
        paths = util.ModelDataPathManager()
        self.assertEqual(paths.CODE_ROOT, 'A')
        self.assertEqual(paths.OUTPUT_DIR, 'E')

    @unittest.skip("")
    def test_pathmgr_global_asserterror(self):
        d = {
            'OBS_DATA_ROOT': 'B', 'MODEL_DATA_ROOT': 'C',
            'WORK_DIR': 'D', 'OUTPUT_DIR': 'E'
        }
        paths = util.ModelDataPathManager(config)
        self.assertRaises(AssertionError, paths, d, list(d.keys()))


@unittest.skip("TODO: Test needs to be rewritten following v3 beta 3 release")
class TestPathManagerPodCase(unittest.TestCase):
    def setUp(self):
        # set up translation dictionary without calls to filesystem
        setUp_config_singletons(
            config=self.case_dict,
            paths={
                'CODE_ROOT': 'A', 'OBS_DATA_ROOT': 'B', 'MODEL_DATA_ROOT': 'C',
                'WORK_DIR': 'D', 'OUTPUT_DIR': 'E'
            },
            pods={'AA': {
                'settings': {},
                'varlist': [{'var_name': 'pr_var', 'freq': 'mon'}]
            }
            })

    case_dict = {
        'CASENAME': 'A', 'model': 'B', 'startdate': 19000101, 'enddate': 21001231,
        'pod_list': ['AA']
    }

    def tearDown(self):
        tearDown_config_singletons()

    def test_pathmgr(self):
        model_paths = util.ModelDataPathManager(config)
        self.assertEqual(model_paths['MODEL_DATA_DIR'], 'TEST_MODEL_DATA_ROOT/A')
        self.assertEqual(model_paths['MODEL_WORK_DIR'], 'TEST_WORK_DIR/MDTF_A_1900_2100')

        # set up the case data source dictionary
        cases = dict()
        for case_name, case_d in self.case_dict.items():
            # instantiate the data_source class instance for the specified convention
            cases[case_name] = data_sources.data_source[case_d.convention.upper() + "DataSource"](case_name,
                                                                                                  case_d,
                                                                                                  model_paths,
                                                                                                  parent=None)
        pod = pod_setup.PodObject('AA', config)
        self.assertEqual(pod.paths['POD_CODE_DIR'], 'TEST_CODE_ROOT/diagnostics/AA')
        self.assertEqual(pod.paths['POD_OBS_DATA'], 'TEST_OBS_DATA_ROOT/AA')
        self.assertEqual(pod.paths['POD_WORK_DIR'], 'TEST_WORK_DIR/MDTF_A_1900_2100/AA')


# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()
