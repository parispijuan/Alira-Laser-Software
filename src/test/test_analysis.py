## @package test_analysis
#  This module contains unit tests for the analysis class - this class
#   handles reading the data obtained from an experiment and analysis 
#   functions like taking the derivative or integral of the data.

import unittest
import numpy as np
from data_analysis import analysis, display
import time

## Testing class for the `Analysis` module
class AnalysisTesting(unittest.TestCase):
    
    def setUp(self):
        test_data = np.linspace(-10.5,10.5,500)
        self.analysis_obj = analysis.Analysis(test_data)


    ## Test the constructor:
    #   @param self Pointer to the `AnalysisTesting` object
    #   - Assert that the type of the object is `Analysis`.
    #   - Assert that data_raw and data_adjusted member variables contain the same
    #       information.
    def test_base_constructor(self):
        self.assertIsInstance(self.analysis_obj, analysis.Analysis)
        np.testing.assert_array_equal(self.analysis_obj.data_raw, \
                         self.analysis_obj.data_adjusted)


    ## Test the reset function:
    #   - Make changes to data_adjusted member variable
    #   - Assert that it is different from data_raw
    #   - Call the reset function and then assert that data_adjusted is now equal
    #       to data_raw
    def test_reset(self):
        self.analysis_obj.data_adjusted[0] = 10000
        self.analysis_obj.data_adjusted[1] = 0.000001

        print(self.analysis_obj.data_raw)
        self.assertNotEqual(self.analysis_obj.data_raw, \
                            self.analysis_obj.data_adjusted)

        self.analysis_obj.reset()

        np.testing.assert_array_equal(self.analysis_obj.data_raw, \
                         self.analysis_obj.data_adjusted)



        
if __name__ == '__main__':
    unittest.main()