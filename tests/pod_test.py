import os
import unittest
import test_input_checksums
import test_POD_execution
import test_output_checksums

#if __name__ == '__main__':
os.environ['_MDTF_DATA_TEST'] = 'true'

# TestSuite lets us control the order of test execution
loader = unittest.TestLoader()
full_suite = unittest.TestSuite()
full_suite.addTests(loader.loadTestsFromModule(test_input_checksums))
full_suite.addTests(loader.loadTestsFromModule(test_POD_execution))
full_suite.addTests(loader.loadTestsFromModule(test_output_checksums))

results = unittest.TextTestRunner().run(full_suite)
os.environ.pop('_MDTF_DATA_TEST')
