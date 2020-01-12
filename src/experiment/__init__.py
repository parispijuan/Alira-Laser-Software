# import for Laser stuff goes here
# import laser
import time

class Experiment:

  # these should be set
  params = {
    'pulse_width': {
      'default': 0,
      # TODO: 'function': laser.set_pulse_width,
      'values': []
    },
    'pulse_rate': {
      'default': 0,
      # TODO: 'function': laser.set_pulse_rate,
      'values': []
    },
    'wavelength': {
      'default': 0,
      # TODO: 'function': laser.set_pulse_wavelength,
      'values': []
    },
    'current': {
      'default': 0,
      # TODO: 'function': laser.set_current,
      'values': []
    },
    'scan_resolution': {
      'default': 0,
      # TODO: 'function': laser.set_scan_resolution,
      'values': []
    },
    'time_steps': {
      'values': []
    }
  }

  tunable_params = ['pulse_width', 'pulse_rate', 'wavelength', 'current', 'scan_resolution']

  def __init__(self):
    self.setup_laser()
    self.verify_params()

  def setup_laser(self):
    # setup of laser goes here
    return

  def verify_params(self):
    for k, v in self.params.items():
      assert(len(self.params['time_steps']['values']) == len(v['values']) or len(v['values']) == 0)

  def run(self):
    # initial param setup step
    for param in self.tunable_params:
        func = self.params[param]['function']
        value = self.params[param]['values'][0] if len(self.params[param]['values']) != 0 else self.params[param]['default']
        func(value)

    # every subsequent time step
    for i in range(1, len(self.params['time_steps']['values'])):
      time.sleep(self.params['time_steps']['values'][i] - self.params['time_steps']['values'][i-1])

      for param in self.tunable_params:
        func = self.params[param]['function']
        value = self.params[param]['values'][i] if len(self.params[param]['values']) != 0 else self.params[param]['default']
        func(value)

    return True

from .simulator_experiment import SimulatorExperiment
from .wavelength_experiment import WavelengthExperiment
