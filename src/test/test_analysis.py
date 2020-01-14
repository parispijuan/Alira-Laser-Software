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
    
    ## setUp method prepares the test fixture, initializing an Analysis object
    def setUp(self):
        test_data = np.linspace(-10.5,10.5,500)
        test_integrate_data = np.linspace(10,10,20)

        self.analysis_obj = analysis.Analysis(test_data)
        self.integrate_obj = analysis.Analysis(test_integrate_data)


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

        self.assertEqual(
            np.array_equal(self.analysis_obj.data_raw, \
                           self.analysis_obj.data_adjusted), False)

        self.analysis_obj.reset()

        np.testing.assert_array_equal(self.analysis_obj.data_raw, \
                         self.analysis_obj.data_adjusted)


    ## Test the differentiate function:
    #   - For the analysis linspace used, the derivative should be a constant 
    #       1 for all values
    #   - Square original, deriv should be 2*orig, ignore end points as np.gradient
    #       uses first differences with those points
    #   - Repeat this with the cube and to the fourth power
    def test_differentiate(self):
        self.analysis_obj.differentiate()

        for value in self.analysis_obj.data_adjusted.tolist():
            self.assertAlmostEqual(value, 1) # default is 7 places


        self.analysis_obj.reset()
        self.analysis_obj.data_adjusted = self.analysis_obj.data_adjusted**2
        self.analysis_obj.differentiate()

        for value,orig in zip(self.analysis_obj.data_adjusted.tolist()[1:-1],\
                          self.analysis_obj.data_raw.tolist()[1:-1]):
            self.assertAlmostEqual(value, 2*orig)


        self.analysis_obj.reset()
        self.analysis_obj.data_adjusted = self.analysis_obj.data_adjusted**3
        self.analysis_obj.differentiate()
        self.analysis_obj.differentiate()

        for value,orig in zip(self.analysis_obj.data_adjusted.tolist()[2:-2],\
                          self.analysis_obj.data_raw.tolist()[2:-2]):
            self.assertAlmostEqual(value, 6*orig)


        self.analysis_obj.reset()
        self.analysis_obj.data_adjusted = self.analysis_obj.data_adjusted**4
        self.analysis_obj.differentiate()
        self.analysis_obj.differentiate()
        self.analysis_obj.differentiate()

        for value,orig in zip(self.analysis_obj.data_adjusted.tolist()[3:-3],\
                          self.analysis_obj.data_raw.tolist()[3:-3]):
            self.assertAlmostEqual(value, 24*orig)



    ## Test the integrate function:
    #   - For the integrate linspace used, the integral should return a np array
    #       that is equivalent to the list comprehension [x*10 for x in range(1,20)]
    def test_integrate(self):     
        self.integrate_obj.integrate()

        self.assertEqual(self.integrate_obj.data_adjusted.tolist(), \
                         [x*10 for x in range(1,20)])


    ## Test the trim function:
    #   - For the analysis linspace used, cut the first and last element out
    #   - The new first element should be the old second element
    #   - The new last element should be the old second to last element
    def test_trim(self):
        start = 1
        stop = np.prod(self.analysis_obj.data_adjusted.shape) - 1

        self.analysis_obj.trim(start, stop) 

        self.assertEqual(self.analysis_obj.data_adjusted[0], \
                         self.analysis_obj.data_raw[1])
        self.assertEqual(self.analysis_obj.data_adjusted[-1], \
                         self.analysis_obj.data_raw[-2])

    ## Test the normalize function:
    #   - For the analysis linspace used, all values should be divided by 10.5
    #   - Iterate and compare each value of the new array to the old array's value
    #       divided by 10.5
    #   - The values should all be less than one, so assert this and check
    def test_normalize(self):
        self.analysis_obj.normalize()

        i = 0
        for value in self.analysis_obj.data_adjusted.tolist():
            self.assertEqual(value, self.analysis_obj.data_raw[i]/10.5)
            self.assertLessEqual(value, 1)
            i += 1


        
if __name__ == '__main__':
    unittest.main()