import laser
from laser import *
import numpy
import time
import unittest

@unittest.skip("Cannot be enabled for automatic discovery testing to function.")
class test_laser_operation(unittest.TestCase):

    # Should create a connection to the laser.
    @classmethod
    def setUpClass(cls):
        cls.drive = laser.get()

    # Should indicate that unsafe wavelength parameter
    # inputs are throwing exceptions. Unable to verify values.
    def test_set_wavelength(self):
        self.assertRaises(Laser_Exception, self.drive.set_field, "wavelength", 1300)
        self.assertRaises(Laser_Exception, self.drive.set_field, "wavelength", 900)
        self.drive.set_field("wavelength", 1020)
        self.assertEqual(self.drive.wavelength, 1020)

    # Should indicate correct setting of current qcl parameter, and that unsafe
    # inputs are throwing exceptions.
    def test_set_current(self):
        self.assertRaises(Laser_Exception, self.drive.set_field, "current", 1700)
        self.assertRaises(Laser_Exception, self.drive.set_field, "current", 1100)
        self.drive.set_field("current", 1300)
        qcl_params = self.drive._Laser__read_qcl_params()
        out = qcl_params['current_ma_ptr'].contents.value
        self.assertEqual(out, 1300)

    # Should indicate correct setting of pulse rate qcl parameter, and that unsafe
    # inputs are throwing exceptions.
    def test_set_pr(self):
        self.assertRaises(Laser_Exception, self.drive.set_field, "pulse_rate", 16000)
        self.assertRaises(Laser_Exception, self.drive.set_field, "pulse_rate", 1000)
        self.drive.set_field("pulse_rate", 10000)
        qcl_params = self.drive._Laser__read_qcl_params()
        out = qcl_params['pulse_rate_hz_ptr'].contents.value
        self.assertEqual(out, 10000)

    # Should indicate correct setting of pulse rate qcl parameter, and that unsafe
    # inputs are throwing exceptions.
    def test_set_pw(self):
        self.assertRaises(Laser_Exception, self.drive.set_field, "pulse_width", 2600)
        self.assertRaises(Laser_Exception, self.drive.set_field, "pulse_width", 400)
        self.drive.set_field("pulse_width", 1000)
        qcl_params = self.drive._Laser__read_qcl_params()
        out = qcl_params['pulse_width_ns_ptr'].contents.value
        self.assertEqual(out, 1000)


    # Ensures the connection is closed and laser is turned off at conclusion of
    # testing.
    @classmethod
    def tearDownClass(cls):
        cls.drive.turn_off_laser()

if __name__ == '__main__':
    unittest.main()
