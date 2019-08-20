import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
from src.data_manager import DataManager

class TestDataManager(unittest.TestCase):

    def test_setup_model_paths(self):
        pass

    model_dict_set_model_env_vars = {
        'A':{'B':'C', 'D':5}
    }

    @mock.patch.dict('os.environ', {})
    @patch.multiple(DataManager, __abstractmethods__=set())
    def test_set_model_env_vars(self):
        # set env vars for model
        with mock.patch.object(Model, '__init__', lambda x, y: None):
            model = Model('A')
            model.model_dict = self.model_dict_set_model_env_vars
            model._set_model_env_vars('A')
            self.assertEqual(os.environ['B'], 'C')
            self.assertEqual(os.environ['D'], '5')

    @mock.patch.dict('os.environ', {})
    @patch.multiple(DataManager, __abstractmethods__=set())
    def test_set_model_env_vars_no_model(self):
        # exit if can't find model
        with mock.patch.object(Model, '__init__', lambda x, y: None):
            model = Model('A')
            model.model_dict = self.model_dict_set_model_env_vars
            self.assertRaises(SystemExit, model._set_model_env_vars, 
                'nonexistent')

    def test_setup_html(self):
        pass

if __name__ == '__main__':
    unittest.main()