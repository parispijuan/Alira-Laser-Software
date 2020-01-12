from . import Experiment

class SimulatorExperiment(Experiment):

  results = []

  def __init__(self):

    super().__init__()

    self.update_params({
      'wavelength': {
        'values': {
          'pre_action': [None]*9,
          'action': [100, 200, 300, 400, 500, 400, 300, 200, 100],
          'post_action': [0, 1, 2, 3, 4, 5, 6, 7, 8]
        },
        'functions': {
          'pre_action': self.get_user_input,
          'action': self.simulate_output,
          'post_action': self.process_results
        }
      },
      'time_steps': {
        'values': [0, 1, 2, 3, 4, 5, 6, 7, 8]
      }
    })

    self.tunable_params = ['wavelength']

  # get input from user
  def get_user_input(self, value):
    if self.current_time_step == 4:
      value = input('Which wavelength do you want? ')
      self.params['wavelength']['values']['action'][self.current_time_step] = int(value)

  # simulator simply returns the value
  def simulate_output(self, value):
    self.results.append(value)

  # do some post processing on result
  def process_results(self, value):
    self.results[self.current_time_step] *= value