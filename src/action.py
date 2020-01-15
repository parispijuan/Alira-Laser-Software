import laser
from abc import ABC, abstractmethod

##
# The Action class is an Abstract Base Class for all possible actions
# that the physical laser can accomplish. The ABC only needs the user
# to define the run(self, current_time) method which outputs the desired laser setting.
# Internally, this is used in a run_wrapper which is what the user
# should call to actually change the state of the laser. The user
# is not supposed to subclass the Action class

class Action(ABC):

  _field_name = None

  def __init__(self, field):
    self._field_name = field

  def run_wrapper(self, current_time):
    value = self.run(current_time)
    laser.get().set_field(self._field_name, value)

  @abstractmethod
  def run(self, current_time):
    """ The main function of the action """
    return

##
# The EndAction class is what is used by the experiment class
# to turnoff the laser

class EndAction:
  def run(self):
    laser.get().turn_off_laser()
    return

##
# The PulseWidthAction class is what should be subclassed
# by actions that wish to alter the pulse width of the laser.
# The user simply defines run(self, current_time) which should
# output the desired pulse width at wall clock time current_time.
#
# Example: The following would make an action that changes the
# pulse width to 7 after 5 seconds in the experiment
#
# class CustomPulseWidthAction(PulseWidthAction):
#
#   results = None
#
#   def run(self, current_time):
#     if current_time == 5:
#       self.results = 7

class PulseWidthAction(Action):
  def __init__(self):
    super().__init__('pulse_width')

##
# The PulseRateAction class is what should be subclassed
# by actions that wish to alter the pulse rate of the laser.
# The user simply defines run(self, current_time) which should
# output the desired pulse rate at wall clock time current_time.
#
# Example: The following would make an action that changes the
# pulse rate to 7 after 5 seconds in the experiment
#
# class CustomPulseRateAction(PulseRateAction):
#
#   results = None
#
#   def run(self, current_time):
#     if current_time == 5:
#       self.results = 7

class PulseRateAction(Action):
  def __init__(self):
    super().__init__('pulse_rate')

##
# The WavelengthAction class is what should be subclassed
# by actions that wish to alter the wavelength of the laser.
# The user simply defines run(self, current_time) which should
# output the desired wavelength at wall clock time current_time.
#
# Example: The following would make an action that changes the
# wavelength to 7 after 5 seconds in the experiment
#
# class CustomWavelengthAction(WavelengthAction):
#
#   results = None
#
#   def run(self, current_time):
#     if current_time == 5:
#       self.results = 7

class WavelengthAction(Action):
  def __init__(self):
    super().__init__('wavelength')

##
# The CurrentAction class is what should be subclassed
# by actions that wish to alter the current of the laser.
# The user simply defines run(self, current_time) which should
# output the desired current at wall clock time current_time.
#
# Example: The following would make an action that changes the
# current to 7 after 5 seconds in the experiment
#
# class CustomCurrentAction(CurrentAction):
#
#   results = None
#
#   def run(self, current_time):
#     if current_time == 5:
#       self.results = 7

class CurrentAction(Action):
  def __init__(self):
    super().__init__('current')