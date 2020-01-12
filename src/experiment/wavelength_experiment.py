from . import Experiment

class WavelengthExperiment(Experiment):

  params = {
    'wavelength': {
      'default': 100,
      # TODO: 'function': laser.set_pulse_wavelength,
      'values': [100, 200, 300, 400, 500, 400, 300, 200, 100]
    },
    'time_steps': {
      'values': [0, 1, 2, 3, 4, 5, 6, 7, 8]
    }
  }

  tunable_params = ['wavelength']