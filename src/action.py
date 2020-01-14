import laser
from abc import ABC, abstractmethod

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

class PulseWidthAction(Action):
  def __init__(self):
    super().__init__('pulse_width')

class PulseRateAction(Action):
  def __init__(self):
    super().__init__('pulse_rate')

class WavelengthAction(Action):
  def __init__(self):
    super().__init__('wavelength')

class CurrentAction(Action):
  def __init__(self):
    super().__init__('current')
    