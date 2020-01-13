from action import PulseWidthAction, PulseRateAction, WavelengthAction, CurrentAction, ScanResolutionAction

class Experiment:

  class Builder:
    _actions = None
    _duration = None 

    def with_actions(self, actions):
      self._actions = actions
      return self

    def with_duration(self, duration):
      self._duration = duration
      return self

    def get_actions(self):
      return self._actions

    def get_duration(self):
      return self._duration

    def build(self):
      # Validate that that the experiment is defined properly

      assert len(self._actions) > 0
      assert not self._duration is None
      assert self._duration > 0

      # Max 2 hour experiment
      assert self._duration < 60*60*2

      return Experiment(self)

  _actions = []
  _current_time = 0
  _duration = None

  @staticmethod
  def builder():
    return Experiment.Builder()

  def __init__(self, builder):
    self._actions = builder.get_actions()
    self._duration = builder.get_duration()

  def run(self):
    import time
    # every loop is "one" second
    for i in range(self._duration):
      self._current_time += 1
      time.sleep(1)
      for action in self._actions:
        action.run_wrapper(self._current_time)

    return True
