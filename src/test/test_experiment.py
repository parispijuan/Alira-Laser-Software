import unittest
import experiment
import time

class Testing(unittest.TestCase):
    def test_base_constructor(self):
        exp = experiment.Experiment()
        assert type(exp) == experiment.Experiment

    def test_wavelength_constructor(self):
        exp = experiment.WavelengthExperiment()
        assert type(exp) == experiment.WavelengthExperiment

    def test_simulator_constructor(self):
        exp = experiment.SimulatorExperiment()
        assert type(exp) == experiment.SimulatorExperiment

    def test_simulator_run(self):
        start = time.time()
        exp = experiment.SimulatorExperiment()
        run_complete = exp.run()
        end = time.time()

        assert run_complete

        # make sure expected run time is approprite
        assert end - start > exp.params['time_steps']['values'][-1]

if __name__ == '__main__':
    unittest.main()