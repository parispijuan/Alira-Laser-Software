'''
Primary software/hardware interface.
'''

import time
import os
import platform
from ctypes import CDLL, pointer, c_uint32, c_uint16, c_uint8, c_bool, c_float, c_char
from threading import Thread
import numpy as np
import matplotlib.pyplot as plt
import zhinst
import zhinst.ziPython
import zhinst.utils


class HardwareException(Exception):
    '''Exception class for all fatal exceptions in hardware control'''
    pass


class LaserDriver:
    '''Class interfacing with SDK to control hardware.'''

    def __init__(self, testing_sdk=None, testing_zi_sdk=None, sdk_version=None):
        '''Initialize SDKs and provide hook for testing.

        Arguments:
          testing_sdk: SideKickSDK library if None, else class with equivalent methods for testing
          testing_zisdk: ZI library if None, else class with equivalent methods for testing
          sdk_location: 86 or 64 (which version of Sidekick sdk to load)

        Raises:
           HardwareException if SDK cannot be initialized
        '''

        if sdk_version == 64:
            self.sdk_location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx64.dll')
        elif sdk_version == 86:
            self.sdk_location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx86.dll')
        elif platform.machine().endswith('64'):
            self.sdk_location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx64.dll')
        else:
            self.sdk_location = os.path.join(os.path.dirname(__file__), 'SidekickSDKx86.dll')

        self.arm_laser_timeout = 20

        self.qcl_pulse_rate_hz = 100000
        self.qcl_temp_c = 17
        self.qcl_current_ma = 1500
        self.qcl_width_ns = 500
        self.qcl_set_params_timeout = 5

        self.cool_tecs_timeout = 60
        self.cool_tecs_additional = 10

        self.turn_on_laser_timeout = 30

        self.laser_on = False
        self.laser_on_attempts = 3
        self.laser_on_wait = 5

        self.lockin_ip = '192.168.48.102'
        self.lockin_port = 8004
        self.lockin_amplitude = 1.0 # [V]
        self.lockin_poll_length = 30

        self.lockin_demod_c = '0' # demod channel, for paths on the device
        # self.lockin_out_c = '0' # signal output channel
        self.lockin_in_c = '0' # signal input channel
        self.lockin_osc_c = '0' # oscillator
        self.lockin_osc_freq = 100000 # 30e5 #[Hz] this matches the laser controller
        self.lockin_time_constant = 1e-2 # 3e-3 # 0.0075 # 0.001  [s]
        self.demod_idx = float(self.lockin_demod_c) + 1
        self.poll_timeout = 500 # timeout in ms
        self.demod_rate = 2e3 # 80 # 300 [samples / s]

        self.start_delay = 5
        self.num_scan_steps = 1
        self.scan_ww_unit = c_uint8(2) # SIDEKICK_SDK_UNITS_CM1
        self.scan_start_ww = c_float(1020)
        self.scan_stop_ww = c_float(1220)
        self.scan_step = c_float(3)
        self.manual_tuning_timeout = 50
        self.scan_num_scans = c_uint16(1)
        self.scan_keep_on = c_uint8(1) #0
        self.scan_bidirectional = c_uint8(0)
        self.scan_dwell_time_ms = c_uint32(250) #200
        self.scan_trans_time_ms = c_uint32(25) #25
        self.scan_write = c_bool(True)
        self.scan_operation = c_uint8(7) # SIDEKICK_SDK_SCAN_START_STEP_MEASURE
        self.scan_wait = 0.25
        self.step_scan_timeout = 30

        self.qcl_read_is_write = c_bool(False)
        self.qcl_update_is_write = c_bool(True)

        self.sidekick_sdk_ret_success = 0

        self.sdk = CDLL(self.sdk_location) if testing_sdk is None else testing_sdk
        self.zi_sdk = zhinst if testing_zi_sdk is None else testing_zi_sdk
        self._call_sdk_bool(self.sdk.SidekickSDK_Initialize,
                            'SDK initialization successful', 'Unable to initialize SDK')

        self.laser_turn_off_attempts = 3

        self.handle = None
        self.device = None
        self.daq = None

    def setup_experiment(self):
        '''Main method to perform all laser setup prior to scanning.

        Raises:
           HardwareException for fatal errors controlling hardware
        '''
        try:
            self.connect_laser()
            self.arm_laser()
            self.set_qcl_params()
            self.cool_tecs()
            self.turn_on_laser()
            self.connect_to_lockin()
            self.initialize_lockin()
        except HardwareException as e:
            self.turn_off_laser()
            raise e

    def connect_laser(self):
        '''Connect to laser via USB.

        Raises:
          HardwareException if laser is unavailable or incorrectly connected
        '''
        num_devices_ptr = pointer(c_uint16())
        handle_ptr = pointer(c_uint32())
        self._call_sdk_bool(self.sdk.SidekickSDK_SearchForUsbDevices,
                            'Found USB devices', 'Error occured while searching for USB devices')
        self._call_sdk_bool(self.sdk.SidekickSDK_GetNumOfDevices,
                            'Got device count', 'Error when getting device count', num_devices_ptr)
        self._call_sdk_bool(self.sdk.SidekickSDK_ConnectToDeviceNumber,
                            'Connected to laser', 'Unable to connect to laser',
                            handle_ptr, c_uint16(num_devices_ptr.contents.value - 1))
        self.handle = handle_ptr.contents
        self.sdk.SidekickSDK_ReadAdminQclParams(self.handle, 0)
        self._call_sdk_bool_ptr(self.sdk.SidekickSDK_AdminQclIsAvailable,
                                'QCL installed and detected', 'QCL not detected')
        self._call_sdk_bool_ptr(self.sdk.SidekickSDK_isInterlockedStatusSet,
                                'Interlock set', 'Interlock not set')
        self._call_sdk_bool_ptr(self.sdk.SidekickSDK_isKeySwitchStatusSet,
                                'Keyswitch set', 'Keyswitch not set')

    def arm_laser(self):
        '''Arm laser for scan.

        Raises:
          HardwareException if laser is not armed before timeout.
        '''
        is_armed_ptr = pointer(c_bool(False))
        self.sdk.SidekickSDK_SetLaserArmDisarm(self.handle, True) #c_bool(True))
        self.sdk.SidekickSDK_ExecLaserArmDisarm(self.handle)
        self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
        self.sdk.SidekickSDK_isLaserArmed(self.handle, is_armed_ptr)
        old_t = time.time()
        while not is_armed_ptr.contents.value:
            time.sleep(1)
            self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
            self.sdk.SidekickSDK_isLaserArmed(self.handle, is_armed_ptr)
            curr_t = time.time()
            if curr_t - old_t > self.arm_laser_timeout:
                raise HardwareException('Unable to arm laser')
        print('Laser armed')

    def set_qcl_params(self):
        '''Set relevant parameters of the QCL.

        Raises:
          HardwareException if QCL params aren't set before timeout
        '''
        qcl_params = self._read_qcl_params()
        qcl_params['pulse_rate_hz_ptr'].contents = c_uint32(self.qcl_pulse_rate_hz)
        qcl_params['temp_c_ptr'].contents = c_float(self.qcl_temp_c)
        qcl_params['current_ma_ptr'].contents = c_uint16(self.qcl_current_ma)
        qcl_params['pulse_width_ns_ptr'].contents = c_uint32(self.qcl_width_ns)
        self._update_qcl_params(qcl_params)
        old_t = time.time()
        while (qcl_params['pulse_rate_hz_ptr'].contents.value != self.qcl_pulse_rate_hz or
               qcl_params['temp_c_ptr'].contents.value != self.qcl_temp_c or
               qcl_params['current_ma_ptr'].contents.value != self.qcl_current_ma or
               qcl_params['pulse_width_ns_ptr'].contents.value != self.qcl_width_ns):
            qcl_params = self._read_qcl_params()
            curr_t = time.time()
            if curr_t - old_t > self.qcl_set_params_timeout:
                HardwareException("Unable to set QCL params")
            time.sleep(1)
        print("QCL Parameters: {}".format(
            dict([(k, v.contents.value) for k, v in qcl_params.items()])))

    def cool_tecs(self):
        '''Wait for TECs to cool to correct temp.

        Raises:
          HardwareException if TECs unable to cool
        '''
        is_temp_set_ptr = pointer(c_bool(False))
        self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
        self.sdk.SidekickSDK_isTempStatusSet(self.handle, is_temp_set_ptr)
        old_t = time.time()
        while not is_temp_set_ptr.contents.value:
            time.sleep(1)
            self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
            self.sdk.SidekickSDK_isTempStatusSet(self.handle, is_temp_set_ptr)
            curr_t = time.time()
            if curr_t - old_t > self.cool_tecs_timeout:
                raise HardwareException('TECs unable to cool')
        time.sleep(self.cool_tecs_additional)
        print('TECs are at Temp')

    def turn_on_laser(self):
        '''Turn on QCL laser.

        Raises:
          HardwareException if laser does not turn on within a certain number of attempts
        '''
        status_word_ptr = pointer(c_uint32())
        error_word_ptr = pointer(c_uint16())
        warning_word_ptr = pointer(c_uint16())
        is_emitting_ptr = pointer(c_bool(False))
        turn_on = True
        attempts = 0
        trial_fail = False

        while not self.laser_on and attempts < self.laser_on_attempts:
            attempts += 1
            self.sdk.SidekickSDK_SetLaserOnOff(self.handle, 0, turn_on)
            self.sdk.SidekickSDK_ExecLaserOnOff(self.handle)
            self.sdk.SidekickSDK_ReadInfoStatusMask(self.handle)
            self.sdk.SidekickSDK_isLaserFiring(self.handle, is_emitting_ptr)
            print("Turn on attempts: {}".format(attempts))

            old_t = time.time()
            curr_t = 0
            while not is_emitting_ptr.contents.value:
                time.sleep(self.laser_on_wait)
                self.sdk.SidekickSDK_isLaserFiring(self.handle, is_emitting_ptr)
                curr_t = time.time()
                if curr_t - old_t > self.turn_on_laser_timeout:
                    trial_fail = True
                    break
            self.sdk.SidekickSDK_ReadStatusMask(
                self.handle, status_word_ptr, error_word_ptr, warning_word_ptr)
            print('Status Word is {}, Error Word is {}, Warning Word is {}'.format(
                status_word_ptr.contents.value, error_word_ptr.contents.value,
                warning_word_ptr.contents.value))

            if trial_fail:
                trial_fail = False
                continue

            self.laser_on = True

        if not is_emitting_ptr.contents.value:
            raise HardwareException('Laser failed to turn on')

        print('Laser is on.')

    def connect_to_lockin(self):
        '''Connect to lock-in amplifier.'''
        self.daq = self.zi_sdk.ziPython.ziDAQServer(self.lockin_ip, self.lockin_port)
        self.device = self.zi_sdk.utils.autoDetect(self.daq)
        #device_id = 'dev3097'
        #zi_device = self._get_lockin_ref(device_id)
        print('Connected to lock-In device {}'.format(self.device))

    def initialize_lockin(self):
        '''Initialize lock-in amplifier.'''
        print("Initializing lock-in amp")

        devtype = self.daq.getByte('/' + self.device + '/features/devtype')
        options = self.daq.getByte('/' + self.device + '/features/options')

        self.daq.setDouble('/' + self.device + '/demods/*/rate', 0.0)
        self.daq.setInt('/' + self.device + '/demods/*/trigger', 0)
        self.daq.setInt('/' + self.device + '/sigouts/*/enables/*', 0)

        if 'UHF' in devtype:
            self.daq.setInt('/' + self.device + '/demods/*/enable', 0)
            self.daq.setInt('/' + self.device + '/scopes/*/enable', 0)
        elif 'HF2' in devtype:
            self.daq.setInt('/' + self.device + '/scopes/*/trigchannel', -1)
        elif 'MF' in devtype:
            self.daq.setInt('/' + self.device + '/scopes/*/enable', 0)

        self.daq.setInt('/' + self.device + '/sigins/' + self.lockin_in_c + '/imp50', 0)
        self.daq.setInt('/' + self.device + '/sigins/' + self.lockin_in_c + '/ac', 1)
        self.daq.setInt('/' + self.device + '/sigins/' + self.lockin_in_c + '/diff', 0)
        self.daq.setInt('/' + self.device + '/sigins/' + self.lockin_in_c + '/float', 0)
        self.daq.setDouble('/' + self.device + '/sigins/' + self.lockin_in_c + '/range', 2.0)

        self.daq.setDouble('/' + self.device + '/demods/*/phaseshift', 0)
        self.daq.setInt('/' + self.device + '/demods/*/order', 4)
        self.daq.setDouble('/' + self.device + '/demods/' + self.lockin_demod_c + '/rate', self.demod_rate)
        self.daq.setInt('/' + self.device + '/demods/' + self.lockin_demod_c + '/harmonic', 1)
        if 'UHF' in devtype:
            self.daq.setInt('/' + self.device + '/demods/' + self.lockin_demod_c + '/enable', 1)
        if 'MF' in options:
            self.daq.setInt('/' + self.device + '/demods/*/oscselect', float(self.lockin_osc_c))
            self.daq.setInt('/' + self.device + '/demods/*/adcselect', float(self.lockin_in_c))
        self.daq.setDouble('/' + self.device + '/demods/*/timeconstant', self.lockin_time_constant)
        self.daq.setDouble('/' + self.device + '/oscs/' + self.lockin_osc_c + '/freq', self.lockin_osc_freq)

        self.daq.setInt('/' + self.device + '/extrefs/0/enable', 1)
        self.daq.setDouble('/' + self.device + '/triggers/in/0/level', 0.500)
        self.daq.setInt('/' + self.device + '/demods/0/adcselect', 1)  # trigger 1 rising edge for transfer
        self.daq.setInt('/' + self.device + '/demods/0/adcselect', 0)  # voltage signal in 1
        self.daq.setInt('/' + self.device + '/demods/1/adcselect', 2)  # ext ref = trigger 1
        self.daq.setInt('/' + self.device + '/demods/1/adcselect', 8)  # ext ref = aux in 1

        self.daq.unsubscribe('*')
        self.daq.sync()
        time.sleep(10 * self.lockin_time_constant)

    def turn_off_laser(self):
        '''Turn off and disconnect from laser.
        Raises:
           HardwareException if the laser fails to disarm or turn off
        '''
        turn_on = False
        arm = False
        self.sdk.SidekickSDK_SetLaserOnOff(self.handle, 0, turn_on)
        self.sdk.SidekickSDK_ExecLaserOnOff(self.handle)
        self.sdk.SidekickSDK_SetLaserArmDisarm(self.handle, arm)
        self.sdk.SidekickSDK_ExecLaserArmDisarm(self.handle)

        self.sdk.SidekickSDK_Disconnect(self.handle)
        print("Laser off")

    def _read_qcl_params(self):
        '''Read QCL parameters into dictionary.

        Returns:
          Dictionary of QCL parameter pointers
        '''
        params = {'qcl_slot_ptr': pointer(c_uint8()), 'pulse_rate_hz_ptr': pointer(c_uint32()),
                  'pulse_width_ns_ptr': pointer(c_uint32()), 'current_ma_ptr': pointer(c_uint16()),
                  'temp_c_ptr': pointer(c_float()), 'laser_mode_ptr': pointer(c_uint8()),
                  'pulse_mode_ptr': pointer(c_uint8()), 'vsrc_ptr': pointer(c_float())}
        self.sdk.SidekickSDK_ReadWriteLaserQclParams(self.handle, self.qcl_read_is_write, 0)
        self.sdk.SidekickSDK_GetLaserQclParams(
            self.handle, params['qcl_slot_ptr'], params['pulse_rate_hz_ptr'],
            params['pulse_width_ns_ptr'], params['current_ma_ptr'],
            params['temp_c_ptr'], params['laser_mode_ptr'],
            params['pulse_mode_ptr'], params['vsrc_ptr'])
        return params

    def _update_qcl_params(self, params):
        '''Update QCL parameters with values in argument.

        Arguments:
          Params: Dictionary of pointers to QCL parameter values.
        '''
        self.sdk.SidekickSDK_SetLaserQclParams(
            self.handle, params['qcl_slot_ptr'].contents, params['pulse_rate_hz_ptr'].contents,
            params['pulse_width_ns_ptr'].contents, params['current_ma_ptr'].contents,
            params['temp_c_ptr'].contents, params['laser_mode_ptr'].contents,
            params['pulse_mode_ptr'].contents, params['vsrc_ptr'].contents)
        self.sdk.SidekickSDK_ReadWriteLaserQclParams(self.handle, self.qcl_update_is_write, 0)

    def _collect_data(self, data_list, time_list):
        '''Collect data from detector via lock-in amp.

        Arguments:
          poll_length: length of poll in seconds

        Side Effects:
          Appends data collected (1D list), time axis (1D list),
          standard deviation (1D list) to arguments
        '''
        self.daq.sync()
        self.daq.subscribe('/' + self.device + '/demods/' + self.lockin_demod_c + '/sample')
        poll_data = self.daq.poll(self.lockin_poll_length, self.poll_timeout)

        if self.device in poll_data and 'demods' in poll_data[self.device]:
            if len(poll_data[self.device]['demods']) >= int(self.lockin_demod_c):
                if 'sample' in poll_data[self.device]['demods'][self.lockin_demod_c]:
                    sample = poll_data[self.device]['demods'][self.lockin_demod_c]['sample']
                    x = sample['x']
                    y = sample['y']
                    data = np.hypot(x, y)
                    clockbase = float(self.daq.getInt('/' + self.device + '/clockbase'))
                    time_axis = sample['timestamp'] / clockbase
                    if sample['time']['dataloss']:
                        print('warning: Sample loss detected.')
        else:
            data = []
            time_axis = []
        self.daq.unsubscribe('*')
        data_list.append(data)
        time_list.append(time_axis)

    def _call_sdk_bool(self, sdk_fn, success_msg="Success", error_msg="Failure", *args):
        '''Call SDK function with optional arguments and check return value.

        Arguments:
          sdk_fn: SDK function to call
          success_msg: string message to print if function returns success
          error_msg: string message to print if function fails
          *args: optional arguments to pass to SDK function.

        Raises:
          HardwareException if SDK function fails
        '''
        ret = sdk_fn() if not args else sdk_fn(*args)
        if ret == self.sidekick_sdk_ret_success:
            print(success_msg)
        else:
            raise HardwareException(error_msg)

    def _call_sdk_bool_ptr(self, sdk_fn, success_msg, error_msg):
        '''Call SDk function and check boolean status value set by reference.

        Arguments:
          sdk_fn: SDK function to call
          success_msg: string message to print if function returns success
          error_msg: string message to print if function fails

        Raises:
          HardwareException if SDK function fails
        '''
        ret_ptr = pointer(c_bool(False))
        sdk_fn(self.handle, ret_ptr)
        if ret_ptr.contents.value:
            print(success_msg)
        else:
            self.sdk.SidekickSDK_Disconnect(self.handle)
            raise HardwareException(error_msg)
