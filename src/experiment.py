from action import PulseWidthAction, PulseRateAction, WavelengthAction, CurrentAction, EndAction

##
# The Experiment class follows a builder design parameter. It
# allows users to build experiments by defining actions for the
# laser to be performed at any second of wall clock time.
# The user also needs to define a duration. The parameters
# are validated when the build() command is run.
#
# Example: The following experiment sets the wavelength to
# 1337 at the 3 second mark. The total duration of the experiment
# is 5 seconds.
#
# class CustomWavelengthAction(WavelengthAction):
#
#   results = None
#
#   def run(self, current_time):
#     if current_time == 3:
#       self.results = 1337
#
# action = CustomWavelengthAction()
# foobar_exp = Experiment.builder() \
#   .with_actions([action]) \
#   .with_duration(5) \
#   .build()
# foobar_exp.run()

class Experiment:

  ##
  # Builder for the experiment class. This controls and validates
  # what the user can specify in an experiment
  class Builder:
    _actions = None
    _duration = None 

    ##
    # Gives the Builder the set of user defined Actions
    # to be run during the experiment
    def with_actions(self, actions):
      self._actions = actions
      return self

    ##
    # Gives the Builder the user specified duration of the
    # experiment
    def with_duration(self, duration):
      self._duration = duration
      return self

    ##
    # Method to extract the current actions list of the Builder
    def get_actions(self):
      return self._actions

    ##
    # Method to extract the current duration set in the Builder
    def get_duration(self):
      return self._duration

    ##
    # Method to build the Experiment class with the desired actions
    # and duration. Validates both of them. An experiment must have at
    # least one action. Duration must be specified, greater than 0, and
    # less than 2 hours
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
  ##
  # Should be called by the user to retrieve the class Builder
  def builder():
    return Experiment.Builder()

  def __init__(self, builder):
    self._actions = builder.get_actions()
    self._duration = builder.get_duration()

  ##
  # To be called when the user is ready to run the experiment
  # with the defined Actions and specified duration after
  # calling .build() on the Builder
  def run(self):
    import time
    # every loop is "one" second
    for i in range(self._duration):
      self._current_time += 1
      time.sleep(1)
      for action in self._actions:
        action.run_wrapper(self._current_time)

    EndAction().run_wrapper()

    return True
