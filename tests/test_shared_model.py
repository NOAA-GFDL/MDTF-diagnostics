import os
import unittest
import mock # define mock os.environ so we don't mess up real env vars
from src.shared_model import Model

# TODO: refactor Model's __init__: pain to have to mock it out

class TestModel(unittest.TestCase):

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('glob.glob', return_value = [''])
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('src.shared_model.util.read_yaml', 
        return_value = {'model_name':'A','var_names':['B']})
    def test_read_model_varnames(self, mock_safe_load, mock_open, mock_glob):
        # normal operation - convert string to list
        model = Model('A')
        self.assertEqual(model.model_dict['A'], ['B'])

    @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    @mock.patch('glob.glob', return_value = [''])
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('src.shared_model.util.read_yaml', 
        return_value = {'model_name':['A','C'],'var_names':['B']})
    def test_read_model_varnames_multiple(self, mock_safe_load, mock_open, mock_glob):
        # create multiple entries when multiple models specified
        model = Model('A')
        self.assertEqual(model.model_dict['A'], ['B'])
        self.assertEqual(model.model_dict['C'], ['B'])

    # ---------------------------------------------------

    def test_setup_model_paths(self):
        pass

    # ---------------------------------------------------

    model_dict_set_model_env_vars = {
        'A':{'B':'C', 'D':5}
    }
    @mock.patch.dict('os.environ', {})
    def test_set_model_env_vars(self):
        # set env vars for model
        with mock.patch.object(Model, '__init__', lambda x, y: None):
            model = Model('A')
            model.model_dict = self.model_dict_set_model_env_vars
            model._set_model_env_vars('A')
            self.assertEqual(os.environ['B'], 'C')
            self.assertEqual(os.environ['D'], '5')

    @mock.patch.dict('os.environ', {})
    def test_set_model_env_vars_no_model(self):
        # exit if can't find model
        with mock.patch.object(Model, '__init__', lambda x, y: None):
            model = Model('A')
            model.model_dict = self.model_dict_set_model_env_vars
            self.assertRaises(SystemExit, model._set_model_env_vars, 
                'nonexistent')

    # ---------------------------------------------------

    def test_setup_html(self):
        pass

if __name__ == '__main__':
    unittest.main()