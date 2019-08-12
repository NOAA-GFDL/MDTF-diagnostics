import os
import sys
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.shared_environment import EnvironmentManager

class TestEnvironmentManager(unittest.TestCase):
    test_config = {'case_list':[{}], 'pod_list':['X']}

    # ---------------------------------------------------

    def test_setUp(self):
        pass #TODO

    # ---------------------------------------------------

    
    # ---------------------------------------------------

    def test_run(self):
        pass #TODO

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()