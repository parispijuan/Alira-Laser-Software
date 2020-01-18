import laser
from laser import *
import numpy
import time
import unittest

@unittest.skip("Cannot be enabled for automatic discovery testing to function.")
class test_laser_collection(unittest.TestCase):

    # Ensures that laser is collecting data and writing it to the output file.
    def test_output(self):
        drive = laser.get()
        time.sleep(10)
        drive.turn_off_laser()
        data = np.genfromtxt('Data.csv', delimiter = ',')
        self.assertEqual(data.shape[0], 2)
        self.assertTrue(data.shape[1] > 0)

if __name__ == '__main__':
    unittest.main()
