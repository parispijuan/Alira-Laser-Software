from . import Experiment

class WavelengthExperiment(Experiment):

  def __init__(self):

    super().__init__()

    self.params.update({
      'wavelength': {
        'values': [100, 200, 300, 400, 500, 400, 300, 200, 100]
      },
      'time_steps': {
        'values': [0, 1, 2, 3, 4, 5, 6, 7, 8]
      }
    })

    self.tunable_params = ['wavelength']