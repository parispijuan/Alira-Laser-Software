from . import Experiment

class SimulatorExperiment(Experiment):

  def __init__(self):

    super().__init__()

    self.params.update({
      'wavelength': {
        'values': [100, 200, 300, 400, 500, 400, 300, 200, 100],
        'function': self.simulate_output
      },
      'time_steps': {
        'values': [0, 1, 2, 3, 4, 5, 6, 7, 8]
      }
    })

    self.tunable_params = ['wavelength']

  # simulator simply returns the value
  def simulate_output(self, value):
    return value