import unittest
import experiment

class Testing(unittest.TestCase):
    def test_base_constructor(self):
        exp = experiment.Experiment()
        assert type(exp) == experiment.Experiment

    def test_wavelength_constructor(self):
        exp = experiment.WavelengthExperiment()
        assert type(exp) == experiment.WavelengthExperiment

if __name__ == '__main__':
    unittest.main()