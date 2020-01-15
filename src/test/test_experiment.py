import unittest
from experiment import *
import laser

class Testing(unittest.TestCase):

    def test_experiment_setup(self):

      class Laser:
        results = None
        def set_field(self, field_name, value):
          self.results = {field_name:value}

        def turn_off_laser(self):
          return

      laser.set_for_test(Laser())

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

      self.assertEqual(action.results, 1337)

    def test_invalid_experiements(self):

      class Laser:
        results = None
        def set_field(self, field_name, value):
          self.results = {field_name:value}

        def turn_off_laser(self):
          return

      laser.set_for_test(Laser())

      class CustomWavelengthAction(WavelengthAction):

        results = None

        def run(self, current_time):
          if current_time == 5:
            self.results = 1337

      action = CustomWavelengthAction()

      # No actions
      with self.assertRaises(AssertionError):
        foobar_exp = Experiment.builder() \
          .with_actions([]) \
          .with_duration(5) \
          .build()
        foobar_exp.run()

      # No duration
      with self.assertRaises(AssertionError):
        foobar_exp = Experiment.builder() \
          .with_actions([action]) \
          .build()
        foobar_exp.run()

      # Negative duration
      with self.assertRaises(AssertionError):
        foobar_exp = Experiment.builder() \
          .with_actions([action]) \
          .with_duration(-1) \
          .build()
        foobar_exp.run()

      # Too long duration
      with self.assertRaises(AssertionError):
        foobar_exp = Experiment.builder() \
          .with_actions([action]) \
          .with_duration(3*60*60) \
          .build()
        foobar_exp.run()

    def test_laser_singleton(self):

      with self.assertRaises(RuntimeError):
        class Laser:
          results = None
          def set_field(self, field_name, value):
            self.results = {field_name:value}

        laser.set_for_test(Laser())
        laser.get()
        laser.set_for_test(Laser())

    def tearDown(self):
      # Need to destroy singleton instance after every test
      laser.reset_for_testing()

if __name__ == '__main__':
    unittest.main()