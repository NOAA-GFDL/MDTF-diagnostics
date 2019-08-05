import os
import unittest
import test_input_md5
import test_POD_execution
import test_output_md5

#if __name__ == '__main__':
os.environ['_MDTF_DATA_TEST'] = 'true'

loader = unittest.TestLoader()
full_suite = unittest.TestSuite()
full_suite.addTests(loader.loadTestsFromModule(test_input_md5))
full_suite.addTests(loader.loadTestsFromModule(test_POD_execution))
full_suite.addTests(loader.loadTestsFromModule(test_output_md5))

results = unittest.TextTestRunner().run(full_suite)
os.environ.pop('_MDTF_DATA_TEST')
