import unittest
import experiment
import time

class Testing(unittest.TestCase):
    def test_base_constructor(self):
        exp = experiment.Experiment()
        assert type(exp) == experiment.Experiment

    def test_params_merge(self):
      exp = experiment.Experiment()
      exp.update_params({
          'current': {
          'values': {
            'action': [100, 200, 300, 400, 500, 400, 300, 200, 100],
          },
          'functions': {
            'action': sum
          }
        }
      })

      assert exp.params == {
      'pulse_width': {
        'default': 0,
        'functions': {
          'pre_action': None,
          'action': None,
          'post_action': None
        },
        'values': {
          'pre_action': [],
          'action': [],
          'post_action': []
        }
      },
      'pulse_rate': {
        'default': 0,
        'functions': {
          'pre_action': None,
          'action': None,
          'post_action': None
        },
        'values': {
          'pre_action': [],
          'action': [],
          'post_action': []
        }
      },
      'wavelength': {
        'default': 0,
        'functions': {
          'pre_action': None,
          'action': None,
          'post_action': None
        },
        'values': {
          'pre_action': [],
          'action': [],
          'post_action': []
        }
      },
      'current': {
        'default': 0,
        'functions': {
          'pre_action': None,
          'action': sum,
          'post_action': None
        },
        'values': {
          'pre_action': [],
          'action': [100, 200, 300, 400, 500, 400, 300, 200, 100],
          'post_action': []
        }
      },
      'scan_resolution': {
        'default': 0,
        'functions': {
          'pre_action': None,
          'action': None, # TODO: 'function': laser.set_scan_resolution,
          'post_action': None
        },
        'values': {
          'pre_action': [],
          'action': [],
          'post_action': []
        }
      },
      'time_steps': {
        'values': []
      }
    }

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

        # test experiment output
        assert sum(exp.results) == sum([a*b for a,b in zip(exp.params['wavelength']['values']['action'], exp.params['wavelength']['values']['post_action'])])

if __name__ == '__main__':
    unittest.main()