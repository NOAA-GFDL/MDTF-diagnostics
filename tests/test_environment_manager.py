import os
import sys
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.environment_manager import EnvironmentManager

class TestEnvironmentManager(unittest.TestCase):
    test_config = {'case_list':[{}], 'pod_list':['X']}

    # ---------------------------------------------------

    def test_setUp(self):
        pass #TODO

    # ---------------------------------------------------

    # @mock.patch.dict('os.environ', {'DIAG_HOME':'/HOME'})
    # @mock.patch('src.shared_diagnostic.util.read_json', return_value = {
    #     'settings':{'driver':'C.ncl', 'program':'nonexistent_program'}, 'varlist':[]
    #     })
    # @mock.patch('os.path.exists', return_value = True)
    # def test_check_pod_driver_no_program_2(self, mock_exists, mock_read_json):
    #     # assertion fail if explicitly specified program not found
    #     pod = Diagnostic('A') 
    #     self.assertRaises(AssertionError, pod._check_pod_driver)
    
    # ---------------------------------------------------

    def test_run(self):
        pass #TODO

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()