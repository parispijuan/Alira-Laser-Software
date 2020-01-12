# import for Laser stuff goes here
import laser
import time

class Experiment:

  # these should be set
  params = {
    'pulse_width': {
      'default': 0,
      'function': laser.set_pulse_width,
      'values': []
    },
    'pulse_rate': {
      'default': 0,
      'function': laser.set_pulse_rate,
      'values': []
    },
    'wavelength': {
      'default': 0,
      'function': laser.set_pulse_wavelength,
      'values': []
    },
    'current': {
      'default': 0,
      'function': laser.set_current,
      'values': []
    },
    'scan_resolution': {
      'default': 0,
      'function': laser.set_scan_resolution,
      'values': []
    }
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

  def verify_params(self):
    for k, v in self.params:
      assert(len(params['time_steps']['values']) == len(v['values']) or len(v['values']) == 0)

  def run(self):
    for i in range(len(params['time_steps']['values'])):
      time.sleep(params['time_steps']['values'][i])

      for param in tunable_params:
        func = params[param]['function']
        value = params[param]['values'][i] if len(params[param]['values']) != 0 else params[param]['default']
        func(value)
