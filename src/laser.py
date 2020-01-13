__global_laser_do_not_touch = {
  '__instance': None,
  '__get_called': False,
}

def get():
  global __global_laser_do_not_touch
  __global_laser_do_not_touch['__get_called'] = True
  if __global_laser_do_not_touch['__instance'] is None:
    __global_laser_do_not_touch['__instance'] = Laser()
  return __global_laser_do_not_touch['__instance']

def set_for_test(laser_instance):
  global __global_laser_do_not_touch
  if __global_laser_do_not_touch['__get_called']:
    raise "Can not call set() after get()"
  __global_laser_do_not_touch['__instance'] = laser_instance

def reset_for_testing():
  global __global_laser_do_not_touch
  __global_laser_do_not_touch = {
    '__instance': None,
    '__get_called': False,
  }

class Laser:

  def __init__(self):
    # TODO
    return

  def set_field(self, field_name, value):
    # TODO
    return