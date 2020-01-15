## Profiling analysis code
# This is a basic module that contains tests for looking at time
# lengths for running each method in Analysis
#

import unittest
import numpy as np
from data_analysis import analysis
import time

## Profiling class for the 'Analysis' module
class AnalysisProfiling(unittest.TestCase):
    
    ## setUp method prepares the start time
    # testing on a qubic array
    def setUp(self):
        self.test_data_lin = np.linspace(-10.5,10.5,10000)
        self.analysis_obj = analysis.Analysis(self.test_data_lin**3)
        self.startTime = time.time()

    ## tearDown method
    # comparing the run times for tests
    def tearDown(self):
        t = time.time() - self.startTime
        print('%s: %.3f' % (self.id(), t))

    ## reset profile test
    # here we only test the reset method
    def testProfile_Reset(self):
        self.analysis_obj.reset()
        
    ## differenttiate profile test
    # run reset before differentiating in order to use the original data
    #
    def testProfile_differentiate(self):
        self.analysis_obj.reset()
        self.analysis_obj.differentiate()

    ## integrate profile test
    # run reset before differentiating in order to use the original data
    #
    def testProfile_integrate(self):
        self.analysis_obj.reset()
        self.analysis_obj.integrate()

    ## trim profile test
    # run reset before differentiating in order to use the original data
    # triming from a to b
    #
    def testProfile_trim(self):
        a = 100
        b = 500
        self.analysis_obj.reset()
        self.analysis_obj.trim(a, b)

    ## normalize profile test
    # run reset before differentiating in order to use the original data
    #
    def testProfile_normalize(self):
        self.analysis_obj.reset()
        self.analysis_obj.normalize()

    ## ratio profile test
    # run reset before differentiating in order to use the original data
    # taking ratio with self.test_data_lin
    #
    def testProfile_ratio(self):
        self.analysis_obj.reset()
        self.analysis_obj.ratio(self.test_data_lin)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(AnalysisProfiling)
    unittest.TextTestRunner(verbosity=0).run(suite)


