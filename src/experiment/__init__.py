# import for Laser stuff goes here
# import laser
import time
from collections import MutableMapping

class Experiment:

  params = {
    'pulse_width': {
      'default': 0,
      'functions': {
        'pre_action': None,
        'action': None, # TODO: 'function': laser.set_pulse_width,
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
        'action': None, # TODO: 'function': laser.set_pulse_rate,
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
        'action': None, # TODO: 'function': laser.set_wavelength,
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
        'action': None, # TODO: 'function': laser.set_current,
        'post_action': None
      },
      'values': {
        'pre_action': [],
        'action': [],
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

  tunable_params = ['pulse_width', 'pulse_rate', 'wavelength', 'current', 'scan_resolution']

  def __init__(self):
    self.setup_laser()
    self.verify_params()

  def setup_laser(self):
    # setup of laser goes here
    return

  def verify_params(self):
    for k in self.tunable_params:
      v = self.params[k]['values']
      for step in ['pre_action', 'action', 'post_action']:
        assert(len(self.params['time_steps']['values']) == len(v[step]) or len(v[step]) == 0)

  def update_params(self, new_params):
    self.params = self.merge(self.params, new_params)

  def merge(self, d1, d2):
    for k, v in d1.items(): 
        if k in d2:
            if all(isinstance(e, MutableMapping) for e in (v, d2[k])):
                d2[k] = self.merge(v, d2[k])
    d3 = d1.copy()
    d3.update(d2)

    self.verify_params()
    return d3

  def run(self):
    # initial param setup step
    for param in self.tunable_params:

        # iterate through pre, action, and post
        for step in self.params[param]['functions']:
          func = self.params[param]['functions'][step]
          if not func is None:
            value = self.params[param]['values'][step][0] if len(self.params[param]['values'][step]) != 0 else self.params[param]['default']
            func(value)

    # every subsequent time step
    for i in range(1, len(self.params['time_steps']['values'])):
      time.sleep(self.params['time_steps']['values'][i] - self.params['time_steps']['values'][i-1])

      for param in self.tunable_params:

        # iterate through pre, action, and post
        for step in self.params[param]['functions']:
          func = self.params[param]['functions'][step]
          if not func is None:
            value = self.params[param]['values'][step][0] if len(self.params[param]['values'][step]) != 0 else self.params[param]['default']
            func(value)

    return True

from .simulator_experiment import SimulatorExperiment
from .wavelength_experiment import WavelengthExperiment
