import unittest
from experiment import *
import laser

class Testing(unittest.TestCase):

    def test_experiment_setup(self):

      class CustomWavelengthAction(WavelengthAction):

        results = None

        def run(self, current_time):
          if current_time == 5:
            self.results = 1337

      action = CustomWavelengthAction()
      foobar_exp = Experiment.builder() \
        .with_actions([action]) \
        .with_duration(5) \
        .build()
      foobar_exp.run()

      assert action.results ==  1337

    def test_laser(self):

      class Laser:
        results = None
        def set_field(self, field_name, value):
          self.results = {field_name:value}

      laser.set_for_test(Laser())

      class CustomWavelengthAction(WavelengthAction):

        def run(self, current_time):
          return current_time

      foobar_exp = Experiment.builder() \
        .with_actions([CustomWavelengthAction()]) \
        .with_duration(1) \
        .build()
      foobar_exp.run()
       
      assert laser.get().results ==  {'wavelength':1}

    def tearDown(self):
      # Need to destroy singleton instance after every test
      laser.reset_for_testing()

if __name__ == '__main__':
    unittest.main()